# -*- coding: utf-8 -*-
"""
diagnose_operator.py

Traces a specific employee number through the full cleaning pipeline
logic without writing anything to the database. Run this to see exactly
why an operator is or isn't appearing in cycle_operator_presence.

Usage:
    python diagnose_operator.py
"""

import sqlite3
import pandas as pd
import numpy as np
import datetime as dt
from bisect import bisect_left
from itertools import groupby

DB_PATH    = "C:/Users/Ryan.Larson/Documents/Rockwell Manufacturing Database/manufacturing.db"
MOLD       = "Orange"
EMP_NUMBER = 69       # the employee number to trace

# ---------------------------------------------------------------------------
# Helpers -- copied from clean_mold_data.py
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


def between(l1, low, high):
    return [i for i in l1 if i >= low and i < high]


def list_vals(df_col, idx_list):
    col_list = list(df_col)
    return [col_list[i] for i in idx_list]


def closest_before(input_idx, input_list):
    arr = np.asarray(input_list)
    prev = arr[arr <= input_idx]
    return int(prev.max()) if len(prev) > 0 else int(arr[0])


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
    before = input_list[pos - 1]
    after  = input_list[pos]
    if timestamps[pos] - input_timestamp < input_timestamp - timestamps[pos - 1]:
        return after
    return before


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


def collect_lead_ids(df, cycle_inds):
    lead_inds = [i for i in range(len(df)) if pd.notna(df["Lead"].iloc[i])]
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


def get_operator_presence(df, ind_sets, cycle_inds):
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
        close_finish  = cycle_finish - dt.timedelta(seconds=resin_dur_sec)
        layup_start   = layup_finish - dt.timedelta(seconds=layup_dur_sec)
        closest_layup_idx = int((np.abs(df["time"] - layup_start)).idxmin())
        ref_idx = closest_layup_idx
        closest_before_op = closest_layup_idx
        while ref_idx > -1:
            if not np.isnan(df["Lead"].iloc[ref_idx]):
                closest_before_op = ref_idx
                break
            ref_idx -= 1
        all_IDs = [[closest_before_op, df["Lead"].iloc[closest_before_op]]]
        for j in range(closest_layup_idx, cycle_ind + 1):
            if not np.isnan(df["Lead"].iloc[j]):
                all_IDs.append([j, df["Lead"].iloc[j]])
        all_IDs_changes_only = [all_IDs[0]]
        for j in range(1, len(all_IDs)):
            if all_IDs[j][1] != all_IDs[j - 1][1]:
                all_IDs_changes_only.append(all_IDs[j])
        cycle_presence = []
        if len(all_IDs_changes_only) == 1:
            cycle_presence.append({
                "employee_number": safe_int(all_IDs_changes_only[0][1]),
                "on_layup": True, "on_close": True, "on_resin": True,
            })
        else:
            for k, entry in enumerate(all_IDs_changes_only):
                op_clock_in  = df.loc[entry[0], "time"]
                op_clock_out = (
                    df.loc[all_IDs_changes_only[k + 1][0], "time"]
                    if k < len(all_IDs_changes_only) - 1
                    else cycle_finish
                )
                on_layup = op_clock_in < layup_finish
                on_close = op_clock_in < close_finish and op_clock_out > layup_finish
                on_resin = op_clock_in < cycle_finish and op_clock_out > close_finish
                cycle_presence.append({
                    "employee_number": safe_int(entry[1]),
                    "on_layup": on_layup, "on_close": on_close, "on_resin": on_resin,
                })
        results.append(cycle_presence)
    return results


# ---------------------------------------------------------------------------
# Main diagnostic
# ---------------------------------------------------------------------------

def diagnose():
    conn = sqlite3.connect(DB_PATH)

    # Check operator record
    op_row = pd.read_sql(
        "SELECT * FROM operators WHERE employee_number = ?",
        conn, params=(EMP_NUMBER,)
    )
    print(f"Operator record for employee {EMP_NUMBER}:")
    print(op_row.to_string() if not op_row.empty else "  NOT FOUND IN OPERATORS TABLE")
    print()

    # Load raw rows (same query as clean_mold_data.py)
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
          AND (
              layup_time IS NOT NULL OR close_time IS NOT NULL OR
              resin_time IS NOT NULL OR cycle_time IS NOT NULL OR
              lead IS NOT NULL OR assistant_1 IS NOT NULL OR
              assistant_2 IS NOT NULL OR assistant_3 IS NOT NULL
          )
        ORDER BY record_timestamp ASC
    """, conn, params=(MOLD,))
    conn.close()

    df["time"] = pd.to_datetime(df["time"])

    print(f"Rows loaded for {MOLD}: {len(df)}")
    target_rows = df[df["Lead"] == float(EMP_NUMBER)]
    print(f"Rows where Lead = {EMP_NUMBER}: {len(target_rows)}")
    if not target_rows.empty:
        print(target_rows[["raw_id", "time", "Lead"]].head(10).to_string())
    print()

    if df.empty:
        print("No data loaded -- check that processed_at has been reset.")
        return

    df = df.sort_values("time").reset_index(drop=True)

    ind_sets, cycle_inds = associate_cycle_stages(df)
    print(f"Cycles found: {len(cycle_inds)}")
    print()

    presence_by_cycle = get_operator_presence(df, ind_sets, cycle_inds)

    found_in_n_cycles = 0
    full_cycle_count  = 0
    partial_count     = 0
    not_present_count = 0

    for i, presence_list in enumerate(presence_by_cycle):
        cycle_ts = df["time"].iloc[cycle_inds[i]]

        # Merge entries for this employee
        layup = close = resin = False
        appeared = False
        for op in presence_list:
            if op["employee_number"] == EMP_NUMBER:
                appeared = True
                layup = layup or op["on_layup"]
                close = close or op["on_close"]
                resin = resin or op["on_resin"]

        if not appeared:
            not_present_count += 1
            continue

        found_in_n_cycles += 1
        on_full = layup and close and resin

        if on_full:
            full_cycle_count += 1
        else:
            partial_count += 1
            print(f"  Cycle {i} ({cycle_ts}): PARTIAL  "
                  f"layup={layup} close={close} resin={resin}")
            print(f"    Raw presence entries: {presence_list}")

    print(f"\nSummary for employee {EMP_NUMBER} on {MOLD}:")
    print(f"  Appeared in {found_in_n_cycles} of {len(cycle_inds)} cycles")
    print(f"  Full cycle (all 3 stages): {full_cycle_count}")
    print(f"  Partial (some stages):     {partial_count}")
    print(f"  Not present:               {not_present_count}")


if __name__ == "__main__":
    diagnose()