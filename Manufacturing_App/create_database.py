"""
create_database.py

Run this ONCE to create the SQLite database with all raw data tables.
Safe to run again -- all CREATE TABLE statements use IF NOT EXISTS, so
no existing data will be touched if you re-run it.

Usage:
    python create_database.py

After running, open the resulting .db file in DB Browser for SQLite
(free download at https://sqlitebrowser.org/) to inspect the structure.
"""

import sqlite3
import os

# Change this path to wherever you want the database to live.
# On the Ubuntu server this might be: /home/youruser/manufacturing/manufacturing.db
DB_PATH = "C:/Users/Ryan.Larson/Documents/Rockwell Manufacturing Database/manufacturing.db"


def create_database(db_path: str = DB_PATH):
    print(f"Creating database at: {os.path.abspath(db_path)}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # WAL mode lets the Dash app read the database at the same time the sync
    # job is writing to it, without them blocking each other.
    cursor.execute("PRAGMA journal_mode=WAL")

    # -------------------------------------------------------------------------
    # raw_mold_data
    #
    # One table for all 6 molds. mold_name tells you which mold a row is from.
    # Column names correspond to the "ref" strings in your all_tags lists.
    #
    # The UNIQUE constraint on (mold_name, record_timestamp) means that if the
    # sync job tries to insert a record that already exists, it skips it rather
    # than creating a duplicate. This makes incremental syncing safe to run
    # repeatedly without worrying about overlap.
    #
    # raw_response stores the full CSV text from the API for that fetch run.
    # This is your ground truth -- if you ever need to re-parse the data with
    # different logic, it is all preserved here.
    #
    # processed_at is NULL until the cleaning pipeline consumes this row.
    # -------------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_mold_data (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            mold_name           TEXT    NOT NULL,
            fetched_at          TEXT    NOT NULL,
            record_timestamp    TEXT    NOT NULL,

            -- Stage timing (stored in minutes, matching your 0.0166667 factor)
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

            -- Operator ID columns
            lead                REAL,
            assistant_1         REAL,
            assistant_2         REAL,
            assistant_3         REAL,

            -- Bag tracking columns
            bag                 REAL,
            bag_days            REAL,
            bag_cycles          REAL,

            -- Full raw API response text for this mold on this fetch
            raw_response        TEXT,

            -- Set by the cleaning pipeline when this row has been processed
            processed_at        TEXT    DEFAULT NULL,

            UNIQUE(mold_name, record_timestamp)
        )
    """)
    print("  Created table: raw_mold_data")

    # Speeds up the incremental sync query (finding the latest timestamp per mold)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_raw_mold_timestamp
        ON raw_mold_data (mold_name, record_timestamp)
    """)
    # Speeds up the cleaning pipeline (finding all unprocessed rows)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_raw_mold_processed
        ON raw_mold_data (processed_at)
    """)
    print("  Created indexes for raw_mold_data")

    # -------------------------------------------------------------------------
    # raw_resin_data
    #
    # Two stations, identified by station_number (1 or 2).
    # Columns are placeholders -- adjust to match what StrideLinx returns
    # once you set up that data retrieval.
    # -------------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_resin_data (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            station_number      INTEGER NOT NULL,
            fetched_at          TEXT    NOT NULL,
            record_timestamp    TEXT    NOT NULL,

            amount_kg           REAL,

            raw_response        TEXT,
            processed_at        TEXT    DEFAULT NULL,

            UNIQUE(station_number, record_timestamp)
        )
    """)
    print("  Created table: raw_resin_data")

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_raw_resin_timestamp
        ON raw_resin_data (station_number, record_timestamp)
    """)
    print("  Created indexes for raw_resin_data")

    # -------------------------------------------------------------------------
    # raw_temperature_data
    #
    # Stubbed out for now. source_tag identifies the sensor or channel.
    # Add columns once you know what the StrideLinx temperature page returns.
    # -------------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_temperature_data (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            source_tag          TEXT    NOT NULL,
            fetched_at          TEXT    NOT NULL,
            record_timestamp    TEXT    NOT NULL,

            temperature_value   REAL,

            raw_response        TEXT,
            processed_at        TEXT    DEFAULT NULL,

            UNIQUE(source_tag, record_timestamp)
        )
    """)
    print("  Created table: raw_temperature_data")

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_raw_temp_timestamp
        ON raw_temperature_data (source_tag, record_timestamp)
    """)
    print("  Created indexes for raw_temperature_data")

    # -------------------------------------------------------------------------
    # sync_log
    #
    # A record of every sync run. Useful for diagnosing gaps in your data if
    # the scheduled job fails silently.
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

    conn.commit()
    conn.close()
    print(f"\nDone. Open '{db_path}' in DB Browser for SQLite to inspect the tables.")
    print("Download DB Browser free at: https://sqlitebrowser.org/")


if __name__ == "__main__":
    create_database()
