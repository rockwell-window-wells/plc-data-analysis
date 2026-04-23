# -*- coding: utf-8 -*-
"""
derive_cycle_operator_presence.py

Populates cycle_operator_presence by aggregating cycle_stage_operators.

For each (cycle_id, operator_id) pair, reads the three stage rows and
sets on_layup, on_close, on_resin, and on_full_cycle based on the
present flag in cycle_stage_operators.

Run this after clean_mold_data.py. Safe to run repeatedly -- rows are
inserted with INSERT OR REPLACE, so existing entries are updated if the
underlying stage data has changed.

Usage:
    python derive_cycle_operator_presence.py

    # To re-derive only a specific mold:
    python derive_cycle_operator_presence.py --mold Brown

    # To re-derive only cycles with no presence rows yet:
    python derive_cycle_operator_presence.py --missing-only
"""

import sqlite3
import argparse
import datetime as dt
import os
import yaml

# DB_PATH = "C:/Users/Ryan.Larson/Documents/Rockwell Manufacturing Database/manufacturing.db"
CONFIG_FILE = 'config_vars.yaml'

with open(CONFIG_FILE, 'r') as file:
    config_data = yaml.safe_load(file)
    DB_PATH = config_data['db_path']


def derive_presence(db_path=DB_PATH, mold_name=None, missing_only=False):
    """
    Aggregate cycle_stage_operators into cycle_operator_presence.

    The aggregation query groups by (cycle_id, operator_id) and takes the
    MAX of present for each stage. MAX works here because present is 0 or 1,
    so MAX(present) = 1 if any row for that stage has present=1.

    on_full_cycle = 1 only when all three stages have present=1.
    """
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at {os.path.abspath(db_path)}")
        return

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    cursor = conn.cursor()

    start_time = dt.datetime.now()
    print(f"\n[{start_time.strftime('%Y-%m-%d %H:%M:%S')}] "
          f"Deriving cycle_operator_presence...")

    # Build the WHERE clause based on options
    where_clauses = []
    params = []

    if mold_name:
        where_clauses.append("c.mold_name = ?")
        params.append(mold_name)
        print(f"  Filtering to mold: {mold_name}")

    if missing_only:
        where_clauses.append("""
            NOT EXISTS (
                SELECT 1 FROM cycle_operator_presence p
                WHERE p.cycle_id    = cso.cycle_id
                  AND p.operator_id = cso.operator_id
            )
        """)
        print(f"  Processing only (cycle, operator) pairs with no existing presence row.")

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    # Count how many pairs need processing
    count_sql = f"""
        SELECT COUNT(DISTINCT cso.cycle_id || '-' || cso.operator_id)
        FROM cycle_stage_operators cso
        JOIN cycles c ON c.id = cso.cycle_id
        {where_sql}
    """
    cursor.execute(count_sql, params)
    total_pairs = cursor.fetchone()[0]
    print(f"  Found {total_pairs} (cycle, operator) pairs to process.")

    if total_pairs == 0:
        print("  Nothing to do.")
        conn.close()
        return

    # The aggregation. For each (cycle_id, operator_id):
    #   on_layup  = 1 if any stage='layup'  row has present=1
    #   on_close  = 1 if any stage='close'  row has present=1
    #   on_resin  = 1 if any stage='resin'  row has present=1
    #   on_full   = 1 only if all three are 1
    #
    # INSERT OR REPLACE handles both new rows and updates to existing ones.
    # The UNIQUE(cycle_id, operator_id) constraint on cycle_operator_presence
    # is what makes REPLACE update in-place rather than duplicate.
    derive_sql = f"""
        INSERT OR REPLACE INTO cycle_operator_presence
            (cycle_id, operator_id, on_layup, on_close, on_resin, on_full_cycle)
        SELECT
            cso.cycle_id,
            cso.operator_id,
            MAX(CASE WHEN cso.stage = 'layup' AND cso.present = 1 THEN 1 ELSE 0 END)
                AS on_layup,
            MAX(CASE WHEN cso.stage = 'close' AND cso.present = 1 THEN 1 ELSE 0 END)
                AS on_close,
            MAX(CASE WHEN cso.stage = 'resin' AND cso.present = 1 THEN 1 ELSE 0 END)
                AS on_resin,
            CASE
                WHEN MAX(CASE WHEN cso.stage = 'layup' AND cso.present = 1 THEN 1 ELSE 0 END) = 1
                 AND MAX(CASE WHEN cso.stage = 'close' AND cso.present = 1 THEN 1 ELSE 0 END) = 1
                 AND MAX(CASE WHEN cso.stage = 'resin' AND cso.present = 1 THEN 1 ELSE 0 END) = 1
                THEN 1
                ELSE 0
            END AS on_full_cycle
        FROM cycle_stage_operators cso
        JOIN cycles c ON c.id = cso.cycle_id
        {where_sql}
        GROUP BY cso.cycle_id, cso.operator_id
    """

    cursor.execute(derive_sql, params)
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()

    elapsed = str(dt.datetime.now() - start_time).split(".")[0]
    print(f"\nDone.")
    print(f"  Time elapsed:      {elapsed}")
    print(f"  Rows written:      {rows_affected}")
    print(f"\nVerify with:")
    print(f"  SELECT on_layup, on_close, on_resin, on_full_cycle,")
    print(f"         COUNT(*) AS n")
    print(f"  FROM cycle_operator_presence")
    print(f"  GROUP BY 1, 2, 3, 4;")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Derive cycle_operator_presence from cycle_stage_operators."
    )
    parser.add_argument(
        "--mold", default=None,
        help="Only process a specific mold (e.g. Brown). Default: all molds."
    )
    parser.add_argument(
        "--missing-only", action="store_true",
        help="Only process (cycle, operator) pairs with no existing presence row."
    )
    parser.add_argument(
        "--db", default=DB_PATH,
        help=f"Path to the database file (default: {DB_PATH})"
    )
    args = parser.parse_args()

    derive_presence(
        db_path      = args.db,
        mold_name    = args.mold,
        missing_only = args.missing_only,
    )