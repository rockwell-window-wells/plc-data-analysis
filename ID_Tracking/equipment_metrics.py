# -*- coding: utf-8 -*-
"""
Created on Mon Feb 14 15:31:56 2022

@author: Ryan.Larson

equipment_metrics.py: Code for taking in a CSV downloaded from StrideLinx
and outputting all the cycle times, resin times, and other relevant metrics
for equipment (right now this only includes bags).

Date created: 2/14/2022
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import seaborn as sns

def get_closest_ID(cycle_idx, bag_inds):
    """
    Take an index of the cycle time and an array of indices for a given
    operator. Determine the index of the closest previous operator value to the
    chosen cycle index. If there is no previous operator value to the chosen
    cycle index, copy the closest operator value.

    Parameters
    ----------
    cycle_idx : integer
        DESCRIPTION.
    operator_inds : numpy array
        DESCRIPTION.

    Returns
    -------
    operator_idx : integer of the index closest and previous to the chosen
        cycle time index.

    """

    # Get array with all differences between cycle_idx and operator_inds
    diff_arr = cycle_idx - bag_inds

    posdiffs = [x for x in diff_arr if x > 0] or None
    if posdiffs is None:
        bag_idx = min(bag_inds)
    else:
        mindiff = min(posdiffs)
        # print("Cycle index: {}\tLead is {} away".format(cycle_idx, mindiff))
        bag_idx = cycle_idx - mindiff

    return bag_idx


def align_inds_times(input_inds, input_times, ref_inds, longest_inds, longest_len):
    while len(input_inds) < longest_len:
        for i in range(len(input_inds)):
            diff = ref_inds[i] - input_inds[i]
            if diff < 0:
                input_inds.insert(i, i)
                input_times.insert(i, np.nan)
                break
        if len(input_inds) < longest_len:
            input_inds.append(longest_inds[len(input_inds)])
            input_times.append(np.nan)


def align_cycles_inds_times(input_inds, input_times, ref_inds, longest_inds, longest_len, datetimes):
    while len(input_inds) < longest_len:
        for i in range(len(input_inds)):
            diff = input_inds[i] - ref_inds[i]
            if diff < 0:
                input_inds.insert(i, i)
                input_times.insert(i, np.nan)
                datetimes.insert(i, datetimes[i])
                break
        if len(input_inds) < longest_len:
            input_inds.append(longest_inds[len(input_inds)])
            input_times.append(np.nan)
            datetimes.append(datetimes[-1])


def clean_single_mold_data(single_mold_data):
    """
    Take in StrideLinx data download for a given period, and produce a dataframe
    of times and associated cycle times and operators.
    """
    # Load the data from .csv (make this general after testing is complete)
    df_raw = pd.read_csv(single_mold_data, parse_dates=["time"])

    # Drop the columns not relevant to cycle times
    df_raw = df_raw.drop(["Parts Count", "Weekly Count", "Monthly Count",
                          "Trash Count", "Lead", "Assistant 1", "Assistant 2",
                          "Assistant 3"], axis=1)

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
                        if np.isnan(df_sorted["Leak Time"].iloc[i]):
                            if np.isnan(df_sorted["Leak Count"].iloc[i]):
                                if np.isnan(df_sorted["Bag"].iloc[i]):
                                    if np.isnan(df_sorted["Bag Days"].iloc[i]):
                                        if np.isnan(df_sorted["Bag Cycles"].iloc[i]):
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

    # Find the indices where there is a leak time
    leaktime_inds = []
    not_nan_series = df_cleaned["Leak Time"].notnull()
    for i in range(len(not_nan_series)):
        if not_nan_series.iloc[i] == True:
            leaktime_inds.append(i)
    leaktime_inds = np.array(leaktime_inds)

    # Find the indices where there is a leak count number
    leak_inds = []
    not_nan_series = df_cleaned["Leak Count"].notnull()
    for i in range(len(not_nan_series)):
        if not_nan_series.iloc[i] == True:
            leak_inds.append(i)
    leak_inds = np.array(leak_inds)

    # Find the indices where there is an assistant 1 number
    bagid_inds = []
    not_nan_series = df_cleaned["Bag"].notnull()
    for i in range(len(not_nan_series)):
        if not_nan_series.iloc[i] == True:
            bagid_inds.append(i)
    bagid_inds = np.array(bagid_inds)

    # Find the indices where there is an assistant 2 number
    bagday_inds = []
    not_nan_series = df_cleaned["Bag Days"].notnull()
    for i in range(len(not_nan_series)):
        if not_nan_series.iloc[i] == True:
            bagday_inds.append(i)
    bagday_inds = np.array(bagday_inds)

    # Find the indices where there is an assistant 3 number
    bagcount_inds = []
    not_nan_series = df_cleaned["Bag Cycles"].notnull()
    for i in range(len(not_nan_series)):
        if not_nan_series.iloc[i] == True:
            bagcount_inds.append(i)
    bagcount_inds = np.array(bagcount_inds)

    # Grab each datetime that corresponds to a logged cycle time
    cycle_datetimes = []
    for i, cycle_ind in enumerate(cycle_inds):
        cycle_datetimes.append(df_cleaned["time"].iloc[cycle_ind])
        
    # Grab each datetime that corresponds to a logged resin time
    resin_datetimes = []
    for i, resin_ind in enumerate(resin_inds):
        resin_datetimes.append(df_cleaned["time"].iloc[resin_ind])
        
    # Grab each datetime that corresponds to a logged close time
    close_datetimes = []
    for i, close_ind in enumerate(close_inds):
        close_datetimes.append(df_cleaned["time"].iloc[close_ind])
        
    # Grab each datetime that corresponds to a logged layup time
    layup_datetimes = []
    for i, layup_ind in enumerate(layup_inds):
        layup_datetimes.append(df_cleaned["time"].iloc[layup_ind])

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

    df_layup = align_bag_times(df_cleaned, layup_datetimes, "Layup Time",
                               layup_inds, layup_times, bagid_inds,
                               bagday_inds, bagcount_inds)
    df_close = align_bag_times(df_cleaned, close_datetimes, "Close Time",
                               close_inds, close_times, bagid_inds,
                               bagday_inds, bagcount_inds)
    df_resin = align_bag_times(df_cleaned, resin_datetimes, "Resin Time",
                               resin_inds, resin_times, bagid_inds,
                               bagday_inds, bagcount_inds)
    df_cycle = align_bag_times(df_cleaned, cycle_datetimes, "Cycle Time",
                               cycle_inds, cycle_times, bagid_inds,
                               bagday_inds, bagcount_inds)

    return df_layup, df_close, df_resin, df_cycle


def align_bag_times(df_cleaned, datetimes, timestring, time_inds, measured_times, bagid_inds, bagday_inds, bagcount_inds):
    # For each cycle time, determine the lead and assistant numbers
    bagids = []
    bagdays = []
    bagcounts = []
    for i, ind in enumerate(time_inds):
        # Determine the closest previous index in the Lead column that contains a
        # lead number
        bagid_idx = get_closest_ID(ind, bagid_inds)
        bagids.append(df_cleaned["Bag"].iloc[bagid_idx])
        bagday_idx = get_closest_ID(ind, bagday_inds)
        bagdays.append(df_cleaned["Bag Days"].iloc[bagday_idx])
        bagcount_idx = get_closest_ID(ind, bagcount_inds)
        bagcounts.append(df_cleaned["Bag Cycles"].iloc[bagcount_idx])
    
    bagids = [int(x) for x in bagids]
    bagdays = [int(x) for x in bagdays]
    bagcounts = [int(x) for x in bagcounts]

    # Check if datetimes is longer than the rest of the data. If so, add NaN to
    # the end of all other vectors
    while len(datetimes) > len(measured_times):
        randint = np.random.randint(1,len(datetimes)-2)
        del datetimes[randint]
    while len(datetimes) < len(measured_times):
        datetimes.insert(-1, datetimes[-1])

    # Combine data
    aligned_data = {"time": datetimes, timestring: measured_times,
                    "Bag": bagids, "Bag Days": bagdays,
                    "Bag Cycles": bagcounts}
    df_aligned = pd.DataFrame.from_dict(aligned_data)

    return df_aligned


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

    layup_frames = []
    close_frames = []
    resin_frames = []
    cycle_frames = []
    for datafile in mold_data_files:
        df_layup, df_close, df_resin, df_cycle = clean_single_mold_data(datafile)
        layup_frames.append(df_layup)
        close_frames.append(df_close)
        resin_frames.append(df_resin)
        cycle_frames.append(df_cycle)

    all_layup = pd.concat(layup_frames)
    all_layup = all_layup.reset_index(drop=True)
    all_close = pd.concat(close_frames)
    all_close = all_close.reset_index(drop=True)
    all_resin = pd.concat(resin_frames)
    all_resin = all_resin.reset_index(drop=True)
    all_cycle = pd.concat(cycle_frames)
    all_cycle = all_cycle.reset_index(drop=True)    
    
    ######## Produce correlation plots here for bag age and cycle time, resin time, etc.
    sns.regplot(x=df_layup["Bag Days"], y=df_layup["Layup Time"])
    plotname = "Layup_Bag_Days_Correlation.png"
    plt.savefig(plotname, dpi=300)
    plt.close()
    sns.regplot(x=df_close["Bag Days"], y=df_close["Close Time"])
    plotname = "Close_Bag_Days_Correlation.png"
    plt.savefig(plotname, dpi=300)
    plt.close()
    sns.regplot(x=df_resin["Bag Days"], y=df_resin["Resin Time"])
    plotname = "Resin_Bag_Days_Correlation.png"
    plt.savefig(plotname, dpi=300)
    plt.close()
    sns.regplot(x=df_cycle["Bag Days"], y=df_cycle["Cycle Time"])
    plotname = "Cycle_Bag_Days_Correlation.png"
    plt.savefig(plotname, dpi=300)
    plt.close()
    
    sns.regplot(x=df_layup["Bag Cycles"], y=df_layup["Layup Time"])
    plotname = "Layup_Bag_Count_Correlation.png"
    plt.savefig(plotname, dpi=300)
    plt.close()
    sns.regplot(x=df_close["Bag Cycles"], y=df_close["Close Time"])
    plotname = "Close_Bag_Count_Correlation.png"
    plt.savefig(plotname, dpi=300)
    plt.close()
    sns.regplot(x=df_resin["Bag Cycles"], y=df_resin["Resin Time"])
    plotname = "Resin_Bag_Count_Correlation.png"
    plt.savefig(plotname, dpi=300)
    plt.close()
    sns.regplot(x=df_cycle["Bag Cycles"], y=df_cycle["Cycle Time"])
    plotname = "Cycle_Bag_Count_Correlation.png"
    plt.savefig(plotname, dpi=300)
    plt.close()
    
    return all_layup, all_close, all_resin, all_cycle
    

if __name__ == "__main__":
    datafolder = os.getcwd()
    datafolder = datafolder + "\\testdata\\"
    datafile = datafolder + "pink-mold_pink-mold-stats_2022-07-16T00-00-00_2022-08-08T23-59-59.csv"
    df_layup, df_close, df_resin, df_cycle = clean_single_mold_data(datafile)
        
    datafolder = os.getcwd()
    datafolder = datafolder + "\\testdata\\"
    all_layup, all_close, all_resin, all_cycle = analyze_all_molds(datafolder)
