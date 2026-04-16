"""
backfill_operator_presence.py

Fills in missing cycle_operator_presence rows for a specific operator
without reprocessing raw data or touching the cycles table.

Use this when you add a new operator to the operators table after the
cleaning pipeline has already run. Rather than resetting processed_at
and rerunning everything, this script:

  1. Finds all raw_mold_data rows where the given employee number appears
     in the Lead column and processed_at is already set (already cleaned).
  2. Looks up the corresponding cycle row via source_raw_id.
  3. Checks whether a presence row already exists for that cycle + operator.
  4. If not, re-runs the operator presence logic for that cycle and inserts
     the missing presence row.

Usage:
    python backfill_operator_presence.py --employee-number 42

    # Or to preview what would be inserted without writing anything:
    python backfill_operator_presence.py --employee-number 42 --dry-run
"""

import sqlite3
import pandas as pd
import numpy as np
import datetime as dt
import argparse
import os
from bisect import bisect_left
from itertools import groupby

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DB_PATH = "C:/Users/Ryan.Larson/Documents/Rockwell Manufacturing Database/manufacturing.db"

# Saturation thresholds -- must match clean_mold_data.py
LAYUP_THRESHOLD = 275
CLOSE_THRESHOLD = 90
RESIN_THRESHOLD = 180


# ---------------------------------------------------------------------------
# Copied helpers from clean_mold_data.py
# These must stay in sync with that file if you ever change the logic there.
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


def resolve_operator_id(cursor, employee_number: int, cycle_date: str):
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


def find_nonzero_notnull_inds(series):
    inds = [i for i in range(len(series))
            if pd.notna(series.iloc[i]) and series.iloc[i] != 0]
    return [i[0] for i in groupby(inds)]


def associate_cycle_stages(df):
    layup_inds = find_nonzero_notnull_inds(df["Layup Time"])
    close_inds = find_nonzero_notnull_inds(df["Close Time"])
    resin_inds = find_nonzero_notnull_inds(df["Resin Time"])
    cycle_inds = find_nonzero_notnull_inds(df["Cycle Time"])
    ind_sets = []
    for ind in cycle_inds:
        cl = closest_by_timestamp(ind, layup_inds, df)
        cc = closest_by_timestamp(ind, close_inds, df)
        cr = closest_by_timestamp(ind, resin_inds, df)
        ind_sets.append([cl, cc, cr, ind])
    return ind_sets, cycle_inds


def between(l1, low, high):
    return [i for i in l1 if i >= low and i < high]


def list_vals(df_col, idx_list):
    col_list = list(df_col)
    return [col_list[i] for i in idx_list]


def collect_lead_ids(df, cycle_inds):
    """Step 1: collect which operator numbers were active per cycle window."""
    lead_inds = [i for i in range(len(df))
                 if pd.notna(df["Lead"].iloc[i])]
    if not lead_inds:
        return [[0.0] for _ in cycle_inds]

    leadIDs = [[] for _ in cycle_inds]
    for i, cyc_ind in enumerate(cycle_inds):
        if i == 0:
            lead_between = between(lead_inds, 0, cyc_ind)
            leadIDs[i].extend(list_vals(df["Lead"], lead_between))
        else:
            prev_cyc_ind = cycle_inds[i - 1]
            cb = closest_before(prev_cyc_ind, lead_inds)
            leadIDs[i].append(df["Lead"].iloc[cb])
            lead_between = between(lead_inds, prev_cyc_ind, cyc_ind)
            leadIDs[i].extend(list_vals(df["Lead"], lead_between))

        IDs = list(np.unique(leadIDs[i]))
        if len(IDs) == 1 and IDs[0] == 0:
            pass
        else:
            IDs = [id_ for id_ in IDs if id_ != 0]
        if len(IDs) == 0:
            IDs = [0.0]
        leadIDs[i] = IDs

    return leadIDs


def get_operator_presence_for_cycle(df, ind_set, cycle_inds, cycle_position):
    """
    Step 2: determine per-stage presence for one specific cycle.
    cycle_position is the index of this cycle within cycle_inds,
    needed so collect_lead_ids can establish the correct window.
    """
    # Run collect_lead_ids for all cycles so window boundaries are correct,
    # then pick just the entry for our target cycle
    leadIDs = collect_lead_ids(df, cycle_inds)

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

    closest_layup_idx = int((np.abs(df["time"] - layup_start)).idxmin())
    ref_idx = closest_layup_idx
    closest_before_op = closest_layup_idx
    while ref_idx > -1:
        if pd.notna(df["Lead"].iloc[ref_idx]):
            closest_before_op = ref_idx
            break
        ref_idx -= 1

    all_IDs = [[closest_before_op, df["Lead"].iloc[closest_before_op]]]
    for j in range(closest_layup_idx, cycle_ind + 1):
        if pd.notna(df["Lead"].iloc[j]):
            all_IDs.append([j, df["Lead"].iloc[j]])

    # Strip PLC re-logs (consecutive identical IDs)
    all_IDs_changes_only = [all_IDs[0]]
    for j in range(1, len(all_IDs)):
        if all_IDs[j][1] != all_IDs[j - 1][1]:
            all_IDs_changes_only.append(all_IDs[j])

    cycle_presence = []
    if len(all_IDs_changes_only) == 1:
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

    return cycle_presence


# ---------------------------------------------------------------------------
# Backfill logic
# ---------------------------------------------------------------------------

def load_raw_window_for_cycle(conn, mold_name, cycle_timestamp, window_hours=12):
    """
    Load a window of raw rows around a given cycle timestamp. We need
    enough context rows before and after the cycle for the stage
    association and operator presence logic to work correctly.
    """
    ts = pd.Timestamp(cycle_timestamp)
    ts_start = (ts - dt.timedelta(hours=window_hours)).isoformat()
    ts_end   = (ts + dt.timedelta(hours=1)).isoformat()

    df = pd.read_sql("""
        SELECT
            id              AS raw_id,
            record_timestamp AS time,
            layup_time      AS "Layup Time",
            close_time      AS "Close Time",
            resin_time      AS "Resin Time",
            cycle_time      AS "Cycle Time",
            lead            AS "Lead",
            assistant_1     AS "Assistant 1",
            assistant_2     AS "Assistant 2",
            assistant_3     AS "Assistant 3"
        FROM raw_mold_data
        WHERE mold_name = ?
          AND record_timestamp >= ?
          AND record_timestamp <= ?
          AND (
              layup_time IS NOT NULL OR close_time IS NOT NULL OR
              resin_time IS NOT NULL OR cycle_time IS NOT NULL OR
              lead IS NOT NULL OR assistant_1 IS NOT NULL OR
              assistant_2 IS NOT NULL OR assistant_3 IS NOT NULL
          )
        ORDER BY record_timestamp ASC
    """, conn, params=(mold_name, ts_start, ts_end))

    df["time"] = pd.to_datetime(df["time"])
    return df


def find_ind_set_for_cycle(df, target_timestamp):
    """
    Given a DataFrame window and a target cycle timestamp, find the
    ind_set and its position within cycle_inds. Returns (ind_set,
    cycle_inds, position) or (None, None, None) if not found.
    """
    ind_sets, cycle_inds = associate_cycle_stages(df)

    target_ts = pd.Timestamp(target_timestamp)
    for i, cycle_idx in enumerate(cycle_inds):
        if df["time"].iloc[cycle_idx] == target_ts:
            return ind_sets[i], cycle_inds, i

    # Fallback: find the closest cycle within 60 seconds
    for i, cycle_idx in enumerate(cycle_inds):
        diff = abs((df["time"].iloc[cycle_idx] - target_ts).total_seconds())
        if diff <= 60:
            return ind_sets[i], cycle_inds, i

    return None, None, None


def presence_row_exists(cursor, cycle_id, operator_id):
    cursor.execute("""
        SELECT id FROM cycle_operator_presence
        WHERE cycle_id = ? AND operator_id = ?
    """, (cycle_id, operator_id))
    return cursor.fetchone() is not None


def backfill_operator(employee_number: int, db_path: str = DB_PATH,
                      dry_run: bool = False):
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at {os.path.abspath(db_path)}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Confirm operator exists in the operators table
    cursor.execute("""
        SELECT id, name, active_from, active_to
        FROM operators
        WHERE employee_number = ?
        ORDER BY active_from
    """, (employee_number,))
    op_rows = cursor.fetchall()

    if not op_rows:
        print(f"ERROR: Employee number {employee_number} not found in "
              f"operators table. Add them first, then re-run.")
        conn.close()
        return

    print(f"Found {len(op_rows)} operator record(s) for employee "
          f"number {employee_number}:")
    for row in op_rows:
        status = "active" if row[3] is None else f"left {row[3]}"
        print(f"  id={row[0]}  name={row[1]}  "
              f"from={row[2]}  ({status})")

    if dry_run:
        print("\n[DRY RUN] No changes will be written.\n")

    # Find all cycles where this employee number appears as Lead in the
    # raw data within a window around the cycle timestamp, but has no
    # presence row yet.
    #
    # We cannot simply check the single raw row that source_raw_id points
    # to, because source_raw_id points to the row where the Cycle Time
    # was logged -- the Lead ID for that cycle is typically on a different
    # nearby row. Instead, we look for any raw row where this employee
    # number appears as Lead within a 12-hour window before each cycle.
    print(f"\nSearching for cycles with employee {employee_number} "
          f"in raw data but missing presence rows...")

    candidates = pd.read_sql("""
        SELECT DISTINCT
            c.id            AS cycle_id,
            c.mold_name,
            c.cycle_timestamp,
            c.source_raw_id AS raw_id
        FROM cycles c
        WHERE EXISTS (
            SELECT 1 FROM raw_mold_data r
            WHERE r.mold_name = c.mold_name
              AND r.lead = ?
              AND r.record_timestamp <= c.cycle_timestamp
              AND r.record_timestamp >= datetime(c.cycle_timestamp, '-12 hours')
        )
        ORDER BY c.cycle_timestamp ASC
    """, conn, params=(float(employee_number),))

    if candidates.empty:
        print(f"No cycles found where employee {employee_number} "
              f"appears as Lead in the raw data.")
        conn.close()
        return

    print(f"Found {len(candidates)} candidate cycles across "
          f"{candidates['mold_name'].nunique()} mold(s).")

    inserted      = 0
    already_exist = 0
    errors        = 0

    for _, row in candidates.iterrows():
        cycle_id        = int(row["cycle_id"])
        mold_name       = row["mold_name"]
        cycle_timestamp = row["cycle_timestamp"]
        cycle_date      = cycle_timestamp[:10]

        try:
            # Resolve which operators.id this employee number maps to
            # on this specific cycle date (handles reuse correctly)
            operator_id = resolve_operator_id(
                cursor, employee_number, cycle_date
            )
            if operator_id is None:
                # No matching operator record covers this date
                print(f"  SKIP {cycle_timestamp} ({mold_name}): "
                      f"employee {employee_number} has no operators row "
                      f"covering this date.")
                errors += 1
                continue

            # Skip if presence row already exists
            if presence_row_exists(cursor, cycle_id, operator_id):
                already_exist += 1
                continue

            # Load a window of raw data around this cycle and re-run
            # the presence logic to get accurate stage flags
            df_window = load_raw_window_for_cycle(
                conn, mold_name, cycle_timestamp
            )
            ind_set, cycle_inds_window, cycle_pos = find_ind_set_for_cycle(
                df_window, cycle_timestamp
            )

            if ind_set is None:
                print(f"  SKIP {cycle_timestamp} ({mold_name}): "
                      f"could not locate cycle in raw window.")
                errors += 1
                continue

            presence_list = get_operator_presence_for_cycle(
                df_window, ind_set, cycle_inds_window, cycle_pos
            )

            # Find this employee's entry in the presence list
            op_entry = next(
                (p for p in presence_list
                 if p["employee_number"] == employee_number),
                None
            )

            if op_entry is None:
                # Operator didn't appear in the presence logic for this
                # cycle window -- the raw Lead value may be from a
                # different stage boundary. Skip silently.
                errors += 1
                continue

            on_full = (op_entry["on_layup"]
                       and op_entry["on_close"]
                       and op_entry["on_resin"])

            if dry_run:
                print(f"  WOULD INSERT: cycle {cycle_id} "
                      f"({cycle_timestamp}, {mold_name}) "
                      f"operator_id={operator_id} "
                      f"layup={op_entry['on_layup']} "
                      f"close={op_entry['on_close']} "
                      f"resin={op_entry['on_resin']} "
                      f"full={on_full}")
            else:
                cursor.execute("""
                    INSERT OR IGNORE INTO cycle_operator_presence (
                        cycle_id, operator_id,
                        on_layup, on_close, on_resin, on_full_cycle
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (cycle_id, operator_id,
                      int(op_entry["on_layup"]),
                      int(op_entry["on_close"]),
                      int(op_entry["on_resin"]),
                      int(on_full)))

            inserted += 1

        except Exception as e:
            print(f"  ERROR on cycle {cycle_id} "
                  f"({cycle_timestamp}, {mold_name}): "
                  f"{type(e).__name__}: {e}")
            errors += 1

    if not dry_run:
        conn.commit()

    conn.close()

    action = "Would insert" if dry_run else "Inserted"
    print(f"\nDone.")
    print(f"  {action}:       {inserted} presence rows")
    print(f"  Already existed: {already_exist} (skipped)")
    print(f"  Errors/skipped:  {errors}")


# ---------------------------------------------------------------------------
# Auto-detection: find operators that need backfilling
# ---------------------------------------------------------------------------

def find_operators_needing_backfill(conn):
    """
    Returns a list of employee_numbers that are in the operators table
    but have no rows at all in cycle_operator_presence.

    This works by joining operators to cycle_operator_presence and keeping
    only the operators where no match is found (LEFT JOIN ... WHERE NULL).
    Operators with at least one presence row anywhere are excluded, since
    they have been at least partially processed -- backfill_operator handles
    the already_exist check per-cycle for any remaining gaps.
    """
    df = pd.read_sql("""
        SELECT DISTINCT
            o.employee_number,
            o.name,
            o.active_from,
            o.active_to
        FROM operators o
        LEFT JOIN cycle_operator_presence p ON p.operator_id = o.id
        WHERE p.id IS NULL
        ORDER BY o.employee_number, o.active_from
    """, conn)
    return df


def run_backfill(db_path: str = DB_PATH, dry_run: bool = False):
    """
    Automatically find all operators in the operators table that have no
    presence rows, then run backfill_operator for each one.
    """
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at {os.path.abspath(db_path)}")
        return

    conn = sqlite3.connect(db_path)
    missing = find_operators_needing_backfill(conn)
    conn.close()

    if missing.empty:
        print("All operators in the operators table already have presence "
              "rows in cycle_operator_presence. Nothing to backfill.")
        return

    print(f"Found {len(missing)} operator record(s) with no presence rows:\n")
    for _, row in missing.iterrows():
        status = "active" if pd.isna(row["active_to"]) else f"left {row['active_to']}"
        print(f"  employee_number={int(row['employee_number'])}  "
              f"name={row['name']}  "
              f"from={row['active_from']}  ({status})")

    if dry_run:
        print("\n[DRY RUN] No changes will be written.")

    print()

    total_inserted = 0
    total_errors   = 0

    for _, row in missing.iterrows():
        emp_num = int(row["employee_number"])
        print(f"\n{'='*50}")
        print(f"Backfilling employee number {emp_num} ({row['name']})...")

        # backfill_operator opens and closes its own connection,
        # so we call it independently for each operator
        backfill_operator(
            employee_number = emp_num,
            db_path         = db_path,
            dry_run         = dry_run
        )

    print(f"\n{'='*50}")
    print("Backfill run complete.")
    if dry_run:
        print("[DRY RUN] No changes were written.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Backfill cycle_operator_presence rows for operators that are "
            "missing from that table. By default, automatically finds all "
            "operators in the operators table with no presence rows. "
            "Pass --employee-number to target a specific operator instead."
        )
    )
    parser.add_argument(
        "--employee-number", type=int, default=None,
        help="Optional: 3-digit employee number to backfill (e.g. 42). "
             "If omitted, all operators with no presence rows are processed."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview what would be inserted without writing anything."
    )
    parser.add_argument(
        "--db", default=DB_PATH,
        help=f"Path to the database file (default: {DB_PATH})"
    )
    args = parser.parse_args()

    if args.employee_number is not None:
        # Target a specific operator
        backfill_operator(
            employee_number = args.employee_number,
            db_path         = args.db,
            dry_run         = args.dry_run
        )
    else:
        # Auto-detect all operators needing backfill
        run_backfill(
            db_path  = args.db,
            dry_run  = args.dry_run
        )