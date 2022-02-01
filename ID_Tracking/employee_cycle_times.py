"""employee_cycle_times.py: Code for taking in a CSV downloaded from StrideLinx
and outputting all the cycle times for each employee, as well as averages
and other useful metrics.

Date created: 1/26/2022
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

def get_closest_operator(cycle_idx, operator_inds):
    """
    Take an index of the cycle time and an array of indices for a given
    operator. Determine the index of the closest previous operator value to the
    chosen cycle index. If there is no previous operator value to the chosen
    cycle index, copy the closest operator value.

    Parameters
    ----------
    cycle_idx : integer
        DESCRIPTION.
    operator_inds : array
        DESCRIPTION.

    Returns
    -------
    operator_idx : integer of the index closest and previous to the chosen
        cycle time index.

    """

    # Get array with all differences between cycle_idx and operator_inds
    diff_arr = cycle_idx - operator_inds

    posdiffs = [x for x in diff_arr if x > 0] or None
    if posdiffs is None:
        operator_idx = min(operator_inds)
    else:
        mindiff = min(posdiffs)
        # print("Cycle index: {}\tLead is {} away".format(cycle_idx, mindiff))
        operator_idx = cycle_idx - mindiff

    return operator_idx


def clean_single_mold_data(single_mold_data):
    """
    Take in StrideLinx data download for a given period, and produce a dataframe
    of times and associated cycle times and operators.
    """
    # Load the data from .csv (make this general after testing is complete)
    df_raw = pd.read_csv(single_mold_data, parse_dates=["time"])

    # Drop the columns not relevant to cycle times
    df_raw = df_raw.drop(["Leak Time", "Leak Count", "Parts Count",
                        "Weekly Count", "Monthly Count", "Trash Count"], axis=1)

    # Sort by ascending time
    df_sorted = df_raw.sort_values(list(df_raw.columns), ascending=True)
    df_sorted = df_sorted.reset_index(drop=True)

    # Get rid of any rows with nan in all columns but time
    nan_indices = []
    for i in range(len(df_sorted)):
        if np.isnan(df_sorted["Layup Time"].iloc[i]):
            if np.isnan(df_sorted["Close Time"].iloc[i]):
                if np.isnan(df_sorted["Resin Time"].iloc[i]):
                    if np.isnan(df_sorted["Cycle Time"].iloc[i]):
                        if np.isnan(df_sorted["Lead"].iloc[i]):
                            if np.isnan(df_sorted["Assistant 1"].iloc[i]):
                                if np.isnan(df_sorted["Assistant 2"].iloc[i]):
                                    if np.isnan(df_sorted["Assistant 3"].iloc[i]):
                                        nan_indices.append(i)

    df_cleaned = df_sorted.drop(df_sorted.index[nan_indices])
    df_cleaned = df_cleaned.reset_index(drop=True)

    ### Collapse the rows together so corresponding cycle times are on the same row
    # Find the indices where there is a cycle time.
    cycle_inds = []
    not_nan_series = df_cleaned["Cycle Time"].notnull()
    for i in range(len(not_nan_series)):
        if not_nan_series.iloc[i] == True:
            cycle_inds.append(i)

    # Find the indices where there is a resin time
    resin_inds = []
    not_nan_series = df_cleaned["Resin Time"].notnull()
    for i in range(len(not_nan_series)):
        if not_nan_series.iloc[i] == True:
            resin_inds.append(i)

    # Find the indices where there is a close time
    close_inds = []
    not_nan_series = df_cleaned["Close Time"].notnull()
    for i in range(len(not_nan_series)):
        if not_nan_series.iloc[i] == True:
            close_inds.append(i)

    # Find the indices where there is a layup time
    layup_inds = []
    not_nan_series = df_cleaned["Layup Time"].notnull()
    for i in range(len(not_nan_series)):
        if not_nan_series.iloc[i] == True:
            layup_inds.append(i)

    # Find the indices where there is a lead number
    lead_inds = []
    not_nan_series = df_cleaned["Lead"].notnull()
    for i in range(len(not_nan_series)):
        if not_nan_series.iloc[i] == True:
            lead_inds.append(i)
    lead_inds = np.array(lead_inds)

    # Find the indices where there is an assistant 1 number
    assistant1_inds = []
    not_nan_series = df_cleaned["Assistant 1"].notnull()
    for i in range(len(not_nan_series)):
        if not_nan_series.iloc[i] == True:
            assistant1_inds.append(i)
    assistant1_inds = np.array(assistant1_inds)

    # Find the indices where there is an assistant 2 number
    assistant2_inds = []
    not_nan_series = df_cleaned["Assistant 2"].notnull()
    for i in range(len(not_nan_series)):
        if not_nan_series.iloc[i] == True:
            assistant2_inds.append(i)
    assistant2_inds = np.array(assistant2_inds)

    # Find the indices where there is an assistant 3 number
    assistant3_inds = []
    not_nan_series = df_cleaned["Assistant 3"].notnull()
    for i in range(len(not_nan_series)):
        if not_nan_series.iloc[i] == True:
            assistant3_inds.append(i)
    assistant3_inds = np.array(assistant3_inds)

    # Grab each datetime that corresponds to a logged cycle time
    datetimes = []
    for i, cycle_ind in enumerate(cycle_inds):
        datetimes.append(df_cleaned["time"].iloc[cycle_ind])

    # Grab each cycle time
    cycle_times = []
    for i, cycle_ind in enumerate(cycle_inds):
        cycle_times.append(df_cleaned["Cycle Time"].iloc[cycle_ind])


    # Grab each resin time
    resin_times = []
    for i, resin_ind in enumerate(resin_inds):
        resin_times.append(df_cleaned["Resin Time"].iloc[resin_ind])

    # Grab each close time
    close_times = []
    for i, close_ind in enumerate(close_inds):
        close_times.append(df_cleaned["Close Time"].iloc[close_ind])

    # Grab each layup time
    layup_times = []
    for i, layup_ind in enumerate(layup_inds):
        layup_times.append(df_cleaned["Layup Time"].iloc[layup_ind])

    # Check lengths of the various time vectors
    ncycle = len(cycle_times)
    nresin = len(resin_times)
    nclose = len(close_times)
    nlayup = len(layup_times)

    # Add a nan to the beginning or end of each list, depending on if the number
    # of logged times matches the count of cycle times. Determine the position of
    # the nan value by looking at the relative position of the times in df_cleaned.
    # Resin times:
    if cycle_inds[0] < resin_inds[0]:
        cycle_times.insert(0, np.nan)
    if cycle_inds[-1] < resin_inds[-1]:
        cycle_times.append(np.nan)
    ncycle = len(cycle_times)
    nresin = len(resin_times)
    if nresin != ncycle:
        raise Exception("Resin and cycle time vectors aren't matching lengths")

    # Close times:
    if cycle_inds[0] < close_inds[0]:
        if close_times[0] != np.nan:
            close_times.insert(0, np.nan)
    if cycle_inds[-1] < close_inds[-1]:
        if close_times[-1] != np.nan:
            close_times.append(np.nan)
    ncycle = len(cycle_times)
    nresin = len(resin_times)
    nclose = len(close_times)
    if nclose != nresin:
        raise Exception("Close time vector isn't matching resin time vector")
    if nclose != ncycle:
        raise Exception("Close time vector isn't matching cycle time vector")

    # Layup times:
    if cycle_inds[0] < layup_inds[0]:
        if layup_times[0] != np.nan:
            layup_times.insert(0, np.nan)
    if cycle_inds[-1] < layup_inds[-1]:
        if layup_times[-1] != np.nan:
            layup_times.append(np.nan)
    ncycle = len(cycle_times)
    nresin = len(resin_times)
    nlayup = len(layup_times)
    if nlayup != nclose:
        raise Exception("Layup time vector isn't matching close time vector")
    if nlayup != nresin:
        raise Exception("Layup time vector isn't matching resin time vector")
    if nlayup != ncycle:
        raise Exception("Layup time vector isn't matching cycle time vector")

    # For each cycle time, determine the lead and assistant numbers
    leads = []
    assistant1s = []
    assistant2s = []
    assistant3s = []
    for i, cycle_ind in enumerate(cycle_inds):
        # Determine the closest previous index in the Lead column that contains a
        # lead number
        lead_idx = get_closest_operator(cycle_ind, lead_inds)
        leads.append(df_cleaned["Lead"].iloc[lead_idx])
        assistant1_idx = get_closest_operator(cycle_ind, assistant1_inds)
        assistant1s.append(df_cleaned["Assistant 1"].iloc[assistant1_idx])
        assistant2_idx = get_closest_operator(cycle_ind, assistant2_inds)
        assistant2s.append(df_cleaned["Assistant 2"].iloc[assistant2_idx])
        assistant3_idx = get_closest_operator(cycle_ind, assistant3_inds)
        assistant3s.append(df_cleaned["Assistant 3"].iloc[assistant3_idx])

    # Combine data
    collapse_data = {"time": datetimes, "Layup Time": layup_times,
                     "Close Time": close_times, "Resin Time": resin_times,
                     "Cycle Time": cycle_times, "Lead": leads,
                     "Assistant 1": assistant1s, "Assistant 2": assistant2s,
                     "Assistant 3": assistant3s}
    df_collapse = pd.DataFrame.from_dict(collapse_data)
    # df_collapse["time"] = pd.to_datetime(df_collapse["time"])

    return df_collapse


def get_operator_stats_single_mold(df_collapse):
    startdate = df_collapse["time"].iloc[0].date()
    enddate = df_collapse["time"].iloc[-1].date()

    ### Get statistics on each operator in the data ###
    # Get lists of unique operator numbers for each category
    unique_leads = [int(x) for x in df_collapse["Lead"].unique()]
    if 0 in unique_leads:
        unique_leads.remove(0)
    unique_assistant1 = [int(x) for x in df_collapse["Assistant 1"].unique()]
    unique_assistant2 = [int(x) for x in df_collapse["Assistant 2"].unique()]
    unique_assistant3 = [int(x) for x in df_collapse["Assistant 3"].unique()]
    unique_assistants = unique_assistant1 + unique_assistant2 + unique_assistant3
    unique_assistants = list(np.unique(unique_assistants))
    if 0 in unique_assistants:
        unique_assistants.remove(0)


    operator_strings = []
    for operator in unique_leads:
        operator_strings.append("Lead {}".format(operator))
    for operator in unique_assistants:
        operator_strings.append("Assistant {}".format(operator))

    all_cycle_times = pd.DataFrame()

    # Go through each unique operator number and gather their data
    unique_operators = unique_leads + unique_assistants
    unique_operators = list(np.unique(unique_operators))
    
    for operator in unique_operators:
        df_operator = df_collapse.loc[(df_collapse["Lead"] == operator) |
                                      (df_collapse["Assistant 1"] == operator) |
                                      (df_collapse["Assistant 2"] == operator) |
                                      (df_collapse["Assistant 3"] == operator)]
        
        df_lead = df_collapse.loc[df_collapse["Lead"] == operator]
        df_assistant = df_collapse.loc[(df_collapse["Assistant 1"] == operator) |
                                       (df_collapse["Assistant 2"] == operator) |
                                       (df_collapse["Assistant 3"] == operator)]
        
        # Append the cycle time data as a column to all_cycle_times
        lead_col = "Lead {}".format(operator)
        assistant_col = "Assistant {}".format(operator)
        operator_col = "All Operator {}".format(operator)
        all_cycle_times = pd.concat([all_cycle_times, df_lead["Cycle Time"].rename(lead_col)], axis=1)
        all_cycle_times = pd.concat([all_cycle_times, df_assistant["Cycle Time"].rename(assistant_col)], axis=1)
        
        # Compare the current operator against all cycle times
        operator_compare = pd.DataFrame()
        operator_compare = pd.concat([operator_compare, df_lead["Cycle Time"].rename(lead_col)], axis=1)
        operator_compare = pd.concat([operator_compare, df_assistant["Cycle Time"].rename(assistant_col)], axis=1)
        operator_compare = pd.concat([operator_compare, df_operator["Cycle Time"].rename(operator_col)], axis=1)
        operator_compare = pd.concat([operator_compare, df_collapse["Cycle Time"].rename("All Cycle Times")], axis=1)
        
        operator_compare.boxplot(column = list(operator_compare.columns), rot=45)
        plt.title("Operator {} Cycle Times: {} to {}".format(operator, startdate, enddate))
        plt.ylabel("Cycle Time (minutes)")
        plt.show()

    all_cycle_times.boxplot(column = list(all_cycle_times.columns), rot=45)
    plt.title("All operator cycle times: {} to {}".format(startdate, enddate))


def analyze_single_mold(single_mold_data):
    df = clean_single_mold_data(single_mold_data)
    get_operator_stats_single_mold(df)


def analyze_all_molds(mold_data_folder):
    """
    Take a list of CSV files containing mold data downloaded from StrideLinx.
    Combine the data into one large dataframe of cycle times and their
    associated operators, and get individual operator stats. Print a nice report
    for each individual operator number that includes their lead, assistant,
    and overall stats compared to all cycle times for the same period.
    """
    mold_data_files = []
    for root, dirs, files in os.walk(os.path.abspath(mold_data_folder)):
        for file in files:
            mold_data_files.append(os.path.join(root, file))
    
    frames = []
    for datafile in mold_data_files:
        frames.append(clean_single_mold_data(datafile))

    allmolds = pd.concat(frames)
    allmolds = allmolds.reset_index(drop=True)

    get_operator_stats_single_mold(allmolds)


if __name__ == "__main__":
    datafolder = os.getcwd()
    datafolder = datafolder + "\\testdata"
    analyze_all_molds(datafolder)