"""
analytics.py

Functions for querying cycle time statistics and generating plots from
the manufacturing database. All functions take a database connection or
path and return either DataFrames or matplotlib figures.

Usage example:
    import sqlite3
    from analytics import get_operator_cycle_times, plot_operator_boxplot

    conn = sqlite3.connect("manufacturing.db")
    df = get_operator_cycle_times(conn, employee_number=69)
    fig = plot_operator_boxplot(df, employee_number=69)
    fig.savefig("operator_69_cycles.png", dpi=200)
    conn.close()

Dependencies:
    pip install pandas numpy matplotlib seaborn
"""

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import datetime as dt
import os
import yaml

CONFIG_FILE = 'config_vars.yaml'

with open(CONFIG_FILE, 'r') as file:
    config_data = yaml.safe_load(file)
    DB_PATH = config_data['db_path']
# DB_PATH = "C:/Users/Ryan.Larson/Documents/Rockwell Manufacturing Database/manufacturing.db"


# ---------------------------------------------------------------------------
# Database connection helper
# ---------------------------------------------------------------------------

def get_connection(db_path: str = DB_PATH, read_only: bool = True) -> sqlite3.Connection:
    """
    Open a connection to the database.
    read_only=True (default): safe for Dash app callbacks that only query.
    read_only=False: required for any callback that writes (add/retire operator).
    """
    if read_only:
        uri  = "file:///" + db_path.replace("\\", "/") + "?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
    else:
        conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# Operator queries
# ---------------------------------------------------------------------------

def get_shift_cycle_times(
    conn: sqlite3.Connection,
    shift: str,
    mold_name: str = None,
    date_start: str = None,
    date_end: str = None,
    full_cycle_only: bool = True,
    exclude_flagged: bool = True,
) -> pd.DataFrame:
    """
    Return all cycle times for every operator on a given shift, combined
    into a single DataFrame. The 'name' column is set to the shift name
    so it renders as a single labelled trace on the boxplot.

    shift : 'Day', 'Swing', or 'Graveyard'
    All other parameters match get_operator_cycle_times.
    """
    where_clauses = ["o.shift = ?"]
    params = [shift]

    if mold_name:
        where_clauses.append("c.mold_name = ?")
        params.append(mold_name)
    if date_start:
        where_clauses.append("c.cycle_timestamp >= ?")
        params.append(date_start)
    if date_end:
        end_dt = (dt.date.fromisoformat(date_end)
                  + dt.timedelta(days=1)).isoformat()
        where_clauses.append("c.cycle_timestamp < ?")
        params.append(end_dt)
    if full_cycle_only:
        where_clauses.append("p.on_full_cycle = 1")
    if exclude_flagged:
        where_clauses.append("c.exclusion_reason IS NULL")

    # Also exclude operators whose active_to has passed before the cycle date,
    # meaning the cycle happened after they left -- they were active at cycle time
    # if active_from <= cycle and (active_to is null or active_to > cycle).
    where_clauses.append(
        "(o.active_to IS NULL OR o.active_to > c.cycle_timestamp)"
    )
    where_clauses.append("o.active_from <= c.cycle_timestamp")

    where_sql = "WHERE " + " AND ".join(where_clauses)

    df = pd.read_sql(f"""
        SELECT
            c.id            AS cycle_id,
            c.mold_name,
            c.cycle_timestamp,
            c.cycle_time,
            c.layup_time,
            c.close_time,
            c.resin_time,
            p.on_layup,
            p.on_close,
            p.on_resin,
            p.on_full_cycle,
            o.id            AS operator_id,
            o.employee_number,
            o.name,
            o.shift
        FROM cycle_operator_presence p
        JOIN cycles    c ON c.id = p.cycle_id
        JOIN operators o ON o.id = p.operator_id
        {where_sql}
        ORDER BY c.cycle_timestamp ASC
    """, conn, params=params)

    if not df.empty:
        df["cycle_timestamp"] = pd.to_datetime(df["cycle_timestamp"], format="ISO8601")
        # Label as the shift name so it shows as one trace
        df["name"] = f"{shift} Shift"

    return df


def get_all_cycles(
    conn: sqlite3.Connection,
    mold_name: str = None,
    date_start: str = None,
    date_end: str = None,
    full_cycle_only: bool = True,
    exclude_flagged: bool = True,
) -> pd.DataFrame:
    """
    Return all cycles across every operator and shift combined, labelled
    as 'All Shifts'. Used as a facility-wide baseline for comparison.

    All parameters match get_operator_cycle_times except employee_number.
    """
    where_clauses = []
    params = []

    if mold_name:
        where_clauses.append("c.mold_name = ?")
        params.append(mold_name)
    if date_start:
        where_clauses.append("c.cycle_timestamp >= ?")
        params.append(date_start)
    if date_end:
        end_dt = (dt.date.fromisoformat(date_end)
                  + dt.timedelta(days=1)).isoformat()
        where_clauses.append("c.cycle_timestamp < ?")
        params.append(end_dt)
    if full_cycle_only:
        where_clauses.append("p.on_full_cycle = 1")
    if exclude_flagged:
        where_clauses.append("c.exclusion_reason IS NULL")

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    df = pd.read_sql(f"""
        SELECT
            c.id            AS cycle_id,
            c.mold_name,
            c.cycle_timestamp,
            c.cycle_time,
            c.layup_time,
            c.close_time,
            c.resin_time,
            p.on_layup,
            p.on_close,
            p.on_resin,
            p.on_full_cycle,
            o.id            AS operator_id,
            o.employee_number,
            o.name,
            o.shift
        FROM cycle_operator_presence p
        JOIN cycles    c ON c.id = p.cycle_id
        JOIN operators o ON o.id = p.operator_id
        {where_sql}
        ORDER BY c.cycle_timestamp ASC
    """, conn, params=params)

    if not df.empty:
        df["cycle_timestamp"] = pd.to_datetime(df["cycle_timestamp"], format="ISO8601")
        df["name"] = "All Shifts"

    return df


def get_operators_by_shift(conn: sqlite3.Connection) -> dict:
    """
    Return a dict mapping shift name -> list of employee_numbers
    for all currently active operators.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT shift, employee_number, name
        FROM operators
        WHERE active_to IS NULL
        ORDER BY shift, name
    """)
    result = {}
    for shift, emp_num, name in cursor.fetchall():
        if shift not in result:
            result[shift] = []
        result[shift].append({"employee_number": emp_num, "name": name})
    return result


def get_cycles_for_explorer(
    conn: sqlite3.Connection,
    mold_name: str = None,
    date_start: str = None,
    date_end: str = None,
    employee_numbers: list = None,
    exclude_flagged: bool = True,
) -> pd.DataFrame:
    """
    Return cycle data for the Cycle Analysis explorer page.

    Fetches every cycle matching the filters and computes derived columns
    needed for the x/y/color axes:
        hour_of_day   -- 0-23, for time-of-day analysis
        day_of_week   -- 0=Monday ... 6=Sunday
        day_name      -- 'Monday' ... 'Sunday'
        operator_name -- name of the operator (or 'Unknown' if none matched)
        shift         -- operator's shift at cycle time

    Unlike get_operator_cycle_times, this is not filtered to operators
    present for the full cycle -- it returns all cycles that match the
    date/mold/operator filters, with operator info attached where available.

    Parameters
    ----------
    employee_numbers : list of int, optional
        If provided, only cycles where at least one of these operators
        was present (on_full_cycle=1) are returned. If None, all cycles
        are returned regardless of operator.
    """
    where_clauses = []
    params        = []

    if mold_name:
        where_clauses.append("c.mold_name = ?")
        params.append(mold_name)
    if date_start:
        where_clauses.append("c.cycle_timestamp >= ?")
        params.append(date_start)
    if date_end:
        end_dt = (dt.date.fromisoformat(date_end)
                  + dt.timedelta(days=1)).isoformat()
        where_clauses.append("c.cycle_timestamp < ?")
        params.append(end_dt)
    if exclude_flagged:
        where_clauses.append("c.exclusion_reason IS NULL")
    if employee_numbers:
        placeholders = ",".join("?" * len(employee_numbers))
        where_clauses.append(f"""
            EXISTS (
                SELECT 1 FROM cycle_operator_presence p2
                JOIN operators o2 ON o2.id = p2.operator_id
                WHERE p2.cycle_id = c.id
                  AND p2.on_full_cycle = 1
                  AND o2.employee_number IN ({placeholders})
            )
        """)
        params.extend(employee_numbers)

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    df = pd.read_sql(f"""
        SELECT
            c.id              AS cycle_id,
            c.mold_name,
            c.cycle_timestamp,
            c.cycle_time,
            c.layup_time,
            c.close_time,
            c.resin_time,
            c.bag_number,
            c.bag_cycles_raw  AS bag_cycles,
            c.bag_days_raw    AS bag_days,
            c.exclusion_reason
        FROM cycles c
        {where_sql}
        ORDER BY c.cycle_timestamp ASC
    """, conn, params=params)

    if df.empty:
        return df

    df["cycle_timestamp"] = pd.to_datetime(df["cycle_timestamp"], format="ISO8601")
    df["hour_of_day"]     = df["cycle_timestamp"].dt.hour
    df["day_of_week"]     = df["cycle_timestamp"].dt.dayofweek
    df["day_name"]        = df["cycle_timestamp"].dt.day_name()

    # Attach the operator name and shift for each cycle.
    # A cycle may have multiple operators; we pick the one with on_full_cycle=1.
    # If there are multiple full-cycle operators, we take the one with the
    # lowest employee_number (arbitrary but consistent).
    op_df = pd.read_sql("""
        SELECT
            p.cycle_id,
            o.name        AS operator_name,
            o.shift,
            o.employee_number
        FROM cycle_operator_presence p
        JOIN operators o ON o.id = p.operator_id
        WHERE p.on_full_cycle = 1
        ORDER BY p.cycle_id, o.employee_number
    """, conn)

    if not op_df.empty:
        # Keep only the first full-cycle operator per cycle
        op_df = op_df.drop_duplicates(subset="cycle_id", keep="first")
        df = df.merge(
            op_df[["cycle_id", "operator_name", "shift"]],
            on="cycle_id",
            how="left",
        )
    else:
        df["operator_name"] = "Unknown"
        df["shift"]         = "Unknown"

    df["operator_name"] = df["operator_name"].fillna("Unknown")
    df["shift"]         = df["shift"].fillna("Unknown")

    return df


def get_operator_cycle_times(
    conn: sqlite3.Connection,
    employee_number: int,
    mold_name: str = None,
    date_start: str = None,
    date_end: str = None,
    full_cycle_only: bool = True,
    exclude_flagged: bool = True,
) -> pd.DataFrame:
    """
    Return cycle times for a specific operator as a DataFrame.

    Parameters
    ----------
    conn : sqlite3.Connection
    employee_number : int
        The 3-digit employee number (e.g. 69).
    mold_name : str, optional
        Filter to a specific mold ('Brown', 'Purple', etc.).
        If None, returns data across all molds.
    date_start : str, optional
        ISO date string 'YYYY-MM-DD'. Inclusive.
    date_end : str, optional
        ISO date string 'YYYY-MM-DD'. Inclusive.
    full_cycle_only : bool
        If True (default), only include cycles where the operator was
        present for all three stages. If False, includes partial cycles.
    exclude_flagged : bool
        If True (default), excludes cycles with a non-null exclusion_reason
        (first Monday parts, saturated stages, etc.).

    Returns
    -------
    pd.DataFrame with columns:
        cycle_id, mold_name, cycle_timestamp, cycle_time,
        layup_time, close_time, resin_time,
        on_layup, on_close, on_resin, on_full_cycle,
        operator_id, employee_number, name
    """
    where_clauses = ["o.employee_number = ?"]
    params = [employee_number]

    if mold_name:
        where_clauses.append("c.mold_name = ?")
        params.append(mold_name)
    if date_start:
        where_clauses.append("c.cycle_timestamp >= ?")
        params.append(date_start)
    if date_end:
        # Add one day so the end date is inclusive
        end_dt = (dt.date.fromisoformat(date_end)
                  + dt.timedelta(days=1)).isoformat()
        where_clauses.append("c.cycle_timestamp < ?")
        params.append(end_dt)
    if full_cycle_only:
        where_clauses.append("p.on_full_cycle = 1")
    if exclude_flagged:
        where_clauses.append("c.exclusion_reason IS NULL")

    where_sql = "WHERE " + " AND ".join(where_clauses)

    df = pd.read_sql(f"""
        SELECT
            c.id            AS cycle_id,
            c.mold_name,
            c.cycle_timestamp,
            c.cycle_time,
            c.layup_time,
            c.close_time,
            c.resin_time,
            p.on_layup,
            p.on_close,
            p.on_resin,
            p.on_full_cycle,
            o.id            AS operator_id,
            o.employee_number,
            o.name
        FROM cycle_operator_presence p
        JOIN cycles    c ON c.id = p.cycle_id
        JOIN operators o ON o.id = p.operator_id
        {where_sql}
        ORDER BY c.cycle_timestamp ASC
    """, conn, params=params)

    if not df.empty:
        df["cycle_timestamp"] = pd.to_datetime(df["cycle_timestamp"], format="ISO8601")

    return df


def get_operator_stats(
    conn: sqlite3.Connection,
    employee_number: int,
    **kwargs,
) -> dict:
    """
    Return summary statistics for a specific operator's cycle times.

    Accepts the same keyword arguments as get_operator_cycle_times.

    Returns
    -------
    dict with keys:
        employee_number, name, n_cycles, median, mean, std,
        q25, q75, min, max, mold_name (if filtered to one mold)
    """
    df = get_operator_cycle_times(conn, employee_number, **kwargs)

    if df.empty:
        return {
            "employee_number": employee_number,
            "name":            None,
            "n_cycles":        0,
            "median":          None,
            "mean":            None,
            "std":             None,
            "q25":             None,
            "q75":             None,
            "min":             None,
            "max":             None,
        }

    ct = df["cycle_time"].dropna()
    return {
        "employee_number": employee_number,
        "name":            df["name"].iloc[0],
        "n_cycles":        len(ct),
        "median":          round(ct.median(), 2),
        "mean":            round(ct.mean(), 2),
        "std":             round(ct.std(), 2),
        "q25":             round(ct.quantile(0.25), 2),
        "q75":             round(ct.quantile(0.75), 2),
        "min":             round(ct.min(), 2),
        "max":             round(ct.max(), 2),
    }


def get_all_operators_stats(
    conn: sqlite3.Connection,
    **kwargs,
) -> pd.DataFrame:
    """
    Return summary statistics for every operator in the operators table.

    Accepts the same keyword arguments as get_operator_cycle_times
    (except employee_number, which is iterated automatically).

    Returns
    -------
    pd.DataFrame with one row per operator, sorted by median cycle time.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT DISTINCT employee_number FROM operators ORDER BY employee_number"
    )
    emp_numbers = [row[0] for row in cursor.fetchall()]

    rows = []
    for emp_num in emp_numbers:
        stats = get_operator_stats(conn, emp_num, **kwargs)
        rows.append(stats)

    df = pd.DataFrame(rows)
    df = df[df["n_cycles"] > 0].reset_index(drop=True)
    df = df.sort_values("median").reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# Mold-level queries
# ---------------------------------------------------------------------------

def get_mold_cycle_times(
    conn: sqlite3.Connection,
    mold_name: str,
    date_start: str = None,
    date_end: str = None,
    exclude_flagged: bool = True,
) -> pd.DataFrame:
    """
    Return all cycle times for a specific mold, without filtering by operator.
    Useful for facility-wide trend analysis.
    """
    where_clauses = ["c.mold_name = ?"]
    params = [mold_name]

    if date_start:
        where_clauses.append("c.cycle_timestamp >= ?")
        params.append(date_start)
    if date_end:
        end_dt = (dt.date.fromisoformat(date_end)
                  + dt.timedelta(days=1)).isoformat()
        where_clauses.append("c.cycle_timestamp < ?")
        params.append(end_dt)
    if exclude_flagged:
        where_clauses.append("c.exclusion_reason IS NULL")

    where_sql = "WHERE " + " AND ".join(where_clauses)

    df = pd.read_sql(f"""
        SELECT
            c.id AS cycle_id,
            c.mold_name,
            c.cycle_timestamp,
            c.cycle_time,
            c.layup_time,
            c.close_time,
            c.resin_time
        FROM cycles c
        {where_sql}
        ORDER BY c.cycle_timestamp ASC
    """, conn, params=params)

    if not df.empty:
        df["cycle_timestamp"] = pd.to_datetime(df["cycle_timestamp"], format="ISO8601")

    return df


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_operator_boxplot(
    df: pd.DataFrame,
    employee_number: int = None,
    time_column: str = "cycle_time",
    group_by: str = None,
    title: str = None,
    figsize: tuple = (8, 5),
) -> plt.Figure:
    """
    Generate a seaborn boxplot of cycle times for one operator.

    Parameters
    ----------
    df : pd.DataFrame
        Output of get_operator_cycle_times or similar.
    employee_number : int, optional
        Used in the default title if provided.
    time_column : str
        Column to plot. One of 'cycle_time', 'layup_time',
        'close_time', 'resin_time'.
    group_by : str, optional
        If provided, splits the boxplot by this column (e.g. 'mold_name'
        to compare the operator's performance across molds).
    title : str, optional
        Custom plot title. If None, a default is generated.
    figsize : tuple

    Returns
    -------
    matplotlib.figure.Figure
    """
    df = df.dropna(subset=[time_column]).copy()

    if df.empty:
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, "No data available",
                ha="center", va="center", transform=ax.transAxes)
        return fig

    name = df["name"].iloc[0] if "name" in df.columns else f"Employee {employee_number}"
    label_map = {
        "cycle_time": "Cycle Time (min)",
        "layup_time": "Layup Time (min)",
        "close_time": "Close Time (min)",
        "resin_time": "Resin Time (min)",
    }
    y_label = label_map.get(time_column, time_column)

    if title is None:
        if group_by == "mold_name":
            title = f"{name} — {y_label} by Mold"
        else:
            title = f"{name} — {y_label}"

    fig, ax = plt.subplots(figsize=figsize)
    sns.set_theme(style="whitegrid")

    flierprops = dict(marker="o", markerfacecolor="none", markersize=4,
                      linestyle="none")

    if group_by and group_by in df.columns:
        order = sorted(df[group_by].unique())
        sns.boxplot(
            data=df, x=group_by, y=time_column,
            order=order, flierprops=flierprops,
            color="steelblue", ax=ax
        )
        ax.set_xlabel(group_by.replace("_", " ").title())
    else:
        sns.boxplot(
            data=df, y=time_column,
            flierprops=flierprops,
            color="steelblue", ax=ax
        )
        ax.set_xlabel("")

    ax.set_ylabel(y_label)
    ax.set_title(title)

    # Annotate with n and median
    if group_by and group_by in df.columns:
        for i, grp in enumerate(order):
            subset = df[df[group_by] == grp][time_column].dropna()
            ax.text(i, ax.get_ylim()[0],
                    f"n={len(subset)}\nmed={subset.median():.1f}",
                    ha="center", va="bottom", fontsize=8, color="dimgray")
    else:
        ct = df[time_column].dropna()
        ax.text(0.98, 0.98,
                f"n={len(ct)}  median={ct.median():.1f}  σ={ct.std():.1f}",
                ha="right", va="top", transform=ax.transAxes,
                fontsize=9, color="dimgray")

    fig.tight_layout()
    return fig


def plot_all_operators_boxplot(
    conn: sqlite3.Connection,
    mold_name: str = None,
    time_column: str = "cycle_time",
    min_cycles: int = 10,
    exclude_flagged: bool = True,
    figsize: tuple = (12, 6),
) -> plt.Figure:
    """
    Generate a comparison boxplot of all operators side by side,
    ordered by median cycle time.

    Parameters
    ----------
    conn : sqlite3.Connection
    mold_name : str, optional
        Filter to a specific mold. If None, uses all molds.
    time_column : str
        Column to plot.
    min_cycles : int
        Minimum number of cycles an operator must have to be included.
        Operators with fewer cycles are excluded to avoid misleading stats.
    exclude_flagged : bool
    figsize : tuple

    Returns
    -------
    matplotlib.figure.Figure
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT DISTINCT employee_number FROM operators ORDER BY employee_number"
    )
    emp_numbers = [row[0] for row in cursor.fetchall()]

    frames = []
    for emp_num in emp_numbers:
        df = get_operator_cycle_times(
            conn, emp_num,
            mold_name=mold_name,
            full_cycle_only=True,
            exclude_flagged=exclude_flagged,
        )
        if len(df) >= min_cycles:
            frames.append(df)

    if not frames:
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, "No data available",
                ha="center", va="center", transform=ax.transAxes)
        return fig

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.dropna(subset=[time_column])

    # Order operators by median cycle time
    order = (combined.groupby("name")[time_column]
             .median()
             .sort_values()
             .index.tolist())

    label_map = {
        "cycle_time": "Cycle Time (min)",
        "layup_time": "Layup Time (min)",
        "close_time": "Close Time (min)",
        "resin_time": "Resin Time (min)",
    }
    y_label = label_map.get(time_column, time_column)
    title = f"All Operators — {y_label}"
    if mold_name:
        title += f" ({mold_name} mold)"

    fig, ax = plt.subplots(figsize=figsize)
    sns.set_theme(style="whitegrid")
    flierprops = dict(marker="o", markerfacecolor="none", markersize=4,
                      linestyle="none")

    sns.boxplot(
        data=combined, x="name", y=time_column,
        order=order, flierprops=flierprops,
        color="steelblue", ax=ax
    )

    for i, name in enumerate(order):
        subset = combined[combined["name"] == name][time_column].dropna()
        ax.text(i, ax.get_ylim()[0],
                f"n={len(subset)}",
                ha="center", va="bottom", fontsize=8, color="dimgray")

    ax.set_xlabel("Operator")
    ax.set_ylabel(y_label)
    ax.set_title(title)
    plt.xticks(rotation=30, ha="right")
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Quick demo -- run directly to verify the database connection works
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    conn = get_connection()

    print("Operators in database:")
    ops = pd.read_sql("SELECT * FROM operators ORDER BY employee_number", conn)
    print(ops.to_string())
    print()

    # Stats for each operator
    stats_df = get_all_operators_stats(conn)
    if not stats_df.empty:
        print("Operator cycle time summary:")
        print(stats_df.to_string())
        print()

        # Plot the operator with the most cycles as a demo
        top = stats_df.loc[stats_df["n_cycles"].idxmax()]
        emp_num = int(top["employee_number"])
        print(f"Generating boxplot for employee {emp_num} ({top['name']})...")

        df = get_operator_cycle_times(conn, emp_num)
        fig = plot_operator_boxplot(df, employee_number=emp_num)
        fig.savefig("demo_operator_boxplot.png", dpi=200)
        print("Saved: demo_operator_boxplot.png")
    else:
        print("No operator data found. Make sure clean_mold_data.py has run.")

    conn.close()
