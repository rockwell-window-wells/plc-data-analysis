"""
clean_mold_data.py

Reads unprocessed rows from raw_mold_data, identifies completed cycles,
back-calculates stage boundaries from timing values, resolves operator
presence by querying the full Lead history (not just the current unprocessed
batch), and writes results to the cycles and cycle_operator_presence tables.

Key design decisions
--------------------
- Stage boundaries are back-calculated from the cycle row's timing values,
  not inferred from row index proximity. This is reliable because cycle_time
  is calculated by the PLC only after all three stage times are logged, and
  is almost always equal to layup + close + resin.

- Operator lookup queries raw_mold_data directly by timestamp range so that
  hourly heartbeat rows from already-processed batches are still found.

- A cycle is flagged (excluded from reports) if any stage time is 0 or null
  (e.g. mold sat overnight and didn't log layup properly), or if it is the
  first cycle on a Monday before 08:00.

- Operator presence for a stage is credited if the operator's active window
  overlaps the stage window at all (op_clock_in < stage_finish AND
  op_clock_out > stage_start).

Run after sync_raw_data.py. Safe to run repeatedly.

Usage:
    python clean_mold_data.py

Dependencies:
    pip install pandas numpy
"""

import sqlite3
import pandas as pd
import numpy as np
import datetime as dt
import os
import yaml

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CONFIG_FILE = 'config_vars.yaml'

with open(CONFIG_FILE, 'r') as file:
    config_data = yaml.safe_load(file)
    DB_PATH = config_data['db_path']

# Saturation thresholds (minutes)
LAYUP_THRESHOLD = 275
CLOSE_THRESHOLD = 90
RESIN_THRESHOLD = 180

# How far before layup_start to look for the operator who was already
# clocked in (covers the case where the last heartbeat was up to 65
# minutes before the cycle started)
OPERATOR_LOOKBACK_MINUTES = 75

# How close to now a cycle must be to be considered in-flight
IN_FLIGHT_THRESHOLD_HOURS = 2

# Window in seconds before the cycle timestamp to look for bag data
BAG_LOOKUP_WINDOW_SECONDS = 10

MOLDS = ["Brown", "Purple", "Red", "Pink", "Orange", "Green"]


# ---------------------------------------------------------------------------
# Safe type conversion
# ---------------------------------------------------------------------------

def safe_int(value, fallback=0):
    try:
        if value is None:
            return fallback
        if isinstance(value, float) and np.isnan(value):
            return fallback
        return int(value)
    except (ValueError, TypeError):
        return fallback


def safe_float(value):
    try:
        if value is None:
            return None
        f = float(value)
        return None if np.isnan(f) else f
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Operator resolution
# ---------------------------------------------------------------------------

def resolve_operator_id(cursor, employee_number: int,
                        cycle_date: str) -> int | None:
    """
    Return operators.id for the given employee number on the given date.
    Returns None if not found or if number is 0 or 1 (no operator / unknown).
    """
    if employee_number in (0, 1):
        return None

    cursor.execute("""
        SELECT id FROM operators
        WHERE employee_number = ?
          AND active_from <= ?
          AND (active_to IS NULL OR active_to > ?)
    """, (int(employee_number), cycle_date, cycle_date))

    row = cursor.fetchone()
    return row[0] if row else None


# ---------------------------------------------------------------------------
# Stage boundary calculation
#
# The cycle row is the anchor. The PLC logs cycle_time only after all three
# stage times are already stored, so cycle_timestamp is effectively
# resin_finish. We back-calculate from there.
#
# Timeline:
#   layup_start --> layup_finish --> close_finish --> cycle_finish
#                  (= close_start)  (= resin_start)  (= resin_finish)
# ---------------------------------------------------------------------------

def calc_stage_boundaries(cycle_ts: dt.datetime,
                          layup_min, close_min, resin_min):
    """
    Given a cycle timestamp and stage durations in minutes, return
    (layup_start, layup_finish, close_finish, resin_finish) as datetimes.

    Any stage with a None or 0 duration returns None for its boundary,
    which the caller uses to flag the cycle as incomplete.
    """
    resin_finish = cycle_ts
    close_finish = (resin_finish - dt.timedelta(minutes=resin_min)
                    if resin_min else None)
    layup_finish = (close_finish - dt.timedelta(minutes=close_min)
                    if close_finish and close_min else None)
    layup_start  = (layup_finish - dt.timedelta(minutes=layup_min)
                    if layup_finish and layup_min else None)

    return layup_start, layup_finish, close_finish, resin_finish


# ---------------------------------------------------------------------------
# Lead row loader and interval builder
# ---------------------------------------------------------------------------

def load_lead_events(conn, mold_name: str,
                     window_start: dt.datetime,
                     window_end: dt.datetime) -> pd.DataFrame:
    """
    Return all rows with a non-null Lead value for this mold between
    window_start and window_end, ordered by timestamp.

    Includes already-processed rows intentionally so that hourly heartbeat
    rows from previous sync batches are not lost.
    """
    df = pd.read_sql("""
        SELECT record_timestamp AS time, lead AS lead_number
        FROM raw_mold_data
        WHERE mold_name         = ?
          AND lead              IS NOT NULL
          AND record_timestamp  >= ?
          AND record_timestamp  <= ?
        ORDER BY record_timestamp ASC
    """, conn, params=(
        mold_name,
        window_start.isoformat(),
        window_end.isoformat(),
    ))

    if df.empty:
        return df

    df["time"]        = pd.to_datetime(df["time"])
    df["lead_number"] = df["lead_number"].apply(safe_int)
    return df


def build_operator_intervals(lead_df: pd.DataFrame,
                             window_end: dt.datetime) -> list[dict]:
    """
    Convert a sequence of Lead rows into non-overlapping operator presence
    intervals:

        [{"employee_number": 254,
          "clock_in":  <datetime>,
          "clock_out": <datetime>}, ...]

    Rules:
    - Each Lead row marks a clock-in event for that number (or 0 = nobody).
    - The previous operator's clock_out equals the next operator's clock_in.
    - The last interval runs until window_end.
    - Consecutive duplicate numbers are collapsed (heartbeat re-logs).
    """
    if lead_df.empty:
        return []

    # Collapse consecutive duplicates (heartbeats)
    changes = []
    prev_num = None
    for _, row in lead_df.iterrows():
        num = row["lead_number"]
        if num != prev_num:
            changes.append({"employee_number": num, "time": row["time"]})
            prev_num = num

    intervals = []
    for k, change in enumerate(changes):
        clock_in  = change["time"]
        clock_out = (changes[k + 1]["time"]
                     if k < len(changes) - 1
                     else pd.Timestamp(window_end))
        intervals.append({
            "employee_number": change["employee_number"],
            "clock_in":        clock_in,
            "clock_out":       clock_out,
        })

    return intervals


def get_operator_presence_for_cycle(
        conn,
        mold_name:    str,
        cycle_ts:     dt.datetime,
        layup_start:  dt.datetime | None,
        layup_finish: dt.datetime | None,
        close_finish: dt.datetime | None,
        resin_finish: dt.datetime,
) -> list[dict]:
    """
    Return a list of operator presence dicts for one cycle:

        [{"employee_number": 254,
          "on_layup": True, "on_close": True, "on_resin": True}, ...]

    Only operators with employee_number > 1 are returned.
    An operator is credited for a stage if their active window overlaps
    the stage window at all.
    """
    search_start = (
        (layup_start - dt.timedelta(minutes=OPERATOR_LOOKBACK_MINUTES))
        if layup_start
        else (cycle_ts - dt.timedelta(minutes=OPERATOR_LOOKBACK_MINUTES))
    )

    lead_df   = load_lead_events(conn, mold_name, search_start, resin_finish)
    intervals = build_operator_intervals(lead_df, resin_finish)

    results = []
    for interval in intervals:
        emp = interval["employee_number"]
        if emp in (0, 1):
            continue

        ci = interval["clock_in"]
        co = interval["clock_out"]

        on_layup = (
            layup_start  is not None
            and layup_finish is not None
            and ci < layup_finish
            and co > layup_start
        )
        on_close = (
            layup_finish is not None
            and close_finish is not None
            and ci < close_finish
            and co > layup_finish
        )
        on_resin = (
            close_finish is not None
            and ci < resin_finish
            and co > close_finish
        )

        results.append({
            "employee_number": emp,
            "on_layup":        on_layup,
            "on_close":        on_close,
            "on_resin":        on_resin,
        })

    return results


# ---------------------------------------------------------------------------
# Exclusion flags
# ---------------------------------------------------------------------------

def get_exclusion_reason(is_first_monday: bool,
                         layup_missing: bool,
                         close_missing: bool,
                         resin_missing: bool,
                         layup_sat: bool,
                         close_sat: bool,
                         resin_sat: bool) -> str | None:
    reasons = []
    if is_first_monday:
        reasons.append("first_monday")
    if layup_missing:
        reasons.append("layup_missing")
    if close_missing:
        reasons.append("close_missing")
    if resin_missing:
        reasons.append("resin_missing")
    if layup_sat:
        reasons.append("layup_saturated")
    if close_sat:
        reasons.append("close_saturated")
    if resin_sat:
        reasons.append("resin_saturated")
    return ", ".join(reasons) if reasons else None


def is_first_monday_cycle(cycle_ts: dt.datetime,
                          prev_cycle_ts: dt.datetime | None) -> bool:
    """
    True if this is the first cycle of a new work week (Monday) —
    i.e. the previous cycle was not on a Monday, or this is the first
    cycle ever and it falls on a Monday before 08:00.
    """
    if cycle_ts.weekday() != 0:
        return False
    if prev_cycle_ts is None:
        return cycle_ts.time() < dt.time(8, 0, 0)
    return prev_cycle_ts.weekday() != 0


# ---------------------------------------------------------------------------
# Raw data loaders
# ---------------------------------------------------------------------------

def load_unprocessed_cycles(conn, mold_name: str) -> pd.DataFrame:
    """
    Load unprocessed rows that have a non-null, non-zero Cycle Time.
    These are the anchor rows — one per completed cycle.
    """
    df = pd.read_sql("""
        SELECT
            id               AS raw_id,
            record_timestamp AS time,
            cycle_time       AS "Cycle Time",
            layup_time       AS "Layup Time",
            close_time       AS "Close Time",
            resin_time       AS "Resin Time"
        FROM raw_mold_data
        WHERE mold_name    = ?
          AND processed_at IS NULL
          AND cycle_time   IS NOT NULL
          AND cycle_time   != 0
        ORDER BY record_timestamp ASC
    """, conn, params=(mold_name,))

    if df.empty:
        return df

    df["time"] = pd.to_datetime(df["time"])
    return df


def load_all_unprocessed_ids(conn, mold_name: str) -> list[int]:
    """Return all unprocessed raw_mold_data IDs for this mold."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM raw_mold_data
        WHERE mold_name = ? AND processed_at IS NULL
    """, (mold_name,))
    return [row[0] for row in cursor.fetchall()]


def lookup_stage_times(conn, mold_name: str,
                       cycle_ts: dt.datetime,
                       prev_cycle_ts: dt.datetime | None) -> tuple:
    """
    Look up stage times for a cycle when they are not present on the cycle
    row itself.

    Handles two historical schemas:
    - New schema (majority): all stage times logged within milliseconds of
      the cycle time row. A short window before cycle_ts suffices.
    - Old schema (early data): each stage time logged when that stage
      finished, so layup_time may arrive ~90 minutes before the cycle row.

    Strategy: for each missing stage, find the most recent non-null value
    in raw_mold_data between the previous cycle timestamp (exclusive) and
    the current cycle timestamp (inclusive). This is schema-agnostic --
    it works whether the value arrived 0.3 seconds or 80 minutes ago,
    as long as it belongs to this cycle and not the previous one.

    Returns (layup_min, close_min, resin_min) as floats or None.
    """
    # Lower bound: just after the previous cycle (or beginning of time)
    lower_bound = (
        (prev_cycle_ts + dt.timedelta(milliseconds=1)).isoformat()
        if prev_cycle_ts
        else "1970-01-01T00:00:00"
    )
    upper_bound = cycle_ts.isoformat()

    df = pd.read_sql("""
        SELECT layup_time AS layup,
               close_time AS close,
               resin_time AS resin,
               record_timestamp AS time
        FROM raw_mold_data
        WHERE mold_name        = ?
          AND record_timestamp >= ?
          AND record_timestamp <= ?
          AND (layup_time IS NOT NULL
               OR close_time IS NOT NULL
               OR resin_time IS NOT NULL)
        ORDER BY record_timestamp ASC
    """, conn, params=(mold_name, lower_bound, upper_bound))

    layup = close = resin = None
    for _, row in df.iterrows():
        # Take the last non-null value seen for each stage — in the old
        # schema the correct value is the most recent one before the cycle
        if row["layup"] is not None:
            v = safe_float(row["layup"])
            if v is not None:
                layup = v
        if row["close"] is not None:
            v = safe_float(row["close"])
            if v is not None:
                close = v
        if row["resin"] is not None:
            v = safe_float(row["resin"])
            if v is not None:
                resin = v

    return layup, close, resin


def lookup_bag_data(cursor, mold_name: str,
                    cycle_timestamp_str: str) -> tuple:
    window_start = (
        dt.datetime.fromisoformat(cycle_timestamp_str)
        - dt.timedelta(seconds=BAG_LOOKUP_WINDOW_SECONDS)
    ).isoformat()

    cursor.execute("""
        SELECT bag, bag_cycles, bag_days
        FROM raw_mold_data
        WHERE mold_name       = ?
          AND record_timestamp >= ?
          AND record_timestamp <= ?
          AND (bag IS NOT NULL
               OR bag_cycles IS NOT NULL
               OR bag_days   IS NOT NULL)
        ORDER BY record_timestamp DESC
        LIMIT 1
    """, (mold_name, window_start, cycle_timestamp_str))

    row = cursor.fetchone()
    if row:
        return (safe_int(row[0], None),
                safe_int(row[1], None),
                safe_int(row[2], None))
    return None, None, None


# ---------------------------------------------------------------------------
# Database writers
# ---------------------------------------------------------------------------

def insert_cycle(cursor, mold_name, raw_id, cycle_timestamp,
                 layup_time, close_time, resin_time, cycle_time,
                 weekday, is_first_monday,
                 layup_sat, close_sat, resin_sat,
                 exclusion_reason,
                 bag_number, bag_cycles_raw, bag_days_raw):
    cursor.execute("""
        INSERT OR IGNORE INTO cycles (
            source_raw_id, mold_name, cycle_timestamp,
            layup_time, close_time, resin_time, cycle_time,
            weekday, is_first_monday,
            layup_saturated, close_saturated, resin_saturated,
            exclusion_reason,
            bag_number, bag_cycles_raw, bag_days_raw
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (raw_id, mold_name, cycle_timestamp,
          layup_time, close_time, resin_time, cycle_time,
          weekday, int(is_first_monday),
          int(layup_sat), int(close_sat), int(resin_sat),
          exclusion_reason,
          bag_number, bag_cycles_raw, bag_days_raw))
    return cursor.lastrowid


def insert_presence(cursor, cycle_id, operator_id,
                    on_layup, on_close, on_resin, on_full_cycle):
    cursor.execute("""
        INSERT INTO cycle_operator_presence (
            cycle_id, operator_id,
            on_layup, on_close, on_resin, on_full_cycle
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (cycle_id, operator_id,
          int(on_layup), int(on_close), int(on_resin), int(on_full_cycle)))


def mark_raw_processed(cursor, raw_ids: list[int]):
    processed_at = dt.datetime.now(dt.timezone.utc).isoformat()
    cursor.executemany(
        "UPDATE raw_mold_data SET processed_at = ? WHERE id = ?",
        [(processed_at, rid) for rid in raw_ids],
    )


# ---------------------------------------------------------------------------
# Bag usage
# ---------------------------------------------------------------------------

def update_bag_usage(cursor, mold_name: str) -> int:
    cursor.execute("DELETE FROM bag_usage WHERE mold_name = ?", (mold_name,))
    cursor.execute("""
        SELECT bag_number, MIN(cycle_timestamp), MAX(cycle_timestamp),
               COUNT(*), MAX(bag_days_raw), MAX(bag_cycles_raw)
        FROM cycles
        WHERE mold_name = ? AND bag_number IS NOT NULL
        GROUP BY bag_number
        ORDER BY MIN(cycle_timestamp)
    """, (mold_name,))

    rows    = cursor.fetchall()
    written = 0
    for bag_num, first_ts, last_ts, n_cycles, max_days, max_cyc in rows:
        cursor.execute("""
            INSERT INTO bag_usage (
                mold_name, bag_number,
                first_cycle_timestamp, last_cycle_timestamp,
                cycle_count, max_bag_days, max_bag_cycles
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (mold_name, bag_num, first_ts, last_ts,
              n_cycles, max_days, max_cyc))
        written += 1

    return written


# ---------------------------------------------------------------------------
# Main processing function
# ---------------------------------------------------------------------------

def process_mold(mold_name: str, conn) -> tuple[int, int]:
    cursor = conn.cursor()

    all_raw_ids = load_all_unprocessed_ids(conn, mold_name)

    if not all_raw_ids:
        print(f"  [{mold_name}] No unprocessed rows -- skipping.")
        return 0, 0

    print(f"  [{mold_name}] {len(all_raw_ids)} total unprocessed rows.")

    cycle_df = load_unprocessed_cycles(conn, mold_name)

    if cycle_df.empty:
        print(f"  [{mold_name}] No complete cycles found -- marked as processed.")
        mark_raw_processed(cursor, all_raw_ids)
        conn.commit()
        return 0, 0

    print(f"  [{mold_name}] {len(cycle_df)} cycle rows to process.")

    # Hold back the most recent cycle if it may still be in progress
    now     = pd.Timestamp.now("UTC").tz_localize(None)
    last_ts = cycle_df["time"].iloc[-1]
    held_back = False

    if (now - last_ts) <= dt.timedelta(hours=IN_FLIGHT_THRESHOLD_HOURS):
        # Don't process the last cycle — leave its raw rows unprocessed
        held_back_raw_id = int(cycle_df["raw_id"].iloc[-1])
        cycle_df = cycle_df.iloc[:-1].copy()
        # Remove the held-back cycle row ID from the to-mark list
        all_raw_ids = [rid for rid in all_raw_ids
                       if rid != held_back_raw_id]
        held_back = True
        print(f"  [{mold_name}] Most recent cycle held back (in-flight).")

    if cycle_df.empty:
        print(f"  [{mold_name}] All cycles held back -- nothing to process.")
        return 0, 0

    cycles_written   = 0
    cycles_skipped   = 0
    cycles_errored   = 0
    presence_written = 0
    unresolved_set   = set()
    unresolved_count = 0

    prev_cycle_ts = None

    for _, row in cycle_df.iterrows():
        cycle_ts = None
        raw_id   = None
        try:
            cycle_ts   = row["time"].to_pydatetime()
            cycle_date = cycle_ts.date().isoformat()
            raw_id     = int(row["raw_id"])

            # ── Stage times ────────────────────────────────────────────────
            layup_min = safe_float(row["Layup Time"])
            close_min = safe_float(row["Close Time"])
            resin_min = safe_float(row["Resin Time"])

            # Fall back to nearby rows if not on the cycle row
            if any(v is None for v in (layup_min, close_min, resin_min)):
                lb, cb, rb = lookup_stage_times(
                    conn, mold_name, cycle_ts, prev_cycle_ts
                )
                if layup_min is None:
                    layup_min = lb
                if close_min is None:
                    close_min = cb
                if resin_min is None:
                    resin_min = rb

            # Treat 0 the same as missing
            layup_missing = layup_min is None or layup_min == 0
            close_missing = close_min is None or close_min == 0
            resin_missing = resin_min is None or resin_min == 0

            # ── Stage boundaries ──────────────────────────────────────────
            layup_start, layup_finish, close_finish, resin_finish = (
                calc_stage_boundaries(
                    cycle_ts,
                    layup_min if not layup_missing else None,
                    close_min if not close_missing else None,
                    resin_min if not resin_missing else None,
                )
            )

            # ── Exclusion flags ────────────────────────────────────────────
            first_monday = is_first_monday_cycle(cycle_ts, prev_cycle_ts)
            layup_sat    = not layup_missing and layup_min >= LAYUP_THRESHOLD
            close_sat    = not close_missing and close_min >= CLOSE_THRESHOLD
            resin_sat    = not resin_missing and resin_min >= RESIN_THRESHOLD

            exclusion = get_exclusion_reason(
                first_monday,
                layup_missing, close_missing, resin_missing,
                layup_sat, close_sat, resin_sat,
            )

            # ── Bag data ───────────────────────────────────────────────────
            bag_num, bag_cyc, bag_days = lookup_bag_data(
                cursor, mold_name, cycle_ts.isoformat()
            )

            # ── Write cycle ────────────────────────────────────────────────
            cycle_db_id = insert_cycle(
                cursor,
                mold_name        = mold_name,
                raw_id           = raw_id,
                cycle_timestamp  = cycle_ts.isoformat(),
                layup_time       = layup_min,
                close_time       = close_min,
                resin_time       = resin_min,
                cycle_time       = safe_float(row["Cycle Time"]),
                weekday          = cycle_ts.weekday(),
                is_first_monday  = first_monday,
                layup_sat        = layup_sat,
                close_sat        = close_sat,
                resin_sat        = resin_sat,
                exclusion_reason = exclusion,
                bag_number       = bag_num,
                bag_cycles_raw   = bag_cyc,
                bag_days_raw     = bag_days,
            )

            if cursor.rowcount == 0:
                cycles_skipped += 1
                prev_cycle_ts = cycle_ts
                continue

            cycles_written += 1
            prev_cycle_ts  = cycle_ts

            # ── Operator presence ──────────────────────────────────────────
            presence_list = get_operator_presence_for_cycle(
                conn, mold_name, cycle_ts,
                layup_start, layup_finish, close_finish, resin_finish,
            )

            # Merge entries for the same employee number (operator may have
            # clocked out and back in during the cycle, producing two intervals
            # with the same number). Take logical OR across all their entries.
            merged = {}
            for op in presence_list:
                emp = op["employee_number"]
                if emp not in merged:
                    merged[emp] = {
                        "on_layup": False,
                        "on_close": False,
                        "on_resin": False,
                    }
                merged[emp]["on_layup"] = merged[emp]["on_layup"] or op["on_layup"]
                merged[emp]["on_close"] = merged[emp]["on_close"] or op["on_close"]
                merged[emp]["on_resin"] = merged[emp]["on_resin"] or op["on_resin"]

            for emp_num, stages in merged.items():
                op_id = resolve_operator_id(cursor, emp_num, cycle_date)
                if op_id is None:
                    unresolved_count += 1
                    unresolved_set.add(emp_num)
                    continue

                on_full = (stages["on_layup"]
                           and stages["on_close"]
                           and stages["on_resin"])
                insert_presence(
                    cursor,
                    cycle_id      = cycle_db_id,
                    operator_id   = op_id,
                    on_layup      = stages["on_layup"],
                    on_close      = stages["on_close"],
                    on_resin      = stages["on_resin"],
                    on_full_cycle = on_full,
                )
                presence_written += 1

        except Exception as e:
            cycles_errored += 1
            print(f"  [{mold_name}] ERROR on cycle "
                  f"(ts={cycle_ts}, raw_id={raw_id}): "
                  f"{type(e).__name__}: {e}")

    # ── Bag usage ──────────────────────────────────────────────────────────
    print(f"  [{mold_name}] Updating bag usage periods...")
    bag_periods = update_bag_usage(cursor, mold_name)

    # ── Mark processed ─────────────────────────────────────────────────────
    print(f"  [{mold_name}] Writing changes to database...")
    mark_raw_processed(cursor, all_raw_ids)
    conn.commit()

    print(f"  [{mold_name}] Done.")
    print(f"    Cycles written:                   {cycles_written}")
    print(f"    Cycles skipped (already existed): {cycles_skipped}")
    print(f"    Cycles errored (skipped):         {cycles_errored}")
    print(f"    Presence rows written:            {presence_written}")
    print(f"    Bag usage periods:                {bag_periods}")
    if unresolved_count > 0:
        print(f"    Unresolved operator lookups: {unresolved_count} "
              f"(unique numbers: {sorted(unresolved_set)})")
        print(f"    Add these to the operators table and re-run to "
              f"capture their presence data.")

    return cycles_written, presence_written


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_cleaning(db_path=DB_PATH):
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at {os.path.abspath(db_path)}")
        return

    start_time = dt.datetime.now()
    print(f"\n[{start_time.strftime('%Y-%m-%d %H:%M:%S')}] "
          f"Starting cleaning pipeline for {len(MOLDS)} molds...")

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")

    total_cycles   = 0
    total_presence = 0
    errors         = []

    for n, mold_name in enumerate(MOLDS, 1):
        print(f"\n--- Mold {n}/{len(MOLDS)}: {mold_name} ---")
        try:
            c, p = process_mold(mold_name, conn)
            total_cycles   += c
            total_presence += p
        except Exception as e:
            print(f"  [{mold_name}] FATAL ERROR -- {e}")
            errors.append((mold_name, str(e)))
            conn.rollback()

    conn.close()

    elapsed     = dt.datetime.now() - start_time
    elapsed_str = str(elapsed).split(".")[0]

    print(f"\n{'=' * 50}")
    print(f"Cleaning pipeline complete.")
    print(f"  Time elapsed:        {elapsed_str}")
    print(f"  Total cycles:        {total_cycles}")
    print(f"  Total presence rows: {total_presence}")
    if errors:
        print(f"  Molds with errors:   {[m for m, _ in errors]}")
        for mold, err in errors:
            print(f"    {mold}: {err}")
    else:
        print(f"  All molds completed without errors.")


if __name__ == "__main__":
    run_cleaning()
