"""
create_database.py

Creates the full manufacturing database from scratch.

Run this ONCE on a fresh database file. All tables are created with
IF NOT EXISTS so it is safe to re-run -- existing data is never touched.

Table creation order (foreign key dependency):
    raw_mold_data
    raw_resin_data
    raw_temperature_data
    sync_log
    operators
    cycles                  (references raw_mold_data)
    cycle_stage_operators   (references cycles, operators)
    cycle_operator_presence (references cycles, operators)

Usage:
    python create_database.py

After running, open the .db file in DB Browser for SQLite to inspect.
Download free at: https://sqlitebrowser.org/
"""

import sqlite3
import os
import yaml

# DB_PATH = "C:/Users/Ryan.Larson/Documents/Rockwell Manufacturing Database/manufacturing.db"

CONFIG_FILE = 'config_vars.yaml'

with open(CONFIG_FILE, 'r') as file:
    config_data = yaml.safe_load(file)
    DB_PATH = config_data['db_path']

def create_database(db_path: str = DB_PATH):
    print(f"Creating database at: {os.path.abspath(db_path)}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # WAL mode: allows the Dash app to read while sync is writing,
    # without them blocking each other.
    cursor.execute("PRAGMA journal_mode=WAL")

    # =========================================================================
    # RAW LAYER
    # =========================================================================

    # -------------------------------------------------------------------------
    # raw_mold_data
    #
    # One table for all 6 molds. mold_name identifies which mold a row is from.
    #
    # record_timestamp stores millisecond precision, e.g.:
    #   "2026-04-15T07:31:34.865"
    #
    # This is critical. The PLC fires multiple tag updates within milliseconds
    # of each other -- a typical cycle fires layup time, close time, resin
    # time, cycle time, bag count, and other tags all within ~50ms. Truncating
    # to seconds would cause the UNIQUE constraint to silently drop all but
    # one event per second, losing nearly all cycle data.
    #
    # ISO format strings with milliseconds sort correctly as plain text in
    # SQLite, so ORDER BY record_timestamp ASC works without any casting.
    #
    # raw_response is intentionally omitted. Storing the full API response
    # text in every row caused two problems:
    #   1. Database size grew to many gigabytes quickly.
    #   2. The blob corrupted nearby column values when rows were read back.
    # If you need to re-fetch raw data, re-run sync_raw_data.py -- the API
    # keeps 3 years of history.
    #
    # processed_at is NULL until clean_mold_data.py consumes this row.
    # -------------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_mold_data (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            mold_name           TEXT    NOT NULL,
            fetched_at          TEXT    NOT NULL,
            record_timestamp    TEXT    NOT NULL,

            -- Stage timing (minutes, matches the 0.0166667 factor in api_config_vars)
            layup_time          REAL,
            close_time          REAL,
            resin_time          REAL,
            cycle_time          REAL,
            leak_time           REAL,

            -- Count columns
            leak_count          REAL,
            parts_count         REAL,
            weekly_count        REAL,
            monthly_count       REAL,
            trash_count         REAL,

            -- Operator ID columns (raw numeric IDs from PLC)
            lead                REAL,
            assistant_1         REAL,
            assistant_2         REAL,
            assistant_3         REAL,

            -- Bag tracking columns
            bag                 REAL,
            bag_days            REAL,
            bag_cycles          REAL,

            -- NULL until clean_mold_data.py processes this row
            processed_at        TEXT    DEFAULT NULL,

            UNIQUE(mold_name, record_timestamp)
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_raw_mold_timestamp
        ON raw_mold_data (mold_name, record_timestamp)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_raw_mold_processed
        ON raw_mold_data (processed_at)
    """)
    print("  Created table: raw_mold_data")

    # -------------------------------------------------------------------------
    # raw_resin_data
    #
    # Two resin dispensing stations, identified by station_number (1 or 2).
    # Columns are placeholders -- adjust once you set up that data retrieval.
    # -------------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_resin_data (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            station_number      INTEGER NOT NULL,
            fetched_at          TEXT    NOT NULL,
            record_timestamp    TEXT    NOT NULL,

            amount_kg           REAL,

            processed_at        TEXT    DEFAULT NULL,

            UNIQUE(station_number, record_timestamp)
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_raw_resin_timestamp
        ON raw_resin_data (station_number, record_timestamp)
    """)
    print("  Created table: raw_resin_data")

    # -------------------------------------------------------------------------
    # raw_temperature_data
    #
    # Stubbed out. source_tag identifies the sensor or channel.
    # Add columns once you know what the StrideLinx temperature page returns.
    # -------------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_temperature_data (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            source_tag          TEXT    NOT NULL,
            fetched_at          TEXT    NOT NULL,
            record_timestamp    TEXT    NOT NULL,

            temperature_value   REAL,

            processed_at        TEXT    DEFAULT NULL,

            UNIQUE(source_tag, record_timestamp)
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_raw_temp_timestamp
        ON raw_temperature_data (source_tag, record_timestamp)
    """)
    print("  Created table: raw_temperature_data")

    # -------------------------------------------------------------------------
    # sync_log
    #
    # One row per sync run. Useful for diagnosing data gaps when the scheduled
    # job fails silently.
    # -------------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sync_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at      TEXT    NOT NULL,
            finished_at     TEXT,
            source          TEXT    NOT NULL,
            rows_inserted   INTEGER DEFAULT 0,
            rows_skipped    INTEGER DEFAULT 0,
            status          TEXT    DEFAULT 'running',
            error_message   TEXT
        )
    """)
    print("  Created table: sync_log")

    # =========================================================================
    # REFERENCE LAYER
    # =========================================================================

    # -------------------------------------------------------------------------
    # operators
    #
    # One row per person per employee number assignment.
    #
    # When a number is reused (someone leaves and a new hire gets the same
    # number), insert a new row rather than updating the old one. Set
    # active_to on the former employee's row, leave it NULL for the current
    # holder.
    #
    # When an operator changes shifts, same pattern: close out the old row
    # with active_to, insert a new row with the new shift and active_from.
    #
    # To find who held number 42 on a specific date:
    #   WHERE employee_number = 42
    #     AND active_from <= '2024-06-15'
    #     AND (active_to IS NULL OR active_to > '2024-06-15')
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
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_operators_number
        ON operators (employee_number)
    """)
    print("  Created table: operators")

    # =========================================================================
    # PROCESSED LAYER
    # =========================================================================

    # -------------------------------------------------------------------------
    # cycles
    #
    # One row per completed, cleaned cycle. Populated by clean_mold_data.py.
    #
    # source_raw_id links back to the raw_mold_data row where the cycle time
    # was logged, so any cycle can be traced back to the original PLC data.
    #
    # exclusion_reason NULL means the cycle is includeable in reports.
    # A non-null value (e.g. "first_monday", "layup_saturated") means the
    # cycle is kept in the database but filtered out at query time. This
    # preserves the data while making filtering explicit and auditable.
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
            exclusion_reason    TEXT    DEFAULT NULL,

            -- Bag tracking columns.
            -- bag_number is the PLC bag identifier (1-99, resets every ~2-3 years).
            -- bag_cycles_raw and bag_days_raw are the unvalidated counter values
            -- as logged by the PLC at cycle time. Use bag_usage for validated
            -- lifetime counts that are correct across resets and repairs.
            bag_number          INTEGER,
            bag_cycles_raw      INTEGER,
            bag_days_raw        INTEGER
        )
    """)
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
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_cycles_bag
        ON cycles (bag_number, cycle_timestamp)
    """)
    print("  Created table: cycles")

    # -------------------------------------------------------------------------
    # bag_usage
    #
    # Tracks validated lifetime usage per bag, across all molds and across
    # counter resets caused by repairs.
    #
    # A bag goes through up to 4 production periods (put into service, repaired
    # up to 3 times, then disposed of). Each time it returns from repair the
    # PLC counter may reset to 0 or an unreliable value. This table accumulates
    # the true lifetime cycle count by detecting those resets and carrying
    # forward the prior total as cumulative_offset.
    #
    # Lifetime cycles for any cycle row =
    #   cumulative_offset + (cycles.bag_cycles_raw - raw_start_value)
    #
    # bag_number rolls over from 99 back to 1 every ~2-3 years. A gap of more
    # than BAG_ROLLOVER_MONTHS (12) between periods with the same bag_number
    # is treated as a different physical bag -- a new generation begins.
    #
    # period_end is NULL while the bag is actively in service on this mold.
    # It is set when a new period begins (i.e. the bag moves to a different
    # mold or a reset is detected) or when the bag is taken out of service.
    # -------------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bag_usage (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            bag_number              INTEGER NOT NULL,
            mold_name               TEXT    NOT NULL,
            period_start            TEXT    NOT NULL,
            period_end              TEXT,
            cumulative_offset       INTEGER NOT NULL DEFAULT 0,
            raw_start_value         INTEGER NOT NULL DEFAULT 0,
            is_reset                INTEGER NOT NULL DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_bag_usage_bag
        ON bag_usage (bag_number, period_start)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_bag_usage_mold
        ON bag_usage (mold_name, bag_number)
    """)
    print("  Created table: bag_usage")

    # -------------------------------------------------------------------------
    # cycle_stage_operators
    #
    # The ground-truth operator presence table. One row per operator per
    # stage per cycle. Populated by clean_mold_data.py.
    #
    # This is a direct port of what count_stages_for_operator computes in
    # cycle_time_methods_v2.py, stored permanently instead of discarded.
    #
    # stage:       'layup', 'close', or 'resin'
    # stage_start: reconstructed stage boundary start (ISO datetime string)
    # stage_end:   reconstructed stage boundary end (ISO datetime string)
    # clock_in:    timestamp the operator's number first appeared in this window
    # clock_out:   timestamp of the next clock event, or cycle_finish for last
    # present:     1 if [clock_in, clock_out] overlaps [stage_start, stage_end]
    #
    # Storing stage_start/stage_end and clock_in/clock_out makes every
    # presence determination auditable -- you can verify the algorithm's
    # reasoning for any individual cycle directly in the database.
    # -------------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cycle_stage_operators (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            cycle_id        INTEGER NOT NULL REFERENCES cycles(id),
            operator_id     INTEGER NOT NULL REFERENCES operators(id),
            stage           TEXT    NOT NULL CHECK(stage IN ('layup','close','resin')),
            stage_start     TEXT    NOT NULL,
            stage_end       TEXT    NOT NULL,
            clock_in        TEXT    NOT NULL,
            clock_out       TEXT    NOT NULL,
            present         INTEGER NOT NULL DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_stage_ops_cycle
        ON cycle_stage_operators (cycle_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_stage_ops_operator
        ON cycle_stage_operators (operator_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_stage_ops_cycle_operator
        ON cycle_stage_operators (cycle_id, operator_id)
    """)
    print("  Created table: cycle_stage_operators")

    # -------------------------------------------------------------------------
    # cycle_operator_presence
    #
    # Derived from cycle_stage_operators by derive_cycle_operator_presence.py.
    # One row per operator per cycle, summarising which stages they were
    # present for.
    #
    # on_full_cycle = 1 means the operator was present for all three stages.
    # This is the primary flag used for standard cycle time reports.
    #
    # UNIQUE(cycle_id, operator_id) allows INSERT OR REPLACE in the
    # derivation script to update rows in-place when re-derived.
    # -------------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cycle_operator_presence (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            cycle_id        INTEGER NOT NULL REFERENCES cycles(id),
            operator_id     INTEGER NOT NULL REFERENCES operators(id),
            on_layup        INTEGER NOT NULL DEFAULT 0,
            on_close        INTEGER NOT NULL DEFAULT 0,
            on_resin        INTEGER NOT NULL DEFAULT 0,
            on_full_cycle   INTEGER NOT NULL DEFAULT 0,
            UNIQUE(cycle_id, operator_id)
        )
    """)
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
    print("  Created table: cycle_operator_presence")

    conn.commit()
    conn.close()

    print(f"""
Done. Database created at:
  {os.path.abspath(db_path)}

Run scripts in this order:
  1. python sync_raw_data.py                   (populate raw_mold_data)
  2. python clean_mold_data.py                 (populate cycles + cycle_stage_operators)
  3. python derive_cycle_operator_presence.py  (populate cycle_operator_presence)

Open the database in DB Browser for SQLite to inspect tables and run queries.
""")


if __name__ == "__main__":
    create_database()
