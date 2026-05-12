"""
sync_raw_data.py

Fetches new data from StrideLinx for all 6 molds and inserts it into the
raw_mold_data table in the local SQLite database.

Uses all_tags for each mold -- every tag the PLC logs -- as a single
unified archive. The cleaning pipeline (clean_mold_data.py) pre-filters
this data to only the columns it needs, so no separate operator-focused
sync is required.

Run this on a schedule to keep the database current. It only fetches data
newer than the most recent record already in the database for each mold,
so it is safe to run frequently.

On first run (empty database), fetches the past INITIAL_LOOKBACK_DAYS days.

USAGE
-----
    python sync_raw_data.py

SCHEDULING (Ubuntu)
-----
    */15 * * * * /path/to/venv/bin/python /path/to/sync_raw_data.py >> /var/log/mold_sync.log 2>&1

DEPENDENCIES
-----
    pip install requests pyyaml pytz
"""

import csv
import io
import sqlite3
import requests
import datetime as dt
import pytz
import os
import sys
import yaml

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
CONFIG_FILE = 'config_vars.yaml'

with open(CONFIG_FILE, 'r') as file:
    config_data = yaml.safe_load(file)
    DB_PATH = config_data['db_path']
# DB_PATH = "C:/Users/Ryan.Larson/Documents/Rockwell Manufacturing Database/manufacturing.db"

# API_CONFIG_DIR = "E:/github/plc-data-analysis/ID_Tracking/IDApp_v2/libs"

# How many days back to fetch on the very first run (empty database).
# StrideLinx keeps 3 years of rolling data (up to 1095 days).
# Start smaller for testing; increase for backfills.
INITIAL_LOOKBACK_DAYS = 365 * 5
# INITIAL_LOOKBACK_DAYS = 90

LOCAL_TZ_NAME = "US/Mountain"

# ---------------------------------------------------------------------------
# Import API config
# ---------------------------------------------------------------------------
# sys.path.insert(0, API_CONFIG_DIR)
import api_config_vars as api

# ---------------------------------------------------------------------------
# Column mapping
#
# Maps the "ref" string from all_tags to the column name in raw_mold_data.
# Any ref not listed here is silently ignored -- all_tags has more tags
# than raw_mold_data stores. Add entries here if you add columns later.
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

KNOWN_COLUMNS = {"time"} | set(REF_TO_COLUMN.keys())


# ---------------------------------------------------------------------------
# Timezone helpers
# ---------------------------------------------------------------------------

def to_api_timestring(naive_datetime):
    """
    Convert a naive local (Mountain) datetime to the CET-based string
    StrideLinx expects, with the 1-hour offset adjustment.
    """
    local_tz = pytz.timezone(LOCAL_TZ_NAME)
    cet      = pytz.timezone("CET")
    localized = local_tz.localize(naive_datetime)
    as_cet    = localized.astimezone(cet)
    adjusted  = as_cet - dt.timedelta(hours=1)
    return adjusted.strftime("%Y-%m-%dT%H:%M:%SZ")


def now_local():
    """Current time as a naive datetime in Mountain time."""
    return dt.datetime.now(pytz.timezone(LOCAL_TZ_NAME)).replace(tzinfo=None)


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_latest_timestamp(cursor, mold_name):
    """
    Most recent record_timestamp already stored for this mold.
    Returns None if no rows exist yet.
    """
    cursor.execute(
        "SELECT MAX(record_timestamp) FROM raw_mold_data WHERE mold_name = ?",
        (mold_name,)
    )
    return cursor.fetchone()[0]


def log_sync_start(cursor, source):
    started_at = dt.datetime.now(dt.timezone.utc).isoformat()
    cursor.execute(
        "INSERT INTO sync_log (started_at, source, status) "
        "VALUES (?, ?, 'running')",
        (started_at, source)
    )
    return cursor.lastrowid


def log_sync_finish(cursor, log_id, rows_inserted, rows_skipped,
                    status, error=None):
    finished_at = dt.datetime.now(dt.timezone.utc).isoformat()
    cursor.execute("""
        UPDATE sync_log
        SET finished_at   = ?,
            rows_inserted = ?,
            rows_skipped  = ?,
            status        = ?,
            error_message = ?
        WHERE id = ?
    """, (finished_at, rows_inserted, rows_skipped, status, error, log_id))


# ---------------------------------------------------------------------------
# API fetch
# ---------------------------------------------------------------------------

def fetch_mold_data(mold_name, dtstart_str, dtend_str):
    """
    POST to the StrideLinx data-export API for one mold using all_tags.
    Returns the raw CSV response text.
    """
    payload = {
        "source":   {"publicId": api.publicIds[mold_name]},
        "tags":     api.all_tags[mold_name],
        "start":    dtstart_str,
        "end":      dtend_str,
        "timeZone": "America/Denver",
    }
    headers = api.request_operator_headers()
    response = requests.request("POST", api.url, json=payload, headers=headers)
    response.raise_for_status()
    return response.text

def fetch_resin_data(resin_name, dtstart_str, dtend_str):
    """
    POST to the StrideLinx data-export API for one resin station using all_tags.
    Returns the raw CSV response text.
    """
    payload = {
        "source":   {"publicId": api.publicIds[resin_name]},
        "tags":     api.all_resin_tags[resin_name],
        "start":    dtstart_str,
        "end":      dtend_str,
        "timeZone": "America/Denver",
    }
    headers = api.request_operator_headers()
    response = requests.request("POST", api.url, json=payload, headers=headers)
    response.raise_for_status()
    return response.text

# ---------------------------------------------------------------------------
# CSV parsing
# ---------------------------------------------------------------------------

def parse_csv_response(raw_text):
    """
    Parse the StrideLinx CSV response using csv.DictReader, which handles
    quoted fields correctly. The previous naive line.split(',') approach
    broke on quoted fields and failed to handle the metadata artifact line
    the API appends at the end of each response.

    Returns a list of row dicts containing only KNOWN_COLUMNS keys.
    Rows without a usable 'time' value are dropped.
    """
    raw_text = raw_text.replace('\r\n', '\n').replace('\r', '\n')

    clean_lines = []
    for line in raw_text.split('\n'):
        stripped = line.strip().strip('"')
        if not stripped:
            continue
        if stripped.replace(',', '') == '':
            continue
        # The API appends a lone ISO timestamp as a metadata artifact on
        # the last line. Detect and drop it.
        try:
            dt.datetime.fromisoformat(
                stripped.rstrip('Z').replace('Z', '+00:00')
            )
            continue
        except ValueError:
            pass
        clean_lines.append(line)

    if len(clean_lines) < 2:
        return []

    rows = []
    for raw_row in csv.DictReader(io.StringIO('\n'.join(clean_lines))):
        row = {}
        for key, val in raw_row.items():
            if key is None:
                continue
            key = key.strip()
            if key not in KNOWN_COLUMNS:
                continue
            val = val.strip() if val else ''
            row[key] = val if val != '' else None
        if not row.get('time'):
            continue
        rows.append(row)

    return rows


def row_to_db_record(row_dict, mold_name, fetched_at):
    """
    Convert one parsed row dict into a dict ready for database insertion.
    Returns None if the timestamp is not a valid full datetime.

    MILLISECOND PRECISION IS REQUIRED. The PLC fires multiple tag updates
    within milliseconds of each other. Truncating to seconds causes the
    UNIQUE(mold_name, record_timestamp) constraint to silently drop all
    but one event per second, losing nearly all cycle and operator data.

    Stored format: "2026-04-15T07:31:34.865"
    ISO strings with milliseconds sort correctly as plain text in SQLite.
    """
    time_val = row_dict.get("time")
    if not time_val:
        return None

    try:
        normalised = time_val.strip().replace(' ', 'T')
        if normalised.endswith('Z'):
            normalised = normalised[:-1] + '+00:00'
        parsed_ts = dt.datetime.fromisoformat(normalised)
        # Trim microseconds to milliseconds (6 fractional digits -> 3)
        record_timestamp = parsed_ts.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
    except (ValueError, AttributeError):
        return None

    record = {
        "mold_name":        mold_name,
        "fetched_at":       fetched_at,
        "record_timestamp": record_timestamp,
        "processed_at":     None,
        "layup_time":    None, "close_time":    None,
        "resin_time":    None, "cycle_time":    None,
        "leak_time":     None, "leak_count":    None,
        "parts_count":   None, "weekly_count":  None,
        "monthly_count": None, "trash_count":   None,
        "lead":          None, "assistant_1":   None,
        "assistant_2":   None, "assistant_3":   None,
        "bag":           None, "bag_days":      None,
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
# Per-mold sync
# ---------------------------------------------------------------------------

def sync_mold(mold_name, conn):
    """
    Fetch and insert new rows for one mold.
    Returns (rows_inserted, rows_skipped).
    """
    cursor = conn.cursor()
    log_id = log_sync_start(cursor, f"mold:{mold_name}")
    conn.commit()

    rows_inserted = 0
    rows_skipped  = 0

    try:
        latest = get_latest_timestamp(cursor, mold_name)

        if latest is None:
            dtstart = now_local() - dt.timedelta(days=INITIAL_LOOKBACK_DAYS)
            print(f"  {mold_name}: No existing data. "
                  f"Fetching last {INITIAL_LOOKBACK_DAYS} days.")
        else:
            # Advance by 1 ms so we don't re-fetch the last stored row
            dtstart = (dt.datetime.fromisoformat(latest)
                       + dt.timedelta(milliseconds=1))
            print(f"  {mold_name}: Fetching from {dtstart} onwards.")

        dtend = now_local()

        if dtstart >= dtend:
            print(f"  {mold_name}: Already up to date.")
            log_sync_finish(cursor, log_id, 0, 0, "up_to_date")
            conn.commit()
            return 0, 0

        raw_text   = fetch_mold_data(
            mold_name,
            to_api_timestring(dtstart),
            to_api_timestring(dtend),
        )
        fetched_at = dt.datetime.now(dt.timezone.utc).isoformat()
        rows       = parse_csv_response(raw_text)

        if not rows:
            print(f"  {mold_name}: API returned no usable rows.")
            log_sync_finish(cursor, log_id, 0, 0, "success")
            conn.commit()
            return 0, 0

        bad_timestamps = 0
        for row_dict in rows:
            record = row_to_db_record(row_dict, mold_name, fetched_at)
            if record is None:
                bad_timestamps += 1
                rows_skipped   += 1
                continue

            cursor.execute("""
                INSERT OR IGNORE INTO raw_mold_data (
                    mold_name, fetched_at, record_timestamp,
                    layup_time, close_time, resin_time, cycle_time,
                    leak_time, leak_count, parts_count, weekly_count,
                    monthly_count, trash_count,
                    lead, assistant_1, assistant_2, assistant_3,
                    bag, bag_days, bag_cycles,
                    processed_at
                ) VALUES (
                    :mold_name, :fetched_at, :record_timestamp,
                    :layup_time, :close_time, :resin_time, :cycle_time,
                    :leak_time, :leak_count, :parts_count, :weekly_count,
                    :monthly_count, :trash_count,
                    :lead, :assistant_1, :assistant_2, :assistant_3,
                    :bag, :bag_days, :bag_cycles,
                    :processed_at
                )
            """, record)

            if cursor.rowcount == 1:
                rows_inserted += 1
            else:
                rows_skipped  += 1

        if bad_timestamps > 0:
            print(f"  {mold_name}: {bad_timestamps} partial-timestamp rows "
                  f"skipped (normal for this API).")

        conn.commit()
        log_sync_finish(cursor, log_id, rows_inserted, rows_skipped, "success")
        conn.commit()

        print(f"  {mold_name}: inserted {rows_inserted}, "
              f"skipped {rows_skipped}.")
        return rows_inserted, rows_skipped

    except Exception as e:
        conn.rollback()
        log_sync_finish(cursor, log_id, rows_inserted, rows_skipped,
                        "error", str(e))
        conn.commit()
        print(f"  {mold_name}: ERROR -- {e}")
        raise


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_sync(db_path=DB_PATH):
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at {os.path.abspath(db_path)}")
        return

    print(f"\n[{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
          f"Starting mold data sync...")

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")

    total_inserted = 0
    total_skipped  = 0
    errors         = []

    for mold_name in api.molds:
        try:
            inserted, skipped = sync_mold(mold_name, conn)
            total_inserted += inserted
            total_skipped  += skipped
        except Exception as e:
            errors.append((mold_name, str(e)))

    conn.close()

    print(f"\nSync complete. "
          f"Total inserted: {total_inserted}, skipped: {total_skipped}")
    if errors:
        print(f"Errors on {len(errors)} mold(s):")
        for mold, err in errors:
            print(f"  {mold}: {err}")
    else:
        print("All molds synced successfully.")


if __name__ == "__main__":
    run_sync()