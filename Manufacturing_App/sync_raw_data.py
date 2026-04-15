"""
sync_raw_data.py

Fetches new data from StrideLinx for all 6 molds and inserts it into the
raw_mold_data table in the local SQLite database.

Run this on a schedule (cron, systemd timer, or APScheduler) to keep the
database up to date. It only fetches data that is newer than the most recent
record already in the database for each mold, so it is safe to run frequently.

On first run (empty database), it fetches the past INITIAL_LOOKBACK_DAYS days.
On subsequent runs, it fetches from the last known timestamp up to now.

Usage:
    python sync_raw_data.py

Dependencies (pip install):
    requests, pyyaml, pytz
    (numpy and pandas are NOT required here -- this script stays lean)
"""

import sqlite3
import requests
import json
import datetime as dt
import pytz
import os
import sys

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Path to your database file. Must match what you used in create_database.py.
DB_PATH = "C:/Users/Ryan.Larson/Documents/Rockwell Manufacturing Database/manufacturing.db"
# DB_PATH = "manufacturing.db"

# Path to your api_config_vars.py file. If this sync script lives in the same
# folder as api_config_vars.py, leave this as-is. Otherwise adjust the path
# and the sys.path.insert line below.
API_CONFIG_DIR = "E:/github/plc-data-analysis/ID_Tracking/IDApp_v2/libs"

# How many days back to fetch on the very first run (empty database).
# StrideLinx keeps 3 years of rolling data, so you could set this up to 1095.
# Start smaller (e.g. 90) to test, then do a one-time historical backfill.
INITIAL_LOOKBACK_DAYS = 30

# StrideLinx uses Mountain Time for your facility. The API needs the quirky
# CET conversion with a 1-hour offset that your existing code already handles.
LOCAL_TZ_NAME = "US/Mountain"

# ---------------------------------------------------------------------------
# Import your existing API config
# ---------------------------------------------------------------------------
sys.path.insert(0, API_CONFIG_DIR)
import api_config_vars as api

# ---------------------------------------------------------------------------
# Column mapping
#
# Maps the "ref" string from your all_tags lists to the corresponding column
# name in raw_mold_data. Any ref not in this map will be ignored (no error).
# Add entries here if you add new tags to your all_tags lists in the future.
# ---------------------------------------------------------------------------
REF_TO_COLUMN = {
    "Layup Time":    "layup_time",
    "Close Time":    "close_time",
    "Resin Time":    "resin_time",
    "Cycle Time":    "cycle_time",
    "Leak Time":     "leak_time",
    "Leak Count":    "leak_count",
    "Parts Count":   "parts_count",
    "Weekly Count":  "weekly_count",
    "Monthly Count": "monthly_count",
    "Trash Count":   "trash_count",
    "Lead":          "lead",
    "Assistant 1":   "assistant_1",
    "Assistant 2":   "assistant_2",
    "Assistant 3":   "assistant_3",
    "Bag":           "bag",
    "Bag Days":      "bag_days",
    "Bag Cycles":    "bag_cycles",
}


# ---------------------------------------------------------------------------
# Timezone helpers
# (replicating the logic from load_operator_data in cycle_time_methods_v2.py)
# ---------------------------------------------------------------------------

def to_api_timestring(naive_datetime, local_tz_name=LOCAL_TZ_NAME):
    """
    Convert a naive local datetime to the CET-based API format that
    StrideLinx expects, with the 1-hour offset adjustment your existing
    code applies.
    """
    local_tz = pytz.timezone(local_tz_name)
    cet = pytz.timezone("CET")

    localized = local_tz.localize(naive_datetime)
    as_cet = localized.astimezone(cet)

    # Apply the 1-hour offset that your existing code uses
    adjusted = as_cet - dt.timedelta(hours=1)

    return adjusted.strftime("%Y-%m-%dT%H:%M:%SZ")


def now_local():
    """Return the current time as a naive datetime in local (Mountain) time."""
    local_tz = pytz.timezone(LOCAL_TZ_NAME)
    return dt.datetime.now(local_tz).replace(tzinfo=None)


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_latest_timestamp(cursor, mold_name):
    """
    Return the most recent record_timestamp already in the database for this
    mold, or None if the table is empty for this mold.
    """
    cursor.execute(
        "SELECT MAX(record_timestamp) FROM raw_mold_data WHERE mold_name = ?",
        (mold_name,)
    )
    result = cursor.fetchone()[0]
    return result  # Will be a string like "2024-11-15T14:23:00" or None


def log_sync_start(cursor, source):
    """Insert a new sync_log row and return its id."""
    started_at = dt.datetime.now(dt.timezone.utc).isoformat()
    cursor.execute(
        "INSERT INTO sync_log (started_at, source, status) VALUES (?, ?, 'running')",
        (started_at, source)
    )
    return cursor.lastrowid


def log_sync_finish(cursor, log_id, rows_inserted, rows_skipped, status, error=None):
    finished_at = dt.datetime.now(dt.timezone.utc).isoformat()
    cursor.execute("""
        UPDATE sync_log
        SET finished_at = ?, rows_inserted = ?, rows_skipped = ?,
            status = ?, error_message = ?
        WHERE id = ?
    """, (finished_at, rows_inserted, rows_skipped, status, error, log_id))


# ---------------------------------------------------------------------------
# API fetch
# ---------------------------------------------------------------------------

def fetch_mold_data(mold_name, dtstart_str, dtend_str):
    """
    Call the StrideLinx API for one mold using all_tags (the full tag set).
    Returns the raw CSV response text.

    dtstart_str and dtend_str should already be formatted API strings,
    as produced by to_api_timestring().
    """
    payload = {
        "source": {"publicId": api.publicIds[mold_name]},
        "tags": api.all_tags[mold_name],
        "start": dtstart_str,
        "end": dtend_str,
        "timeZone": "America/Denver"
    }

    # Use request_operator_headers() -- this refreshes the bearer token.
    # Note: your load_raw_data_single_mold_all_data function had a bug where
    # it referenced api.operator_headers (the static commented-out dict)
    # instead of calling api.request_operator_headers(). This is the fix.
    headers = api.request_operator_headers()

    response = requests.request("POST", api.url, json=payload, headers=headers)
    response.raise_for_status()

    return response.text


# ---------------------------------------------------------------------------
# CSV parsing
#
# Replicates the DataFrame-free version of what your existing functions do,
# so this script doesn't need pandas or numpy as dependencies.
# ---------------------------------------------------------------------------

def parse_csv_response(raw_text):
    """
    Parse the CSV response from StrideLinx into a list of dicts.
    Each dict has 'time' (string) and one key per column header.
    Empty cells are stored as None.

    Returns (column_names, list_of_row_dicts, cleaned_raw_text)
    The cleaned_raw_text strips the carriage return issue your existing
    code handles.
    """
    # Fix the carriage return issue your existing code handles
    raw_text = raw_text.replace('\r\n', '\n').replace('\r', '\n')

    lines = [line for line in raw_text.split('\n') if line.strip()]
    if len(lines) < 2:
        return [], [], raw_text

    header_line = lines[0]
    columns = [c.strip() for c in header_line.split(',')]

    rows = []
    for line in lines[1:]:
        values = line.split(',')
        row = {}
        for i, col in enumerate(columns):
            val = values[i].strip() if i < len(values) else ''
            row[col] = val if val != '' else None
        rows.append(row)

    return columns, rows, raw_text


def row_to_db_record(row_dict, mold_name, fetched_at, raw_response):
    """
    Convert one parsed CSV row into a dict ready for database insertion.
    Returns None if the row has no timestamp (shouldn't happen, but safe).
    """
    time_val = row_dict.get("time")
    if time_val is None:
        return None

    record = {
        "mold_name":        mold_name,
        "fetched_at":       fetched_at,
        "record_timestamp": time_val,
        "raw_response":     raw_response,
        "processed_at":     None,
        # All data columns default to None; filled in below
        "layup_time":    None,
        "close_time":    None,
        "resin_time":    None,
        "cycle_time":    None,
        "leak_time":     None,
        "leak_count":    None,
        "parts_count":   None,
        "weekly_count":  None,
        "monthly_count": None,
        "trash_count":   None,
        "lead":          None,
        "assistant_1":   None,
        "assistant_2":   None,
        "assistant_3":   None,
        "bag":           None,
        "bag_days":      None,
        "bag_cycles":    None,
    }

    for ref_name, col_name in REF_TO_COLUMN.items():
        val = row_dict.get(ref_name)
        if val is not None:
            try:
                record[col_name] = float(val)
            except (ValueError, TypeError):
                record[col_name] = None

    return record


# ---------------------------------------------------------------------------
# Main sync function
# ---------------------------------------------------------------------------

def sync_mold(mold_name, conn):
    """
    Fetch and insert new data for one mold. Returns (rows_inserted, rows_skipped).
    """
    cursor = conn.cursor()
    log_id = log_sync_start(cursor, f"mold:{mold_name}")
    conn.commit()

    rows_inserted = 0
    rows_skipped = 0

    try:
        # Determine the time window to fetch
        latest = get_latest_timestamp(cursor, mold_name)

        if latest is None:
            # First run for this mold -- go back INITIAL_LOOKBACK_DAYS
            dtstart = now_local() - dt.timedelta(days=INITIAL_LOOKBACK_DAYS)
            print(f"  {mold_name}: No existing data. Fetching last {INITIAL_LOOKBACK_DAYS} days.")
        else:
            # Parse the stored timestamp and add 1 second to avoid re-fetching
            # the last record we already have.
            dtstart = dt.datetime.fromisoformat(latest) + dt.timedelta(seconds=1)
            print(f"  {mold_name}: Fetching from {dtstart} onwards.")

        dtend = now_local()

        if dtstart >= dtend:
            print(f"  {mold_name}: Already up to date.")
            log_sync_finish(cursor, log_id, 0, 0, "up_to_date")
            conn.commit()
            return 0, 0

        dtstart_str = to_api_timestring(dtstart)
        dtend_str = to_api_timestring(dtend)

        # Fetch from API
        raw_text = fetch_mold_data(mold_name, dtstart_str, dtend_str)
        fetched_at = dt.datetime.now(dt.timezone.utc).isoformat()

        # Parse the response
        columns, rows, cleaned_text = parse_csv_response(raw_text)

        if not rows:
            print(f"  {mold_name}: API returned no rows.")
            log_sync_finish(cursor, log_id, 0, 0, "success")
            conn.commit()
            return 0, 0

        # Insert each row. INSERT OR IGNORE skips rows that already exist
        # (based on the UNIQUE constraint on mold_name + record_timestamp).
        for row_dict in rows:
            record = row_to_db_record(row_dict, mold_name, fetched_at, cleaned_text)
            if record is None:
                rows_skipped += 1
                continue

            cursor.execute("""
                INSERT OR IGNORE INTO raw_mold_data (
                    mold_name, fetched_at, record_timestamp,
                    layup_time, close_time, resin_time, cycle_time, leak_time,
                    leak_count, parts_count, weekly_count, monthly_count, trash_count,
                    lead, assistant_1, assistant_2, assistant_3,
                    bag, bag_days, bag_cycles,
                    raw_response, processed_at
                ) VALUES (
                    :mold_name, :fetched_at, :record_timestamp,
                    :layup_time, :close_time, :resin_time, :cycle_time, :leak_time,
                    :leak_count, :parts_count, :weekly_count, :monthly_count, :trash_count,
                    :lead, :assistant_1, :assistant_2, :assistant_3,
                    :bag, :bag_days, :bag_cycles,
                    :raw_response, :processed_at
                )
            """, record)

            if cursor.rowcount == 1:
                rows_inserted += 1
            else:
                rows_skipped += 1

        conn.commit()
        log_sync_finish(cursor, log_id, rows_inserted, rows_skipped, "success")
        conn.commit()

        print(f"  {mold_name}: Inserted {rows_inserted} rows, skipped {rows_skipped} duplicates.")
        return rows_inserted, rows_skipped

    except Exception as e:
        conn.rollback()
        log_sync_finish(cursor, log_id, rows_inserted, rows_skipped, "error", str(e))
        conn.commit()
        print(f"  {mold_name}: ERROR -- {e}")
        raise


def run_sync(db_path=DB_PATH):
    """Sync all 6 molds. Called by the scheduler or directly."""
    print(f"\n[{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting mold data sync...")

    conn = sqlite3.connect(db_path)

    total_inserted = 0
    total_skipped = 0
    errors = []

    for mold_name in api.molds:
        try:
            inserted, skipped = sync_mold(mold_name, conn)
            total_inserted += inserted
            total_skipped += skipped
        except Exception as e:
            errors.append((mold_name, str(e)))

    conn.close()

    print(f"\nSync complete. Total inserted: {total_inserted}, skipped: {total_skipped}")
    if errors:
        print(f"Errors on {len(errors)} mold(s):")
        for mold, err in errors:
            print(f"  {mold}: {err}")
    else:
        print("All molds synced successfully.")


if __name__ == "__main__":
    run_sync()
