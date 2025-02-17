# -*- coding: utf-8 -*-
"""
Created on Thu Jan 23 11:57:42 2025

@author: Ryan.Larson
"""

import numpy as np
import pandas as pd
import os
from itertools import groupby
from bisect import bisect_left
import datetime as dt
import matplotlib.pyplot as plt
import seaborn as sns


def between(l1, low, high):
    """
    Outputs a list of the values from l1 that are between low and high, minimum
    inclusive.

    Parameters
    ----------
    l1 : list
        List of ints or floats for filtering.
    low : int or float
        Lowest acceptable value for filtering l1. Assumed to be less than high.
    high : int or float
        Highest value (non-inclusive) for filtering l1. Assumed to be greater
        than low.

    Returns
    -------
    l2 : list
        Contains the values between low and high that are in l1.

    """
    l2 = [i for i in l1 if i >= low and i < high]
    return l2

def list_vals(df_col, idx_list):
    """
    Takes a Pandas DataFrame column, turns it into a list, and outputs only
    the elements of that list indicated by a list of indices found in idx_list.

    Parameters
    ----------
    df_col : column of a Pandas DataFrame (called as df["col_name"])
        Any column of a Pandas DataFrame. Doesn't assume a type of data.
    idx_list : list of ints


    Returns
    -------
    res_list : list
        List of elements of df_col as chosen by indices in idx_list. Data type
        of elements will be the same as that of df_col.

    """
    col_list = list(df_col)
    res_list = [col_list[i] for i in idx_list]
    return res_list

def closest_by_timestamp(input_idx, input_list, df_cleaned):
    """
    Get the closest index to a given cycle time based on the timestamp.

    Parameters
    ----------
    input_idx : int
        DESCRIPTION.
    input_list : list of ints
        DESCRIPTION.
    df_cleaned : DataFrame
        DESCRIPTION.

    Returns
    -------
    None.

    """
    input_timestamp = df_cleaned["datetime"].iloc[input_idx]
    timestamps = list(df_cleaned["datetime"].iloc[input_list])
    
    if input_timestamp in timestamps:
        closest_index = input_list[timestamps.index(input_timestamp)]
    else:
        pos = bisect_left(timestamps, input_timestamp)
        if pos == 0:
            closest_index = input_list[0]
        elif pos == len(input_list):
            closest_index = input_list[-1]
        else:
            before = input_list[pos - 1]
            after = input_list[pos]
            # if after >= len(timestamps):
            #     breakpoint()
            if timestamps[pos] - input_timestamp < input_timestamp - timestamps[pos-1]:
                closest_index = after
            else:
                closest_index = before
    
    return closest_index

def minutes_diff(datetime_start, datetime_end):
    """
    Convenience function for finding the decimal number of minutes between two
    datetime.datetime objects.

    Parameters
    ----------
    datetime_start : datetime.datetime
        Starting datetime. Assumed to be earlier than datetime_end.
    datetime_end : datetime.datetime
        Ending datetime. Assumed to be after datetime_start.

    Returns
    -------
    minutes : float
        The number of minutes, as a decimal, between datetime_start and
        datetime_end. This will work regardless of how many days are between
        the start and end of the period.

    """
    minutes = (datetime_end - datetime_start).total_seconds() / 60.0
    return minutes

def closest_before(input_idx, input_list):
    """
    Takes a chosen index and compares against a list of indices, input_list.
    Finds the closest previous index value to the chosen input_idx value.

    Parameters
    ----------
    input_idx : int
        The reference index value against which the function will compare.
    input_list : list of ints
        A list of integers that are indices. Assumed to be a list in ascending
        order, with no repeated values. (Ex: [3,6,10,22])

    Returns
    -------
    prev_idx : int
        The value from input_list that is the closest previous value to
        input_idx. If input_idx = 20 and input_list = [3,6,10,22], then
        prev_idx will be 10.

    """
    input_array = np.asarray(input_list)
    prev_array = input_array[input_array <= input_idx]
    if len(prev_array) == 0:
        prev_idx = input_array[0]
    else:
        prev_idx = prev_array.max()
    return prev_idx

def count_stages_for_operator(df_cleaned, ind_sets, leadIDs):
    # Make a list of dictionaries that tell which stages should be counted
    # for a given operator (see line 1301 above for location where this should
    # be used)
    
    stages_counted = []
    count_whole_cycle = []
    for i in range(len(ind_sets)):
        layup_ind = ind_sets[i][0]
        close_ind = ind_sets[i][1]
        resin_ind = ind_sets[i][2]
        cycle_ind = ind_sets[i][3]
           
        cycle_finish = df_cleaned["datetime"].iloc[cycle_ind]
        layup_duration = 60.0 * df_cleaned["Layup Time (min.)"].iloc[layup_ind]
        close_duration = 60.0 * df_cleaned["Close Time (min.)"].iloc[close_ind]
        resin_duration = 60.0 * df_cleaned["Resin Time (min.)"].iloc[resin_ind]
        layup_finish = cycle_finish - dt.timedelta(seconds=resin_duration) - dt.timedelta(seconds=close_duration)
        close_start = layup_finish
        close_finish = cycle_finish - dt.timedelta(seconds=resin_duration)
        resin_start = close_finish
        layup_start = cycle_finish - dt.timedelta(seconds=resin_duration) - dt.timedelta(seconds=close_duration) - dt.timedelta(seconds=layup_duration)
        
        # Find the index with the closest value to layup_start's time
        closest_layup_idx = (np.abs(df_cleaned["datetime"] - layup_start)).idxmin()
        ref_idx = closest_layup_idx
        while ref_idx > -1:
            if np.isnan(df_cleaned["Lead"].iloc[ref_idx]) == False:
                closest_before_operator = ref_idx
                break
            else:
                ref_idx -= 1
        if ref_idx == -1:
            closest_before_operator = closest_layup_idx
        all_IDs = [[int(closest_before_operator), df_cleaned["Lead"].iloc[int(closest_before_operator)]]]
        
        # Find the lead IDs and indices that need to be taken into account when
        # finding who clocked in and out and when
        for j in range(closest_layup_idx, cycle_ind+1):
            if np.isnan(df_cleaned["Lead"].iloc[j]) == False:
                all_IDs.append([j, df_cleaned["Lead"].iloc[j]])

        
        all_IDs_changes_only = []
        for j in range(len(all_IDs)):
            if j == 0:
                all_IDs_changes_only.append(all_IDs[j])
            else:
                if all_IDs[j][1] == all_IDs[j-1][1]:
                    continue
                else:
                    all_IDs_changes_only.append(all_IDs[j])
        
        # Determine which operators were present for which stages
        
        # Special case where operator is clocked in the whole time
        # leads_in_range = [ID[1] for ID in all_IDs]
        stages_on_cycle = []
        if len(all_IDs_changes_only) == 1:
            operator_on_layup = True
            operator_on_close = True
            operator_on_resin = True
            cycles_dict = {"Lead": all_IDs_changes_only[0][1],
                           "Layup": operator_on_layup,
                           "Close": operator_on_close,
                           "Resin": operator_on_resin}
            # stages_counted.append([cycles_dict])
            stages_on_cycle.append(cycles_dict)
            count_whole_cycle.append([True])
            
        
        # if len(list(set(leads_in_range))) == 1:
        #     operator_on_layup = True
        #     operator_on_close = True
        #     operator_on_resin = True
        #     cycles_dict = {"Layup": operator_on_layup,
        #                    "Close": operator_on_close,
        #                    "Resin": operator_on_resin}
        #     stages_counted.append([cycles_dict])
        #     count_whole_cycle.append([True])
        
        # All other cases involving more than one lead operator
        else:
            # stages_on_cycle = []
            for k in range(len(all_IDs_changes_only)):
                op_clock_in = df_cleaned.loc[all_IDs_changes_only[k][0], "datetime"]
                if k == len(all_IDs_changes_only)-1:
                    op_clock_out = df_cleaned.loc[cycle_ind, "datetime"]
                else:
                    op_clock_out = df_cleaned.loc[all_IDs_changes_only[k+1][0], "datetime"]
                    
                if op_clock_in < layup_finish:
                    operator_on_layup = True
                else:
                    operator_on_layup = False
                    
                if op_clock_in < close_finish and op_clock_out > layup_finish:
                    operator_on_close = True
                else:
                    operator_on_close = False
                    
                if op_clock_in < cycle_finish and op_clock_out > close_finish:
                    operator_on_resin = True
                else:
                    operator_on_resin = False
                
                
                cycles_dict = {"Lead": all_IDs_changes_only[k][1],
                               "Layup": operator_on_layup,
                               "Close": operator_on_close,
                               "Resin": operator_on_resin}
                
                stages_on_cycle.append(cycles_dict)
                
            # count_whole_cycle.append([False])
            
        stages_counted.append(stages_on_cycle)
        
        
    # Create columns for IDs that were present during each cycle stage
    layupIDs = [[] for row in stages_counted]
    closeIDs = [[] for row in stages_counted]
    resinIDs = [[] for row in stages_counted]
    
    for i,row in enumerate(stages_counted):
        # List operators who helped with layup
        for stage_dict in row:
            if stage_dict["Layup"] == True:
                layupIDs[i].append(stage_dict["Lead"])
            if stage_dict["Close"] == True:
                closeIDs[i].append(stage_dict["Lead"])
            if stage_dict["Resin"] == True:
                resinIDs[i].append(stage_dict["Lead"])
                
        layupIDs[i] = list(np.unique(layupIDs[i]))
        closeIDs[i] = list(np.unique(closeIDs[i]))
        resinIDs[i] = list(np.unique(resinIDs[i]))
    
    cycleIDs = [[] for row in stages_counted]
    for i,row in enumerate(stages_counted):
        for stage_dict in row:
            leadnum = stage_dict["Lead"]
            if leadnum in layupIDs[i] and leadnum in closeIDs[i] and leadnum in resinIDs[i]:
                cycleIDs[i].append(leadnum)
        
        # Some cases can arise where neither the 0 or a real lead ID was
        # present during the whole cycle. In this case, len(cycleIDs[i]) == 0
        if len(cycleIDs[i]) == 0:
            cycleIDs[i] = 0.0
                
        cycleIDs[i] = list(np.unique(cycleIDs[i]))        
        
    return layupIDs, closeIDs, resinIDs, cycleIDs

def associate_cycle_stages(df_cleaned):
    # Get a list of lists of indices for which stage times are closest to a
    # given cycle time
    # Find the indices where there is a layup time.
    layup_inds = []
    not_nan_series = df_cleaned["Layup Time (min.)"].notnull()
    for i in range(len(not_nan_series)):
        if not_nan_series.iloc[i] == True:
            layup_inds.append(i)
    # Get rid of indices that point to a zero layup time
    layup_inds_cleaned = []
    for ind in layup_inds:
        if df_cleaned["Layup Time (min.)"].iloc[ind] != 0:
            layup_inds_cleaned.append(ind)
    layup_inds = layup_inds_cleaned.copy()
    layup_inds = [i[0] for i in groupby(layup_inds)]
    
    # Find the indices where there is a close time.
    close_inds = []
    not_nan_series = df_cleaned["Close Time (min.)"].notnull()
    for i in range(len(not_nan_series)):
        if not_nan_series.iloc[i] == True:
            close_inds.append(i)
    # Get rid of indices that point to a zero close time
    close_inds_cleaned = []
    for ind in close_inds:
        if df_cleaned["Close Time (min.)"].iloc[ind] != 0:
            close_inds_cleaned.append(ind)
    close_inds = close_inds_cleaned.copy()
    close_inds = [i[0] for i in groupby(close_inds)]
    
    # Find the indices where there is a resin time.
    resin_inds = []
    not_nan_series = df_cleaned["Resin Time (min.)"].notnull()
    for i in range(len(not_nan_series)):
        if not_nan_series.iloc[i] == True:
            resin_inds.append(i)
    # Get rid of indices that point to a zero resin time
    resin_inds_cleaned = []
    for ind in resin_inds:
        if df_cleaned["Resin Time (min.)"].iloc[ind] != 0:
            resin_inds_cleaned.append(ind)
    resin_inds = resin_inds_cleaned.copy()
    resin_inds = [i[0] for i in groupby(resin_inds)]

    # Find the indices where there is a cycle time.
    cycle_inds = []
    not_nan_series = df_cleaned["Cycle Time (min.)"].notnull()
    for i in range(len(not_nan_series)):
        if not_nan_series.iloc[i] == True:
            cycle_inds.append(i)
    # Get rid of indices that point to a zero cycle time
    cycle_inds_cleaned = []
    for ind in cycle_inds:
        if df_cleaned["Cycle Time (min.)"].iloc[ind] != 0:
            cycle_inds_cleaned.append(ind)
    cycle_inds = cycle_inds_cleaned.copy()
    cycle_inds = [i[0] for i in groupby(cycle_inds)]
    
    ind_sets = []
    layup_filtered = []
    close_filtered = []
    resin_filtered = []
    for ind in cycle_inds:
        # closest_layup = closest_before(ind, layup_inds)
        # closest_close = closest_before(ind, close_inds)
        # closest_resin = closest_before(ind, resin_inds)
        
        ##################################################################################################################
        # Catch cases where the closest index before gives the wrong supporting
        # data
        # A better strategy might be looking at the timestamp for the cycle time
        # and choosing the closest time to that timestamp. Cycles have to differ
        # by a good deal of time so this would probably be reliable.
        ##################################################################################################################
        
        closest_layup = closest_by_timestamp(ind, layup_inds, df_cleaned)
        closest_close = closest_by_timestamp(ind, close_inds, df_cleaned)
        closest_resin = closest_by_timestamp(ind, resin_inds, df_cleaned)
        
        layup_filtered.append(closest_layup)
        close_filtered.append(closest_close)
        resin_filtered.append(closest_resin)
        ind_sets.append([closest_layup, closest_close, closest_resin, ind])
        
    layup_inds = layup_filtered.copy()
    close_inds = close_filtered.copy()
    resin_inds = resin_filtered.copy()
        
    return ind_sets, layup_inds, close_inds, resin_inds, cycle_inds

def prepare_mold_data(mold_data_folder):
    moldfiles = [os.path.join(mold_data_folder, f) for f in os.listdir(mold_data_folder) if os.path.isfile(os.path.join(mold_data_folder, f))]
    
    moldcolors = {'brown-mold': 'Brown',
                  'purple-mold': 'Purple',
                  'red-mold': 'Red',
                  'pink-mold': 'Pink',
                  'orange-mold': 'Orange',
                  'green-mold': 'Green'}
    
    df_eval = pd.DataFrame()
    
    for moldfile in moldfiles:
        df_raw = pd.read_csv(moldfile)
        
        color = None
        for key in moldcolors:
            if key in moldfile:
                color = moldcolors[key]
                break
        if color is None:
            raise ValueError('No mold color detected')
        else:
            print(f'Processing {color} mold data')
        
        # Read in the time column as a datetime
        df_raw['datetime'] = pd.to_datetime(df_raw['time'], format='%Y-%m-%d %H:%M:%S.%f')
        
        # Clean the data here before sending to a list of dataframes
        # Sort by ascending time
        df_sorted = df_raw.sort_values(list(df_raw.columns), ascending=True)
        df_sorted = df_sorted.reset_index(drop=True)

        # Get rid of any rows with nan in all columns but time
        nan_indices = []
        for i in range(len(df_sorted)):
            if np.isnan(df_sorted["Layup Time (min.)"].iloc[i]):
                if np.isnan(df_sorted["Close Time (min.)"].iloc[i]):
                    if np.isnan(df_sorted["Resin Time (min.)"].iloc[i]):
                        if np.isnan(df_sorted["Cycle Time (min.)"].iloc[i]):
                            if np.isnan(df_sorted["Lead"].iloc[i]):
                                if np.isnan(df_sorted["Assistant 1"].iloc[i]):
                                    if np.isnan(df_sorted["Assistant 2"].iloc[i]):
                                        if np.isnan(df_sorted["Assistant 3"].iloc[i]):
                                            nan_indices.append(i)

        df_cleaned = df_sorted.drop(df_sorted.index[nan_indices])
        df_cleaned = df_cleaned.reset_index(drop=True)

        # Make a new dataframe with only time, Cycle Time, LeadIDs,
        # AssistantIDs, LeadTimes, AssistantTimes columns. LeadTimes and
        # AssistantTimes columns are the individual elapsed times for each
        # operator on the mold. LeadIDs and AssistantIDs columns use a list
        # of the operator numbers instead of single values.
        
        stage_inds, layup_inds, close_inds, resin_inds, cycle_inds = associate_cycle_stages(df_cleaned)

        # Find the indices where there is a lead login
        lead_inds = []
        not_nan_series = df_cleaned["Lead"].notnull()
        for i in range(len(not_nan_series)):
            if not_nan_series.iloc[i] == True:
                lead_inds.append(i)
        
        # Find the indices where there is a bag number
        bag_inds = []
        not_nan_series = df_cleaned["Bag"].notnull()
        for i in range(len(not_nan_series)):
            if not_nan_series.iloc[i] == True:
                bag_inds.append(i)
        
        # Find the indices where there is a bag days logged
        bag_days_inds = []
        not_nan_series = df_cleaned["Bag Days (Days)"].notnull()
        for i in range(len(not_nan_series)):
            if not_nan_series.iloc[i] == True:
                bag_days_inds.append(i)
        
        # Find the indices where there is a bag cycles logged
        bag_cycles_inds = []
        not_nan_series = df_cleaned["Bag Cycles"].notnull()
        for i in range(len(not_nan_series)):
            if not_nan_series.iloc[i] == True:
                bag_cycles_inds.append(i)
        

        # # Find the indices where there is an assistant 1 login
        # assist1_inds = []
        # not_nan_series = df_cleaned["Assistant 1"].notnull()
        # for i in range(len(not_nan_series)):
        #     if not_nan_series.iloc[i] == True:
        #         assist1_inds.append(i)

        # # Find the indices where there is an assistant 2 login
        # assist2_inds = []
        # not_nan_series = df_cleaned["Assistant 2"].notnull()
        # for i in range(len(not_nan_series)):
        #     if not_nan_series.iloc[i] == True:
        #         assist2_inds.append(i)

        # # Find the indices where there is an assistant 1 login
        # assist3_inds = []
        # not_nan_series = df_cleaned["Assistant 3"].notnull()
        # for i in range(len(not_nan_series)):
        #     if not_nan_series.iloc[i] == True:
        #         assist3_inds.append(i)

        leadIDs = [[] for ind in cycle_inds]
        bagIDs = [[] for ind in cycle_inds]
        bagdays = [[] for ind in cycle_inds]
        bagcycles = [[] for ind in cycle_inds]
        
        # man_minutes = [[] for ind in cycle_inds]

        for i, cyc_ind in enumerate(cycle_inds):
            #### Get the lists of IDs associated with each cycle time ####

            # If no one clocked in exactly at the same time as the cycle time
            # was logged, get the closest previous ID number for each role and
            # add the ID number to the appropriate list.
            if i == 0:
                low = 0
                high = cyc_ind

                lead_between = between(lead_inds, low, high)
                leadIDs[i].extend(list_vals(df_cleaned["Lead"], lead_between))
                bag_between = between(bag_inds, low, high)
                bagdays_between = between(bag_days_inds, low, high)
                bagcycles_between = between(bag_cycles_inds, low, high)
                # assist1_between = between(assist1_inds, low, high)
                # assist2_between = between(assist2_inds, low, high)
                # assist3_between = between(assist3_inds, low, high)

                for j,idx in enumerate(lead_between):
                    curr_id = df_cleaned["Lead"][idx]
                    if j == 0:
                        if curr_id == 0:
                            continue
                        datetime_start = df_cleaned["datetime"][0]
                    else:
                        prev_id = df_cleaned["Lead"][lead_between[j-1]]
                        if prev_id == 0:
                            continue
                        datetime_start = df_cleaned["datetime"][lead_between[j-1]]
                    datetime_end = df_cleaned["datetime"][idx]
                    # minutes = minutes_diff(datetime_start, datetime_end)
                    # man_minutes[i].append(minutes)

                    # If at the end of the list, get the time between the last
                    # login (if the ID isn't zero) and the logged cycle time
                    if j == len(lead_between)-1:
                        if df_cleaned["Lead"][idx] != 0:
                            datetime_start = df_cleaned["datetime"][lead_between[j-1]]
                            datetime_end = df_cleaned["datetime"][cyc_ind]
                            # minutes = minutes_diff(datetime_start, datetime_end)
                            # man_minutes[i].append(minutes)

                for j,idx in enumerate(bag_between):
                    curr_id = df_cleaned["Bag"][idx]
                    if j == 0:
                        if curr_id == 0:
                            continue
                        datetime_start = df_cleaned["datetime"][0]
                    else:
                        prev_id = df_cleaned["Bag"][bag_between[j-1]]
                        if prev_id == 0:
                            continue
                        datetime_start = df_cleaned["datetime"][bag_between[j-1]]
                    datetime_end = df_cleaned["datetime"][idx]
                    # minutes = minutes_diff(datetime_start, datetime_end)
                    # man_minutes[i].append(minutes)

                    # If at the end of the list, get the time between the last
                    # login (if the ID isn't zero) and the logged cycle time
                    if j == len(lead_between)-1:
                        if df_cleaned["Bag"][idx] != 0:
                            datetime_start = df_cleaned["datetime"][bag_between[j-1]]
                            datetime_end = df_cleaned["datetime"][cyc_ind]
                            # minutes = minutes_diff(datetime_start, datetime_end)

                for j,idx in enumerate(bagcycles_between):
                    curr_id = df_cleaned["Bag Cycles"][idx]
                    if j == 0:
                        if curr_id == 0:
                            continue
                        datetime_start = df_cleaned["datetime"][0]
                    else:
                        prev_id = df_cleaned["Bag Cycles"][bagcycles_between[j-1]]
                        if prev_id == 0:
                            continue
                        datetime_start = df_cleaned["datetime"][bagcycles_between[j-1]]
                    datetime_end = df_cleaned["datetime"][idx]
                    # minutes = minutes_diff(datetime_start, datetime_end)
                    # man_minutes[i].append(minutes)

                    # If at the end of the list, get the time between the last
                    # login (if the ID isn't zero) and the logged cycle time
                    if j == len(lead_between)-1:
                        if df_cleaned["Bag Cycles"][idx] != 0:
                            datetime_start = df_cleaned["datetime"][bagcycles_between[j-1]]
                            datetime_end = df_cleaned["datetime"][cyc_ind]
                            # minutes = minutes_diff(datetime_start, datetime_end)

                for j,idx in enumerate(bagdays_between):
                    curr_id = df_cleaned["Bag Days (Days)"][idx]
                    if j == 0:
                        if curr_id == 0:
                            continue
                        datetime_start = df_cleaned["datetime"][0]
                    else:
                        prev_id = df_cleaned["Bag Days (Days)"][bagdays_between[j-1]]
                        if prev_id == 0:
                            continue
                        datetime_start = df_cleaned["datetime"][bagdays_between[j-1]]
                    datetime_end = df_cleaned["datetime"][idx]
                    # minutes = minutes_diff(datetime_start, datetime_end)
                    # man_minutes[i].append(minutes)

                    # If at the end of the list, get the time between the last
                    # login (if the ID isn't zero) and the logged cycle time
                    if j == len(lead_between)-1:
                        if df_cleaned["Bag Days (Days)"][idx] != 0:
                            datetime_start = df_cleaned["datetime"][bagdays_between[j-1]]
                            datetime_end = df_cleaned["datetime"][cyc_ind]
                            # minutes = minutes_diff(datetime_start, datetime_end)

                # for j,idx in enumerate(assist1_between):
                #     curr_id = df_cleaned["Assistant 1"][idx]
                #     if j == 0:
                #         if curr_id == 0:
                #             continue
                #         datetime_start = df_cleaned["datetime"][0]
                #     else:
                #         prev_id = df_cleaned["Assistant 1"][assist1_between[j-1]]
                #         if prev_id == 0:
                #             continue
                #         datetime_start = df_cleaned["datetime"][assist1_between[j-1]]
                #     datetime_end = df_cleaned["datetime"][idx]
                #     minutes = minutes_diff(datetime_start, datetime_end)
                #     man_minutes[i].append(minutes)

                #     # If at the end of the list, get the time between the last
                #     # login (if the ID isn't zero) and the logged cycle time
                #     if j == len(assist1_between)-1:
                #         if df_cleaned["Assistant 1"][idx] != 0:
                #             datetime_start = df_cleaned["datetime"][assist1_between[j-1]]
                #             datetime_end = df_cleaned["datetime"][cyc_ind]
                #             minutes = minutes_diff(datetime_start, datetime_end)
                #             man_minutes[i].append(minutes)

                # for j,idx in enumerate(assist2_between):
                #     curr_id = df_cleaned["Assistant 2"][idx]
                #     if j == 0:
                #         if curr_id == 0:
                #             continue
                #         datetime_start = df_cleaned["datetime"][0]
                #     else:
                #         prev_id = df_cleaned["Assistant 2"][assist2_between[j-1]]
                #         if prev_id == 0:
                #             continue
                #         datetime_start = df_cleaned["datetime"][assist2_between[j-1]]
                #     datetime_end = df_cleaned["datetime"][idx]
                #     minutes = minutes_diff(datetime_start, datetime_end)
                #     man_minutes[i].append(minutes)

                #     # If at the end of the list, get the time between the last
                #     # login (if the ID isn't zero) and the logged cycle time
                #     if j == len(assist2_between)-1:
                #         if df_cleaned["Assistant 2"][idx] != 0:
                #             datetime_start = df_cleaned["datetime"][assist2_between[j-1]]
                #             datetime_end = df_cleaned["datetime"][cyc_ind]
                #             minutes = minutes_diff(datetime_start, datetime_end)
                #             man_minutes[i].append(minutes)

                # for j,idx in enumerate(assist3_between):
                #     curr_id = df_cleaned["Assistant 3"][idx]
                #     if j == 0:
                #         if curr_id == 0:
                #             continue
                #         datetime_start = df_cleaned["datetime"][0]
                #     else:
                #         prev_id = df_cleaned["Assistant 3"][assist3_between[j-1]]
                #         if prev_id == 0:
                #             continue
                #         datetime_start = df_cleaned["datetime"][assist3_between[j-1]]
                #     datetime_end = df_cleaned["datetime"][idx]
                #     minutes = minutes_diff(datetime_start, datetime_end)
                #     man_minutes[i].append(minutes)

                #     # If at the end of the list, get the time between the last
                #     # login (if the ID isn't zero) and the logged cycle time
                #     if j == len(assist3_between)-1:
                #         if df_cleaned["Assistant 3"][idx] != 0:
                #             datetime_start = df_cleaned["datetime"][assist3_between[j-1]]
                #             datetime_end = df_cleaned["datetime"][cyc_ind]
                #             minutes = minutes_diff(datetime_start, datetime_end)
                #             man_minutes[i].append(minutes)

            else:
                # If someone was already logged in before the cycle started,
                # count them.
                input_idx = cycle_inds[i-1]
                idx = closest_before(input_idx, lead_inds)
                leadIDs[i].append(df_cleaned["Lead"][idx])

                # Get the IDs logged during the cycle
                low = cycle_inds[i-1]
                high = cyc_ind

                lead_between = between(lead_inds, low, high)
                leadIDs[i].extend(list_vals(df_cleaned["Lead"], lead_between))
                bag_between = between(bag_inds, low, high)
                bagdays_between = between(bag_days_inds, low, high)
                bagcycles_between = between(bag_cycles_inds, low, high)
                # assist1_between = between(assist1_inds, low, high)
                # assist2_between = between(assist2_inds, low, high)
                # assist3_between = between(assist3_inds, low, high)

                for j,idx in enumerate(lead_between):
                    if j == 0:
                        prev_idx = closest_before(idx, lead_inds)
                        prev_id = df_cleaned["Lead"][prev_idx]
                        if prev_id == 0:
                            continue
                        datetime_start = df_cleaned["datetime"][cycle_inds[i-1]]
                    else:
                        prev_id = df_cleaned["Lead"][lead_between[j-1]]
                        if prev_id == 0:
                            continue
                        datetime_start = df_cleaned["datetime"][lead_between[j-1]]
                    datetime_end = df_cleaned["datetime"][idx]
                    # minutes = minutes_diff(datetime_start, datetime_end)
                    # man_minutes[i].append(minutes)

                    # If at the end of the list, get the time between the last
                    # login (if the ID isn't zero) and the logged cycle time
                    if j == len(lead_between)-1:
                        if df_cleaned["Lead"][idx] != 0:
                            datetime_start = df_cleaned["datetime"][lead_between[j]]
                            datetime_end = df_cleaned["datetime"][cyc_ind]
                            # minutes = minutes_diff(datetime_start, datetime_end)
                            # man_minutes[i].append(minutes)

                # for j,idx in enumerate(bag_between):
                #     if j == 0:
                #         prev_idx = closest_before(idx, lead_inds)
                #         prev_id = df_cleaned["Bag"][prev_idx]
                #         if prev_id == 0:
                #             continue
                #         datetime_start = df_cleaned["datetime"][bag_inds[i-1]]
                #     else:
                #         prev_id = df_cleaned["Bag"][bag_between[j-1]]
                #         if prev_id == 0:
                #             continue
                #         datetime_start = df_cleaned["datetime"][bag_between[j-1]]
                #     datetime_end = df_cleaned["datetime"][idx]
                #     # minutes = minutes_diff(datetime_start, datetime_end)
                #     # man_minutes[i].append(minutes)

                #     # If at the end of the list, get the time between the last
                #     # login (if the ID isn't zero) and the logged cycle time
                #     if j == len(lead_between)-1:
                #         if df_cleaned["Bag"][idx] != 0:
                #             datetime_start = df_cleaned["datetime"][bag_between[j]]
                #             datetime_end = df_cleaned["datetime"][cyc_ind]
                #             # minutes = minutes_diff(datetime_start, datetime_end)
                #             # man_minutes[i].append(minutes)

                # for j,idx in enumerate(bagdays_between):
                #     if j == 0:
                #         prev_idx = closest_before(idx, bag_days_inds)
                #         prev_id = df_cleaned["Bag Days (Days)"][prev_idx]
                #         if prev_id == 0:
                #             continue
                #         datetime_start = df_cleaned["datetime"][cycle_inds[i-1]]
                #     else:
                #         prev_id = df_cleaned["Bag Days (Days)"][bagdays_between[j-1]]
                #         if prev_id == 0:
                #             continue
                #         datetime_start = df_cleaned["datetime"][bagdays_between[j-1]]
                #     datetime_end = df_cleaned["datetime"][idx]
                #     # minutes = minutes_diff(datetime_start, datetime_end)
                #     # man_minutes[i].append(minutes)

                #     # If at the end of the list, get the time between the last
                #     # login (if the ID isn't zero) and the logged cycle time
                #     if j == len(lead_between)-1:
                #         if df_cleaned["Bag Days (Days)"][idx] != 0:
                #             datetime_start = df_cleaned["datetime"][bagdays_between[j]]
                #             datetime_end = df_cleaned["datetime"][cyc_ind]
                #             # minutes = minutes_diff(datetime_start, datetime_end)
                #             # man_minutes[i].append(minutes)

                # for j,idx in enumerate(bagcycles_between):
                #     if j == 0:
                #         prev_idx = closest_before(idx, bag_cycles_inds)
                #         prev_id = df_cleaned["Bag Cycles"][prev_idx]
                #         if prev_id == 0:
                #             continue
                #         datetime_start = df_cleaned["datetime"][cycle_inds[i-1]]
                #     else:
                #         prev_id = df_cleaned["Bag Cycles"][bagcycles_between[j-1]]
                #         if prev_id == 0:
                #             continue
                #         datetime_start = df_cleaned["datetime"][bagcycles_between[j-1]]
                #     datetime_end = df_cleaned["datetime"][idx]
                #     # minutes = minutes_diff(datetime_start, datetime_end)
                #     # man_minutes[i].append(minutes)

                #     # If at the end of the list, get the time between the last
                #     # login (if the ID isn't zero) and the logged cycle time
                #     if j == len(lead_between)-1:
                #         if df_cleaned["Bag Cycles"][idx] != 0:
                #             datetime_start = df_cleaned["datetime"][bagcycles_between[j]]
                #             datetime_end = df_cleaned["datetime"][cyc_ind]
                #             # minutes = minutes_diff(datetime_start, datetime_end)
                #             # man_minutes[i].append(minutes)

                # for j,idx in enumerate(assist1_between):
                #     if j == 0:
                #         prev_idx = closest_before(idx, assist1_inds)
                #         prev_id = df_cleaned["Assistant 1"][prev_idx]
                #         if prev_id == 0:
                #             continue
                #         datetime_start = df_cleaned["datetime"][cycle_inds[i-1]]
                #     else:
                #         prev_id = df_cleaned["Assistant 1"][assist1_between[j-1]]
                #         if prev_id == 0:
                #             continue
                #         datetime_start = df_cleaned["datetime"][assist1_between[j-1]]
                #     datetime_end = df_cleaned["datetime"][idx]
                #     minutes = minutes_diff(datetime_start, datetime_end)
                #     man_minutes[i].append(minutes)

                #     # If at the end of the list, get the time between the last
                #     # login (if the ID isn't zero) and the logged cycle time
                #     if j == len(assist1_between)-1:
                #         if df_cleaned["Assistant 1"][idx] != 0:
                #             datetime_start = df_cleaned["datetime"][assist1_between[j]]
                #             datetime_end = df_cleaned["datetime"][cyc_ind]
                #             minutes = minutes_diff(datetime_start, datetime_end)
                #             man_minutes[i].append(minutes)

                # for j,idx in enumerate(assist2_between):
                #     if j == 0:
                #         prev_idx = closest_before(idx, assist2_inds)
                #         prev_id = df_cleaned["Assistant 2"][prev_idx]
                #         if prev_id == 0:
                #             continue
                #         datetime_start = df_cleaned["datetime"][cycle_inds[i-1]]
                #     else:
                #         prev_id = df_cleaned["Assistant 2"][assist2_between[j-1]]
                #         if prev_id == 0:
                #             continue
                #         datetime_start = df_cleaned["datetime"][assist2_between[j-1]]
                #     datetime_end = df_cleaned["datetime"][idx]
                #     minutes = minutes_diff(datetime_start, datetime_end)
                #     man_minutes[i].append(minutes)

                #     # If at the end of the list, get the time between the last
                #     # login (if the ID isn't zero) and the logged cycle time
                #     if j == len(assist2_between)-1:
                #         if df_cleaned["Assistant 2"][idx] != 0:
                #             datetime_start = df_cleaned["datetime"][assist2_between[j]]
                #             datetime_end = df_cleaned["datetime"][cyc_ind]
                #             minutes = minutes_diff(datetime_start, datetime_end)
                #             man_minutes[i].append(minutes)

                # for j,idx in enumerate(assist3_between):
                #     if j == 0:
                #         prev_idx = closest_before(idx, assist3_inds)
                #         prev_id = df_cleaned["Assistant 3"][prev_idx]
                #         if prev_id == 0:
                #             continue
                #         datetime_start = df_cleaned["datetime"][cycle_inds[i-1]]
                #     else:
                #         prev_id = df_cleaned["Assistant 3"][assist3_between[j-1]]
                #         if prev_id == 0:
                #             continue
                #         datetime_start = df_cleaned["datetime"][assist3_between[j-1]]
                #     datetime_end = df_cleaned["datetime"][idx]
                #     minutes = minutes_diff(datetime_start, datetime_end)
                #     man_minutes[i].append(minutes)

                #     # If at the end of the list, get the time between the last
                #     # login (if the ID isn't zero) and the logged cycle time
                #     if j == len(assist3_between)-1:
                #         if df_cleaned["Assistant 3"][idx] != 0:
                #             datetime_start = df_cleaned["datetime"][assist3_between[j]]
                #             datetime_end = df_cleaned["datetime"][cyc_ind]
                #             minutes = minutes_diff(datetime_start, datetime_end)
                #             man_minutes[i].append(minutes)


        # Get the unique IDs for each cycle time
        for i in range(len(leadIDs)):
            # Get unique lead IDs
            IDs = leadIDs[i]    # list of IDs
            IDs = list(np.unique(IDs))

            # Remove zeros for ID numbers
            if len(IDs) == 1 and IDs[0] == 0:
                pass
            else:
                IDs = [id for id in IDs if id != 0]

            if len(IDs) == 0:
                IDs = [0.0]

            leadIDs[i] = IDs

            # # Get unique assistant IDs
            # IDs = assistIDs[i]
            # IDs = list(np.unique(IDs))
            # assistIDs[i] = IDs
            
            # # Get unique bag, bag cycles, and bag days values (mostly to deal with repeats)
            # bagIDs[i] = list(np.unique(bagIDs[i]))
            # bagdays[i] = list(np.unique(bagdays[i]))
            # bagcycles[i] = list(np.unique(bagcycles[i]))
            

        # Find all instances of ID 2 and change to 999 (special case where
        # an operator changed numbers -- don't do this again!)
        for idlist in leadIDs:
            for i,id_int in enumerate(idlist):
                if id_int == 2.0:
                    idlist[i] = 999.0

        # for i,minutes_list in enumerate(man_minutes):
        #     man_minutes[i] = sum(minutes_list)

        # Catch whether the part is the first part on a Monday
        layup_times = list(df_cleaned["Layup Time (min.)"][layup_inds])
        close_times = list(df_cleaned["Close Time (min.)"][close_inds])
        resin_times = list(df_cleaned["Resin Time (min.)"][resin_inds])
        cycle_times = list(df_cleaned["Cycle Time (min.)"][cycle_inds])
        datetimes = list(df_cleaned["datetime"][cycle_inds])
        weekdays = [date.weekday() for date in datetimes]
        firstflags = []
        for i,day in enumerate(weekdays):
            if i == 0 and day == 0:
                if datetimes[i].time() < dt.time(8,0,0):
                    firstflags.append(1)
                else:
                    firstflags.append(0)
            elif day == 0 and weekdays[i-1] != 0:
                firstflags.append(1)
            else:
                firstflags.append(0)
                
        layup_threshold = 275
        layup_saturated = [True if time >= layup_threshold else False for time in layup_times]
        
        close_threshold = 90
        close_saturated = [True if time >= close_threshold else False for time in close_times]
        
        resin_threshold = 180
        resin_saturated = [True if time >= resin_threshold else False for time in resin_times]
                
        layup_target = 30
        layup_past_target = [True if (time >= layup_target) and (time < layup_threshold) else False for time in layup_times]
        
        close_target = 10
        close_past_target = [True if (time >= close_target) and (time < resin_threshold) else False for time in close_times]
        
        resin_target = 65
        resin_past_target = [True if (time >= resin_target) and (time < resin_threshold) else False for time in resin_times]
        
        # color = None
        # for key in moldcolors:
        #     if key in moldfile:
        #         color = moldcolors[key]
        #         break
        # if color is None:
        #     raise ValueError('No mold color detected')
        moldcolor = [color for time in resin_times]
            
        # Add data for showing which stages should be counted for each operator,
        # as well as whether the cycle time should be counted.
        layupIDs, closeIDs, resinIDs, cycleIDs = count_stages_for_operator(df_cleaned, stage_inds, leadIDs)

        # Create DataFrame for evaluations for current mold
        data_eval = {"datetime": datetimes,
                     "Day": weekdays,
                     "First Monday Part": firstflags, 
                     "Layup Time (min.)": layup_times,
                     "Close Time (min.)": close_times,
                     "Resin Time (min.)": resin_times,
                     "Cycle Time (min.)": cycle_times,
                     "Mold Color": moldcolor,
                     "Lead": cycleIDs,
                     "Layup Leads": layupIDs,
                     "Close Leads": closeIDs,
                     "Resin Leads": resinIDs,
                     "Layup Saturated": layup_saturated,
                     "Close Saturated": close_saturated,
                     "Resin Saturated": resin_saturated,
                     "Layup Past Target": layup_past_target,
                     "Close Past Target": close_past_target,
                     "Resin Past Target": resin_past_target,
                     }

        df_eval_mold = pd.DataFrame(data=data_eval)

        # Append mold data to larger DataFrame for all data
        df_eval = pd.concat([df_eval, df_eval_mold], ignore_index=True)
        
    # Add extracted date and time columns for further sorting
    df_eval['date'] = df_eval['datetime'].dt.date
    df_eval['time'] = df_eval['datetime'].dt.time
    df_eval.insert(1, 'date', df_eval.pop('date'))
    df_eval.insert(2, 'time', df_eval.pop('time'))

    return df_eval


if __name__ == "__main__":
    mold_data_folder = r'C:\Users\Ryan.Larson.ROCKWELLINC\github\plc-data-analysis\Production_Analysis\2024_Data\Molds'
    df_eval = prepare_mold_data(mold_data_folder)
    
    total = len(df_eval)
    total_no_saturated = (df_eval[['Layup Saturated', 'Close Saturated', 'Resin Saturated']]==False).all(axis=1).sum()
    no_saturated_mask = (df_eval[['Layup Saturated', 'Close Saturated', 'Resin Saturated']]==False).all(axis=1)
    df_no_saturated = df_eval[no_saturated_mask]
    
    count_layup_past_target = df_eval[df_eval['Layup Past Target'] == True].shape[0]
    count_close_past_target = df_eval[df_eval['Close Past Target'] == True].shape[0]
    count_resin_past_target = df_eval[df_eval['Resin Past Target'] == True].shape[0]
    count_layup_past_target_no_saturated = df_eval[(df_eval['Layup Past Target'] == True) & (df_eval['Layup Saturated'] == False)].shape[0]
    count_close_past_target_no_saturated = df_eval[(df_eval['Close Past Target'] == True) & (df_eval['Close Saturated'] == False)].shape[0]
    count_resin_past_target_no_saturated = df_eval[(df_eval['Resin Past Target'] == True) & (df_eval['Resin Saturated'] == False)].shape[0]
    
    print('')
    print(f'Layup times over target: {count_layup_past_target/total:.1%}')
    print(f'Close times over target: {count_close_past_target/total:.1%}')
    print(f'Resin times over target: {count_resin_past_target/total:.1%}')
    print('')
    print(f'Layup times over target (no saturated): {count_layup_past_target_no_saturated/total_no_saturated:.1%}')
    print(f'Close times over target (no saturated): {count_close_past_target_no_saturated/total_no_saturated:.1%}')
    print(f'Resin times over target (no saturated): {count_resin_past_target_no_saturated/total_no_saturated:.1%}')
    
    # Plot histograms of the non-saturated stage times, using all data (not segmented by time of day)
    layup_target = 30
    close_target = 10
    resin_target = 65
    
    sns.set_style('whitegrid')
    
    
    # Calculate the minutes (hours) of stage time overage
    # Layup
    layup_overage_minutes = df_no_saturated[df_no_saturated['Layup Past Target']==True]['Layup Time (min.)'] - layup_target
    close_overage_minutes = df_no_saturated[df_no_saturated['Close Past Target']==True]['Close Time (min.)'] - close_target
    resin_overage_minutes = df_no_saturated[df_no_saturated['Resin Past Target']==True]['Resin Time (min.)'] - resin_target
    
    layup_overage_total = layup_overage_minutes.sum()
    close_overage_total = close_overage_minutes.sum()
    resin_overage_total = resin_overage_minutes.sum()
    
    # Calculate the value of the resin overage time due to meal times
    lunch_start = 11.8
    lunch_end = 13.2
    lunch_mask = (df_no_saturated['resin_hours_since_midnight'] > lunch_start) & (df_no_saturated['resin_hours_since_midnight'] < lunch_end)
    df_lunch = df_no_saturated[lunch_mask]
    lunch_resin_overage_minutes = df_lunch[df_lunch['Resin Past Target']==True]['Resin Time (min.)'] - resin_target
    lunch_resin_overage_total = lunch_resin_overage_minutes.sum()
    
    dinner_start = 17.3
    dinner_end = 18.3
    dinner_mask = (df_no_saturated['resin_hours_since_midnight'] > dinner_start) & (df_no_saturated['resin_hours_since_midnight'] < dinner_end)
    df_dinner = df_no_saturated[dinner_mask]
    dinner_resin_overage_minutes = df_dinner[df_dinner['Resin Past Target']==True]['Resin Time (min.)'] - resin_target
    dinner_resin_overage_total = dinner_resin_overage_minutes.sum()
    
        
    
    
    # df_no_saturated['hours_since_midnight'] = df_no_saturated['time'].apply(lambda x: x.hour + x.minute / 60.0)
    # df_no_saturated['close_finish_hours_since_midnight'] = df_no_saturated['hours_since_midnight'] - (1/60.0) * df_no_saturated['Resin Time (min.)']
    df_no_saturated.loc[:, 'resin_hours_since_midnight'] = df_no_saturated['time'].apply(lambda x: x.hour + x.minute / 60.0)
    df_no_saturated.loc[:, 'close_hours_since_midnight'] = (
        df_no_saturated['resin_hours_since_midnight'] - (1 / 60.0) * df_no_saturated['Resin Time (min.)']
    )
    df_no_saturated.loc[:, 'layup_hours_since_midnight'] = (
        df_no_saturated['close_hours_since_midnight'] - (1 / 60.0) * df_no_saturated['Close Time (min.)']
    )
    
    # Layup
    plt.figure(dpi=300)
    sns.histplot(df_no_saturated, x='Layup Time (min.)', kde=False, bins=30)
    plt.title('Distribution of Layup Times in 2024')
    plt.xlabel('Layup Time (min.)')
    plt.ylabel('Frequency')
    plt.axvline(x=layup_target, color='red', linestyle='--', linewidth=2, label='Target Layup Time')
    plt.legend()
    
    plt.figure(dpi=300)
    sns.scatterplot(data=df_no_saturated, x='layup_hours_since_midnight', y='Layup Time (min.)', alpha=0.2, s=30)
    plt.title('Layup Time by Hours Since Midnight')
    plt.xlabel('Time of Day')
    plt.ylabel('Layup Time (min.)')
    plt.axhline(y=layup_target, color='red', linestyle='--', linewidth=2, label='Target Layup Time')
    plt.legend()
    
    # Close
    plt.figure(dpi=300)
    sns.histplot(df_no_saturated, x='Close Time (min.)', kde=False, bins=30)
    plt.title('Distribution of Close Times in 2024')
    plt.xlabel('Close Time (min.)')
    plt.ylabel('Frequency')
    plt.axvline(x=close_target, color='red', linestyle='--', linewidth=2, label='Target Close Time')
    plt.legend()
    
    plt.figure(dpi=300)
    # df_no_saturated['hours_since_midnight'] = df_no_saturated['time'].apply(lambda x: x.hour + x.minute / 60.0)
    sns.scatterplot(data=df_no_saturated, x='close_hours_since_midnight', y='Close Time (min.)', alpha=0.2, s=30)
    plt.title('Close Time by Hours Since Midnight')
    plt.xlabel('Time of Day')
    plt.ylabel('Close Time (min.)')
    plt.axhline(y=close_target, color='red', linestyle='--', linewidth=2, label='Target Close Time')
    plt.legend()
    
    # Resin
    plt.figure(dpi=300)
    sns.histplot(df_no_saturated, x='Resin Time (min.)', kde=False, bins=30)
    plt.title('Distribution of Resin Times in 2024')
    plt.xlabel('Resin Time (min.)')
    plt.ylabel('Frequency')
    plt.axvline(x=resin_target, color='red', linestyle='--', linewidth=2, label='Target Resin Time')
    plt.legend()
    
    plt.figure(dpi=300)
    # df_no_saturated['resin_hours_since_midnight'] = df_no_saturated['time'].apply(lambda x: x.hour + x.minute / 60.0)
    sns.scatterplot(data=df_no_saturated, x='resin_hours_since_midnight', y='Resin Time (min.)', alpha=0.2, s=30)
    plt.title('Resin Time by Hours Since Midnight')
    plt.xlabel('Time of Day')
    plt.ylabel('Resin Time (min.)')
    plt.axhline(y=resin_target, color='red', linestyle='--', linewidth=2, label='Target Resin Time')
    plt.legend()
    