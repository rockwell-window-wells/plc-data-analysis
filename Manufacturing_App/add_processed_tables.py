"""
add_processed_tables.py

Adds the three processed-layer tables to an existing manufacturing.db
without touching any data already in the database.

Safe to run multiple times -- all statements use IF NOT EXISTS.

Usage:
    python add_processed_tables.py
"""

import sqlite3
import os

DB_PATH = "C:/Users/Ryan.Larson/Documents/Rockwell Manufacturing Database/manufacturing.db"
# DB_PATH = "manufacturing.db"


def add_processed_tables(db_path: str = DB_PATH):
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at {os.path.abspath(db_path)}")
        print("Check that DB_PATH points to your existing database file.")
        return

    print(f"Opening database at: {os.path.abspath(db_path)}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Confirm the raw tables are already there before proceeding
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing = {row[0] for row in cursor.fetchall()}
    print(f"  Existing tables: {', '.join(sorted(existing))}")

    if "raw_mold_data" not in existing:
        print("WARNING: raw_mold_data not found. Are you pointing at the right file?")

    # -------------------------------------------------------------------------
    # operators
    #
    # One row per person per employee number assignment. When a number is
    # reused, you insert a new row rather than updating the old one. The old
    # row gets its active_to date filled in; the new row has active_to = NULL.
    #
    # active_from and active_to are stored as TEXT in ISO format (YYYY-MM-DD).
    # SQLite has no native DATE type -- TEXT works fine and sorts correctly.
    #
    # To find the current holder of employee number 42:
    #   WHERE employee_number = 42 AND active_to IS NULL
    #
    # To find who held number 42 on a specific date:
    #   WHERE employee_number = 42
    #     AND active_from <= '2023-06-15'
    #     AND (active_to IS NULL OR active_to > '2023-06-15')
    # -------------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS operators (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_number INTEGER NOT NULL,
            name            TEXT,
            active_from     TEXT    NOT NULL,
            active_to       TEXT,
            shift           TEXT
        )
    """)
    print("  Created table: operators")

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_operators_number
        ON operators (employee_number)
    """)
    print("  Created index for operators")

    # -------------------------------------------------------------------------
    # cycles
    #
    # One row per completed, cleaned cycle. Timing data and quality flags only.
    # No operator columns -- those live in cycle_operator_presence.
    #
    # source_raw_id links back to the raw_mold_data row this cycle came from,
    # so you can always trace a cleaned result back to the original API data.
    #
    # exclusion_reason being NULL means the cycle is includeable in reports.
    # If it has a value (e.g. "first_monday", "saturated_layup"), the cycle
    # is kept in the database but filtered out at query time.
    # -------------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cycles (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            source_raw_id       INTEGER REFERENCES raw_mold_data(id),
            mold_name           TEXT    NOT NULL,
            cycle_timestamp     TEXT    NOT NULL,
            layup_time          REAL,
            close_time          REAL,
            resin_time          REAL,
            cycle_time          REAL,
            weekday             INTEGER,
            is_first_monday     INTEGER DEFAULT 0,
            layup_saturated     INTEGER DEFAULT 0,
            close_saturated     INTEGER DEFAULT 0,
            resin_saturated     INTEGER DEFAULT 0,
            exclusion_reason    TEXT    DEFAULT NULL
        )
    """)
    print("  Created table: cycles")

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_cycles_timestamp
        ON cycles (cycle_timestamp)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_cycles_mold
        ON cycles (mold_name, cycle_timestamp)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_cycles_exclusion
        ON cycles (exclusion_reason)
    """)
    print("  Created indexes for cycles")

    # -------------------------------------------------------------------------
    # cycle_operator_presence
    #
    # One row per operator per cycle. Records which stages each operator was
    # present for, based on the clock-in/clock-out logic from your existing
    # count_stages_for_operator function.
    #
    # operator_id is the surrogate key from the operators table -- NOT the
    # raw employee number. This is what makes historical queries correct even
    # when numbers get reused.
    #
    # on_full_cycle = 1 means the operator was present for all three stages.
    # This is the flag used for standard cycle time reports.
    # -------------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cycle_operator_presence (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            cycle_id        INTEGER NOT NULL REFERENCES cycles(id),
            operator_id     INTEGER NOT NULL REFERENCES operators(id),
            on_layup        INTEGER NOT NULL DEFAULT 0,
            on_close        INTEGER NOT NULL DEFAULT 0,
            on_resin        INTEGER NOT NULL DEFAULT 0,
            on_full_cycle   INTEGER NOT NULL DEFAULT 0
        )
    """)
    print("  Created table: cycle_operator_presence")

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_presence_cycle
        ON cycle_operator_presence (cycle_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_presence_operator
        ON cycle_operator_presence (operator_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_presence_full_cycle
        ON cycle_operator_presence (operator_id, on_full_cycle)
    """)
    print("  Created indexes for cycle_operator_presence")

    conn.commit()
    conn.close()

    print("\nDone. Open the database in DB Browser for SQLite to verify the new tables.")
    print("Your existing raw data is untouched.")


if __name__ == "__main__":
    add_processed_tables()
