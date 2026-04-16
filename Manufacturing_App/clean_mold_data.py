"""
clean_mold_data.py

Reads unprocessed rows from raw_mold_data, runs the cycle alignment and
operator presence logic from your existing cycle_time_methods_v2.py, and
writes the results to the cycles and cycle_operator_presence tables.

Run this after sync_raw_data.py has populated raw_mold_data.
Safe to run repeatedly -- already-processed raw rows are skipped, and
duplicate cycles are ignored on insert.

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
from bisect import bisect_left
from itertools import groupby

# ---------------------------------------------------------------------------
# Safe type conversion
# ---------------------------------------------------------------------------

def safe_int(value, fallback=0):
    """
    Convert value to int safely. Returns fallback if value is NaN, None,
    or otherwise uncastable. Used wherever operator numbers or IDs might
    be NaN due to missing PLC data.
    """
    try:
        if value is None:
            return fallback
        if isinstance(value, float) and np.isnan(value):
            return fallback
        return int(value)
    except (ValueError, TypeError):
        return fallback


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DB_PATH = "C:/Users/Ryan.Larson/Documents/Rockwell Manufacturing Database/manufacturing.db"
# DB_PATH = "manufacturing.db"

# Saturation thresholds -- same values as your existing code
LAYUP_THRESHOLD = 275
CLOSE_THRESHOLD = 90
RESIN_THRESHOLD = 180

# ---------------------------------------------------------------------------
# Operator resolution
#
# Looks up the surrogate key (operators.id) for a given employee number
# and cycle date. Returns None if the number can't be resolved, which
# means the cycle will still be written to cycles but no presence row
# is created for that operator -- a signal to investigate later.
# ---------------------------------------------------------------------------

def resolve_operator_id(cursor, employee_number: int, cycle_date: str) -> int | None:
    """
    Given a raw employee number (e.g. 42) and the date of the cycle,
    return the operators.id surrogate key for whichever person held
    that number on that date. Returns None if not found.
    """
    if employee_number == 0 or employee_number == 1:
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
# Helper functions
# Preserved exactly from your cycle_time_methods_v2.py
# ---------------------------------------------------------------------------

def closest_by_timestamp(input_idx, input_list, df):
    input_timestamp = df["time"].iloc[input_idx]
    timestamps = list(df["time"].iloc[input_list])

    if input_timestamp in timestamps:
        return input_list[timestamps.index(input_timestamp)]

    pos = bisect_left(timestamps, input_timestamp)
    if pos == 0:
        return input_list[0]
    elif pos == len(input_list):
        return input_list[-1]
    else:
        before = input_list[pos - 1]
        after  = input_list[pos]
        if timestamps[pos] - input_timestamp < input_timestamp - timestamps[pos - 1]:
            return after
        else:
            return before


def closest_before(input_idx, input_list):
    arr = np.asarray(input_list)
    prev = arr[arr <= input_idx]
    return int(prev.max()) if len(prev) > 0 else int(arr[0])


# ---------------------------------------------------------------------------
# Stage index finder
# Preserved from associate_cycle_stages in cycle_time_methods_v2.py
# ---------------------------------------------------------------------------

def find_nonzero_notnull_inds(series):
    """Return deduplicated indices where series is not null and not zero."""
    inds = [i for i in range(len(series)) if pd.notna(series.iloc[i]) and series.iloc[i] != 0]
    return [i[0] for i in groupby(inds)]


def associate_cycle_stages(df):
    """
    Identical logic to associate_cycle_stages in cycle_time_methods_v2.py.
    Returns (ind_sets, layup_inds, close_inds, resin_inds, cycle_inds).
    Each ind_set is [layup_idx, close_idx, resin_idx, cycle_idx].
    """
    layup_inds = find_nonzero_notnull_inds(df["Layup Time"])
    close_inds = find_nonzero_notnull_inds(df["Close Time"])
    resin_inds = find_nonzero_notnull_inds(df["Resin Time"])
    cycle_inds = find_nonzero_notnull_inds(df["Cycle Time"])

    ind_sets       = []
    layup_filtered = []
    close_filtered = []
    resin_filtered = []

    for ind in cycle_inds:
        cl = closest_by_timestamp(ind, layup_inds, df)
        cc = closest_by_timestamp(ind, close_inds, df)
        cr = closest_by_timestamp(ind, resin_inds, df)
        layup_filtered.append(cl)
        close_filtered.append(cc)
        resin_filtered.append(cr)
        ind_sets.append([cl, cc, cr, ind])

    return ind_sets, layup_filtered, close_filtered, resin_filtered, cycle_inds


# ---------------------------------------------------------------------------
# Operator presence logic
#
# This is a faithful port of the two-step process in cycle_time_methods_v2.py:
#
# Step 1 -- collect_lead_ids():
#   Mirrors the leadIDs collection loop in load_operator_data. For each
#   cycle, finds which operator numbers were active in the window between
#   the previous cycle and this one, using between() and closest_before()
#   exactly as the original code does. Same-number re-logs from the PLC
#   are naturally deduplicated by np.unique at the end.
#
# Step 2 -- get_operator_presence():
#   Mirrors count_stages_for_operator. Takes the leadIDs from step 1 and
#   determines per-stage presence by reconstructing stage boundaries from
#   the timing values, then checking each operator's clock-in/clock-out
#   against those boundaries.
# ---------------------------------------------------------------------------

def between(l1, low, high):
    """Values from l1 that are >= low and < high. From cycle_time_methods_v2."""
    return [i for i in l1 if i >= low and i < high]


def list_vals(df_col, idx_list):
    """Elements of df_col at positions in idx_list. From cycle_time_methods_v2."""
    col_list = list(df_col)
    return [col_list[i] for i in idx_list]


def collect_lead_ids(df, cycle_inds):
    """
    Step 1: For each cycle, collect the list of unique lead operator numbers
    that were active during that cycle's window. Matches the leadIDs loop in
    load_operator_data exactly, including the closest_before lookback for
    operators who were already clocked in at the start of the window.

    Returns leadIDs: a list (one per cycle) of lists of employee numbers.
    Zero means no one was clocked in.
    """
    # Find all row indices where Lead has a non-null value
    lead_inds = [i for i in range(len(df))
                 if pd.notna(df["Lead"].iloc[i])]

    if not lead_inds:
        return [[0.0] for _ in cycle_inds]

    leadIDs = [[] for _ in cycle_inds]

    for i, cyc_ind in enumerate(cycle_inds):
        if i == 0:
            low  = 0
            high = cyc_ind
            lead_between = between(lead_inds, low, high)
            leadIDs[i].extend(list_vals(df["Lead"], lead_between))
        else:
            # Include the operator who was already clocked in before this
            # cycle started (closest Lead row at or before previous cycle)
            prev_cyc_ind = cycle_inds[i - 1]
            cb = closest_before(prev_cyc_ind, lead_inds)
            leadIDs[i].append(df["Lead"].iloc[cb])

            low  = prev_cyc_ind
            high = cyc_ind
            lead_between = between(lead_inds, low, high)
            leadIDs[i].extend(list_vals(df["Lead"], lead_between))

        # Deduplicate, preserving zero-only lists as-is
        IDs = list(np.unique(leadIDs[i]))
        if len(IDs) == 1 and IDs[0] == 0:
            pass
        else:
            IDs = [id_ for id_ in IDs if id_ != 0]
        if len(IDs) == 0:
            IDs = [0.0]
        leadIDs[i] = IDs

    return leadIDs


def get_operator_presence(df, ind_sets, cycle_inds):
    """
    Step 2: For each cycle, determine which operators were present for which
    stages. Matches count_stages_for_operator in cycle_time_methods_v2.py
    exactly, including the all_IDs_changes_only deduplication that strips
    PLC re-logs of the same number.

    Returns a list (one per cycle) of lists of dicts:
        [
          [  # cycle 0
            {"employee_number": 42,
             "on_layup": True, "on_close": True, "on_resin": True},
          ],
          ...
        ]
    """
    # Step 1: collect which operators were active per cycle
    leadIDs = collect_lead_ids(df, cycle_inds)

    results = []

    for i, ind_set in enumerate(ind_sets):
        layup_ind = ind_set[0]
        close_ind = ind_set[1]
        resin_ind = ind_set[2]
        cycle_ind = ind_set[3]

        cycle_finish  = df["time"].iloc[cycle_ind]
        layup_dur_sec = 60.0 * df["Layup Time"].iloc[layup_ind]
        close_dur_sec = 60.0 * df["Close Time"].iloc[close_ind]
        resin_dur_sec = 60.0 * df["Resin Time"].iloc[resin_ind]

        layup_finish = (cycle_finish
                        - dt.timedelta(seconds=resin_dur_sec)
                        - dt.timedelta(seconds=close_dur_sec))
        close_finish = cycle_finish - dt.timedelta(seconds=resin_dur_sec)
        layup_start  = layup_finish - dt.timedelta(seconds=layup_dur_sec)

        # Find the row closest to layup_start, then walk back to the nearest
        # non-null Lead value -- same logic as count_stages_for_operator
        closest_layup_idx = int((np.abs(df["time"] - layup_start)).idxmin())
        ref_idx = closest_layup_idx
        closest_before_op = closest_layup_idx
        while ref_idx > -1:
            if pd.notna(df["Lead"].iloc[ref_idx]):
                closest_before_op = ref_idx
                break
            ref_idx -= 1

        # Collect all [row_index, employee_number] pairs from layup_start
        # through the end of the cycle
        all_IDs = [[closest_before_op,
                    df["Lead"].iloc[closest_before_op]]]
        for j in range(closest_layup_idx, cycle_ind + 1):
            if pd.notna(df["Lead"].iloc[j]):
                all_IDs.append([j, df["Lead"].iloc[j]])

        # Strip consecutive duplicate IDs -- these are PLC re-logs of the
        # same number and don't represent a clock-in or clock-out event
        all_IDs_changes_only = [all_IDs[0]]
        for j in range(1, len(all_IDs)):
            if all_IDs[j][1] != all_IDs[j - 1][1]:
                all_IDs_changes_only.append(all_IDs[j])

        cycle_presence = []

        if len(all_IDs_changes_only) == 1:
            # One operator for the whole cycle
            cycle_presence.append({
                "employee_number": safe_int(all_IDs_changes_only[0][1]),
                "on_layup": True,
                "on_close": True,
                "on_resin": True,
            })
        else:
            for k, entry in enumerate(all_IDs_changes_only):
                op_clock_in  = df.loc[entry[0], "time"]
                op_clock_out = (
                    df.loc[all_IDs_changes_only[k + 1][0], "time"]
                    if k < len(all_IDs_changes_only) - 1
                    else df.loc[cycle_ind, "time"]
                )

                on_layup = op_clock_in < layup_finish
                on_close = (op_clock_in  < close_finish
                            and op_clock_out > layup_finish)
                on_resin = (op_clock_in  < cycle_finish
                            and op_clock_out > close_finish)

                cycle_presence.append({
                    "employee_number": safe_int(entry[1]),
                    "on_layup": on_layup,
                    "on_close": on_close,
                    "on_resin": on_resin,
                })

        results.append(cycle_presence)

    return results


# ---------------------------------------------------------------------------
# Raw data loader
# Reads from raw_mold_data instead of the API
# ---------------------------------------------------------------------------

def load_raw_from_db(conn, mold_name):
    """
    Load unprocessed raw rows for one mold, pre-filtered to only rows that
    are relevant to the cleaning pipeline.

    Because the database is populated from all_tags (every tag the PLC
    logs), most rows contain only bag counts, leak counts, or other data
    the cleaning pipeline doesn't use. Loading all rows would make the
    operator association logic work through a much noisier dataset for no
    benefit. The WHERE clause here replicates what using operator_tags
    would have achieved, but from the unified all_tags archive.

    Rows are included if any of the eight cleaning-relevant columns is
    non-null. All-null rows (e.g. pure bag count rows) are excluded
    entirely, making drop_all_nan_rows unnecessary.
    """
    df = pd.read_sql("""
        SELECT
            id               AS raw_id,
            record_timestamp AS time,
            layup_time       AS "Layup Time",
            close_time       AS "Close Time",
            resin_time       AS "Resin Time",
            cycle_time       AS "Cycle Time",
            lead             AS "Lead",
            assistant_1      AS "Assistant 1",
            assistant_2      AS "Assistant 2",
            assistant_3      AS "Assistant 3"
        FROM raw_mold_data
        WHERE mold_name = ?
          AND processed_at IS NULL
          AND (
              layup_time  IS NOT NULL OR
              close_time  IS NOT NULL OR
              resin_time  IS NOT NULL OR
              cycle_time  IS NOT NULL OR
              lead        IS NOT NULL OR
              assistant_1 IS NOT NULL OR
              assistant_2 IS NOT NULL OR
              assistant_3 IS NOT NULL
          )
        ORDER BY record_timestamp ASC
    """, conn, params=(mold_name,))

    if df.empty:
        return df

    df["time"] = pd.to_datetime(df["time"])
    return df


# ---------------------------------------------------------------------------
# First-Monday flag
# Preserved from load_operator_data
# ---------------------------------------------------------------------------

def compute_first_monday_flags(datetimes):
    weekdays = [d.weekday() for d in datetimes]
    flags = []
    for i, day in enumerate(weekdays):
        if i == 0 and day == 0:
            flags.append(1 if datetimes[i].time() < dt.time(8, 0, 0) else 0)
        elif day == 0 and weekdays[i - 1] != 0:
            flags.append(1)
        else:
            flags.append(0)
    return flags, weekdays


# ---------------------------------------------------------------------------
# Exclusion reason
# A cycle gets a reason string if it should be excluded from reports.
# NULL means it is includeable.
# ---------------------------------------------------------------------------

def get_exclusion_reason(is_first_monday, layup_sat, close_sat, resin_sat):
    reasons = []
    if is_first_monday:
        reasons.append("first_monday")
    if layup_sat:
        reasons.append("layup_saturated")
    if close_sat:
        reasons.append("close_saturated")
    if resin_sat:
        reasons.append("resin_saturated")
    return ", ".join(reasons) if reasons else None


# ---------------------------------------------------------------------------
# Database writers
# ---------------------------------------------------------------------------

def insert_cycle(cursor, mold_name, raw_id, cycle_timestamp, layup_time,
                 close_time, resin_time, cycle_time, weekday, is_first_monday,
                 layup_sat, close_sat, resin_sat, exclusion_reason):
    cursor.execute("""
        INSERT OR IGNORE INTO cycles (
            source_raw_id, mold_name, cycle_timestamp,
            layup_time, close_time, resin_time, cycle_time,
            weekday, is_first_monday,
            layup_saturated, close_saturated, resin_saturated,
            exclusion_reason
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (raw_id, mold_name, cycle_timestamp,
          layup_time, close_time, resin_time, cycle_time,
          weekday, int(is_first_monday),
          int(layup_sat), int(close_sat), int(resin_sat),
          exclusion_reason))
    return cursor.lastrowid


def insert_presence(cursor, cycle_id, operator_id, on_layup, on_close,
                    on_resin, on_full_cycle):
    cursor.execute("""
        INSERT INTO cycle_operator_presence (
            cycle_id, operator_id,
            on_layup, on_close, on_resin, on_full_cycle
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (cycle_id, operator_id,
          int(on_layup), int(on_close), int(on_resin), int(on_full_cycle)))


def mark_raw_processed(cursor, raw_ids):
    processed_at = dt.datetime.now(dt.timezone.utc).isoformat()
    cursor.executemany(
        "UPDATE raw_mold_data SET processed_at = ? WHERE id = ?",
        [(processed_at, rid) for rid in raw_ids]
    )


# ---------------------------------------------------------------------------
# Main processing function for one mold
# ---------------------------------------------------------------------------

def process_mold(mold_name, conn):
    cursor = conn.cursor()

    print(f"\n  [{mold_name}] Loading unprocessed rows from database...")

    # Collect ALL unprocessed row IDs before any filtering.
    # This includes bag count, leak count, and other rows that the
    # pre-filter in load_raw_from_db will exclude from the DataFrame.
    # mark_raw_processed uses this full list so those rows get stamped
    # and don't re-appear on every subsequent run.
    cursor.execute("""
        SELECT id FROM raw_mold_data
        WHERE mold_name = ? AND processed_at IS NULL
    """, (mold_name,))
    all_raw_ids = [row[0] for row in cursor.fetchall()]

    if not all_raw_ids:
        print(f"  [{mold_name}] No unprocessed rows -- skipping.")
        return 0, 0

    # Load only the cleaning-relevant rows (stage times + operator columns)
    df_raw = load_raw_from_db(conn, mold_name)
    print(f"  [{mold_name}] {len(all_raw_ids)} total unprocessed rows, "
          f"{len(df_raw)} relevant to cleaning pipeline.")

    if df_raw.empty:
        mark_raw_processed(cursor, all_raw_ids)
        conn.commit()
        print(f"  [{mold_name}] No cleaning-relevant rows -- marked as processed.")
        return 0, 0

    raw_ids = list(df_raw["raw_id"])
    print(f"  [{mold_name}] {len(raw_ids)} relevant rows to process.")

    df = df_raw.sort_values("time").reset_index(drop=True)
    date_min = df["time"].iloc[0].strftime("%Y-%m-%d")
    date_max = df["time"].iloc[-1].strftime("%Y-%m-%d")
    print(f"  [{mold_name}] Data spans {date_min} to {date_max}.")

    print(f"  [{mold_name}] Associating cycle stages...")
    try:
        ind_sets, layup_inds, close_inds, resin_inds, cycle_inds = associate_cycle_stages(df)
    except Exception as e:
        print(f"  [{mold_name}] Stage association failed -- {e}")
        return 0, 0

    if not cycle_inds:
        mark_raw_processed(cursor, all_raw_ids)
        conn.commit()
        print(f"  [{mold_name}] No complete cycles found -- marked as processed.")
        return 0, 0

    print(f"  [{mold_name}] Found {len(cycle_inds)} cycles. Computing flags and saturation...")

    layup_times = [df["Layup Time"].iloc[i] for i in layup_inds]
    close_times = [df["Close Time"].iloc[i] for i in close_inds]
    resin_times = [df["Resin Time"].iloc[i] for i in resin_inds]
    cycle_times = [df["Cycle Time"].iloc[i] for i in cycle_inds]
    datetimes   = [df["time"].iloc[i] for i in cycle_inds]
    raw_row_ids = [df["raw_id"].iloc[i] for i in cycle_inds]

    first_monday_flags, weekdays = compute_first_monday_flags(datetimes)

    layup_saturated = [t >= LAYUP_THRESHOLD for t in layup_times]
    close_saturated = [t >= CLOSE_THRESHOLD for t in close_times]
    resin_saturated = [t >= RESIN_THRESHOLD for t in resin_times]

    n_excluded = sum(
        1 for i in range(len(cycle_inds))
        if first_monday_flags[i] or layup_saturated[i]
        or close_saturated[i] or resin_saturated[i]
    )
    print(f"  [{mold_name}] {n_excluded} cycles flagged for exclusion "
          f"({len(cycle_inds) - n_excluded} reportable).")

    print(f"  [{mold_name}] Resolving operator presence for each cycle...")
    presence_by_cycle = get_operator_presence(df, ind_sets, cycle_inds)

    cycles_written   = 0
    cycles_skipped   = 0
    presence_written = 0
    unresolved_ops   = 0
    unresolved_set   = set()   # track unique unresolved numbers for summary

    # Progress reporting every 10%
    total    = len(cycle_inds)
    interval = max(1, total // 10)

    cycles_errored = 0

    for i in range(total):
        if i > 0 and i % interval == 0:
            pct = int(i / total * 100)
            print(f"  [{mold_name}] {pct}% -- {cycles_written} cycles written so far...")

        try:
            cycle_ts   = datetimes[i].isoformat()
            cycle_date = datetimes[i].date().isoformat()
            exclusion  = get_exclusion_reason(
                first_monday_flags[i],
                layup_saturated[i],
                close_saturated[i],
                resin_saturated[i]
            )

            cycle_db_id = insert_cycle(
                cursor,
                mold_name       = mold_name,
                raw_id          = safe_int(raw_row_ids[i]),
                cycle_timestamp = cycle_ts,
                layup_time      = layup_times[i],
                close_time      = close_times[i],
                resin_time      = resin_times[i],
                cycle_time      = cycle_times[i],
                weekday         = weekdays[i],
                is_first_monday = first_monday_flags[i],
                layup_sat       = layup_saturated[i],
                close_sat       = close_saturated[i],
                resin_sat       = resin_saturated[i],
                exclusion_reason= exclusion
            )

            if cursor.rowcount == 0:
                cycles_skipped += 1
                continue
            cycles_written += 1

            # Merge presence entries by operator before inserting.
            # The same operator can appear multiple times in presence_by_cycle[i]
            # if they clocked in and out during the cycle window. We take the
            # logical OR across all their entries so a single row per
            # (cycle_id, operator_id) pair is inserted with the union of
            # whichever stages they were present for.
            merged = {}
            
            # # FIXME
            # # TEMPORARY DIAGNOSTIC -- remove after debugging
            # if any(emp != 0 and emp != 1 for emp in merged.keys()):
            #     print(f"  [{mold_name}] Cycle {i} ({datetimes[i].date()}) "
            #           f"merged presence: {merged}")
            # # FIXME
            
            for op in presence_by_cycle[i]:
                emp_num = op["employee_number"]
                if emp_num in (0, 1):
                    continue
                if emp_num not in merged:
                    merged[emp_num] = {
                        "on_layup": False,
                        "on_close": False,
                        "on_resin": False,
                    }
                merged[emp_num]["on_layup"] = merged[emp_num]["on_layup"] or op["on_layup"]
                merged[emp_num]["on_close"] = merged[emp_num]["on_close"] or op["on_close"]
                merged[emp_num]["on_resin"] = merged[emp_num]["on_resin"] or op["on_resin"]

            for emp_num, stages in merged.items():
                operator_id = resolve_operator_id(cursor, emp_num, cycle_date)
                if operator_id is None:
                    unresolved_ops += 1
                    unresolved_set.add(emp_num)
                    continue

                on_full = stages["on_layup"] and stages["on_close"] and stages["on_resin"]
                insert_presence(
                    cursor,
                    cycle_id      = cycle_db_id,
                    operator_id   = operator_id,
                    on_layup      = stages["on_layup"],
                    on_close      = stages["on_close"],
                    on_resin      = stages["on_resin"],
                    on_full_cycle = on_full,
                )
                presence_written += 1

        except Exception as e:
            cycles_errored += 1
            # Print enough detail to identify the problem row
            print(f"  [{mold_name}] ERROR on cycle {i} "
                  f"(timestamp: {datetimes[i]}, "
                  f"raw_id: {raw_row_ids[i]}, "
                  f"cycle_time: {cycle_times[i]}, "
                  f"layup: {layup_times[i]}, "
                  f"close: {close_times[i]}, "
                  f"resin: {resin_times[i]}, "
                  f"presence: {presence_by_cycle[i]})")
            print(f"  [{mold_name}]   Error was: {type(e).__name__}: {e}")
            print(f"  [{mold_name}]   Skipping this cycle and continuing...")

    print(f"  [{mold_name}] Writing changes to database...")
    mark_raw_processed(cursor, all_raw_ids)
    conn.commit()

    print(f"  [{mold_name}] Done.")
    print(f"    Cycles written:   {cycles_written}")
    print(f"    Cycles skipped (already existed): {cycles_skipped}")
    print(f"    Cycles errored (skipped): {cycles_errored}")
    print(f"    Presence rows written: {presence_written}")
    if unresolved_ops > 0:
        print(f"    Unresolved operator lookups: {unresolved_ops} "
              f"(unique numbers: {sorted(unresolved_set)})")
        print(f"    Add these employee numbers to the operators table "
              f"and re-run to capture their presence data.")

    return cycles_written, presence_written


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

MOLDS = ["Brown", "Purple", "Red", "Pink", "Orange", "Green"]


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
            print(f"  [{mold_name}] ERROR -- {e}")
            errors.append((mold_name, str(e)))
            conn.rollback()

    conn.close()

    elapsed = dt.datetime.now() - start_time
    elapsed_str = str(elapsed).split(".")[0]   # trim microseconds

    print(f"\n{'='*50}")
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