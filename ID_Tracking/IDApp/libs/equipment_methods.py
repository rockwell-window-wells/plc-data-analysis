# -*- coding: utf-8 -*-
"""
Created on Thu Mar 24 13:33:10 2022

@author: Ryan.Larson
"""

import numpy as np
import pandas as pd
import requests
import datetime as dt
import pytz
import api_config_vars as api
import matplotlib.pyplot as plt
import seaborn as sns
import math

from cycle_time_methods_v2 import between, closest_before, closest_idx

# from . import data_assets
import data_assets


def load_bag_data_single_mold(dtstart, dtend, moldcolor):
    """
    

    Parameters
    ----------
    dtstart : TYPE
        DESCRIPTION.
    dtend : TYPE
        DESCRIPTION.
    moldcolor : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    # Adjust dtstart and dtend to Central European Time for API compatibility
    mtn = pytz.timezone('US/Mountain')
    cet = pytz.timezone('CET')
    
    dtstart = mtn.localize(dtstart)
    dtend = mtn.localize(dtend)
    
    dtstart = dtstart.astimezone(cet)
    dtend = dtend.astimezone(cet)
    
    # Subtract an hour from start (weird API behavior adjustment - end time
    # doesn't appear to be affected by this issue, so it's not a daylight
    # savings time thing)
    dtstart = dtstart - dt.timedelta(hours=1)
    dtend = dtend - dt.timedelta(hours=1)
    
    # Convert dtstart and dtend from datetimes to formatted strings
    dtstart = dtstart.strftime("%Y-%m-%dT%H:%M:%SZ")
    dtend = dtend.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    url = api.url

    publicID = api.publicIds[moldcolor]
    tags = api.bag_tags[moldcolor]

    payload = {
        "source": {"publicId": publicID},
        "tags": tags,
        "start": dtstart,
        "end": dtend,
        "timeZone": "America/Denver"
    }
    headers = api.operator_headers

    response = requests.request("POST", url, json=payload, headers=headers)

    # print(response.text)

    # Save the response as a string
    datastr = response.text
    # print(datastr)

    # Convert the data string to a Pandas DataFrame
    df = pd.DataFrame([x.split(',') for x in datastr.split('\n')])
    new_header = df.iloc[0] #grab the first row for the header
    df = df[1:] #take the data less the header row
    df.columns = new_header #set the header row as the df header
    df = df.reset_index(drop=True)

    # Replace empty values with NaN
    df = df.replace(r'^\s*$', np.nan, regex=True)

    # Fix last column name having a carriage return at the end of the string
    lastcolold = df.columns[-1]
    if lastcolold[-1] == "\r":
        # print("Carriage return found at the end of column name")
        lastcolnew = lastcolold[0:-1]
        df = df.rename(columns={lastcolold: lastcolnew})
    
    # Convert to the relevant data types
    for i,col in enumerate(df.columns):
        if col == "time":
            df[col] = pd.to_datetime(df[col])
        else:
            df[col] = df[col].astype(float)
    
    # Fix issue where some data is read in from the day before the date of
    # dtstart. Get rid of rows with a date earlier than daystart.
    dtstart = dt.datetime.strptime(dtstart, "%Y-%m-%dT%H:%M:%SZ")
    daystart = dt.datetime.date(dtstart)
    df = df.loc[pd.to_datetime(df["time"]).dt.date >= daystart]

    return df


def organize_bag_data(dtstart, dtend):
    """
    

    Parameters
    ----------
    dtstart : TYPE
        DESCRIPTION.
    dtend : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    df_equip = pd.DataFrame()
    
    for moldcolor in api.molds:
        df_raw = load_bag_data_single_mold(dtstart, dtend, moldcolor)
        
        # Clean the data here before sending to a list of dataframes
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
                            if np.isnan(df_sorted["Bag"].iloc[i]):
                                if np.isnan(df_sorted["Bag Days"].iloc[i]):
                                    if np.isnan(df_sorted["Bag Cycles"].iloc[i]):
                                        nan_indices.append(i)

        df_cleaned = df_sorted.drop(df_sorted.index[nan_indices])
        df_cleaned = df_cleaned.reset_index(drop=True)
        
        # Make a new dataframe with only time, Cycle Time, Bag,
        # Bag Days, and Bag Count columns.
        
        # Find the indices where there is a layup time.
        layup_inds = []
        not_nan_series = df_cleaned["Layup Time"].notnull()
        for i in range(len(not_nan_series)):
            if not_nan_series.iloc[i] == True:
                layup_inds.append(i)
                
        # Find the indices where there is a close time.
        close_inds = []
        not_nan_series = df_cleaned["Close Time"].notnull()
        for i in range(len(not_nan_series)):
            if not_nan_series.iloc[i] == True:
                close_inds.append(i)
                
        # Find the indices where there is a resin time.
        resin_inds = []
        not_nan_series = df_cleaned["Resin Time"].notnull()
        for i in range(len(not_nan_series)):
            if not_nan_series.iloc[i] == True:
                resin_inds.append(i)
        
        # Find the indices where there is a cycle time.
        cycle_inds = []
        not_nan_series = df_cleaned["Cycle Time"].notnull()
        for i in range(len(not_nan_series)):
            if not_nan_series.iloc[i] == True:
                cycle_inds.append(i)
        
        # Find the indices where there is a bag ID.
        bagid_inds = []
        not_nan_series = df_cleaned["Bag"].notnull()
        for i in range(len(not_nan_series)):
            if not_nan_series.iloc[i] == True:
                bagid_inds.append(i)
                
        # Find the indices where there is a bag day count.
        bagdays_inds = []
        not_nan_series = df_cleaned["Bag Days"].notnull()
        for i in range(len(not_nan_series)):
            if not_nan_series.iloc[i] == True:
                bagdays_inds.append(i)
                
        # Find the indices where there is a bag cycle count.
        bagcycles_inds = []
        not_nan_series = df_cleaned["Bag Cycles"].notnull()
        for i in range(len(not_nan_series)):
            if not_nan_series.iloc[i] == True:
                bagcycles_inds.append(i)
                
        
        bagIDs = []
        bagdays = []
        bagcycles = []
        
        layup_times = []
        close_times = []
        resin_times = []
        
        layup_idx_diff = []
        close_idx_diff = []
        resin_idx_diff = []
        
        # For each cycle time, get the most recent bag number, bag days, and
        # bag cycle count
        for i, cyc_ind in enumerate(cycle_inds):
            
            if i == 0:
                bagIDs.append(df_cleaned["Bag"][bagid_inds[0]])
                bagdays.append(df_cleaned["Bag Days"][bagdays_inds[0]])
                bagcycles.append(df_cleaned["Bag Cycles"][bagcycles_inds[0]])
                
                layup_times.append(df_cleaned["Layup Time"][layup_inds[0]])
                close_times.append(df_cleaned["Close Time"][close_inds[0]])
                resin_times.append(df_cleaned["Resin Time"][resin_inds[0]])
            else:            
                input_idx = cycle_inds[i]
                idx = closest_before(input_idx, bagid_inds)
                bagIDs.append(df_cleaned["Bag"][idx])
                idx = closest_before(input_idx, bagdays_inds)
                bagdays.append(df_cleaned["Bag Days"][idx])
                idx = closest_before(input_idx, bagcycles_inds)
                bagcycles.append(df_cleaned["Bag Cycles"][idx])
                
                idx = closest_idx(input_idx, layup_inds)
                layup_idx_diff.append(input_idx-idx)
                if np.abs(input_idx-idx) >= 3:
                    # print("Layup: {} - {}".format(input_idx, idx))
                    layup_times.append(np.nan)
                else:
                    layup_times.append(df_cleaned["Layup Time"][idx])
                
                idx = closest_idx(input_idx, close_inds)
                close_idx_diff.append(input_idx-idx)
                if np.abs(input_idx-idx) >= 3:
                    # print("Close: {} - {}".format(input_idx, idx))
                    close_times.append(np.nan)
                else:
                    close_times.append(df_cleaned["Close Time"][idx])
                
                idx = closest_idx(input_idx, resin_inds)
                resin_idx_diff.append(input_idx-idx)
                if np.abs(input_idx-idx) >= 3:
                    # print("Resin: {} - {}".format(input_idx, idx))
                    resin_times.append(np.nan)
                else:
                    resin_times.append(df_cleaned["Resin Time"][idx])
        
        cycle_times = list(df_cleaned["Cycle Time"][cycle_inds])
        datetimes = list(df_cleaned["time"][cycle_inds])
        
        saturated = []
        
        for i,val in enumerate(layup_times):
            if math.isnan(val):
                # print("Found nan in layup, index {}".format(i))
                layup_times[i] = cycle_times[i] - resin_times[i] - close_times[i]
                
        for i,val in enumerate(close_times):
            if math.isnan(val):
                # print("Found nan in close, index {}".format(i))
                close_times[i] = cycle_times[i] - resin_times[i] - layup_times[i]
                
        for i,val in enumerate(resin_times):
            if math.isnan(val):
                # print("Found nan in resin, index {}".format(i))
                resin_times[i] = cycle_times[i] - close_times[i] - layup_times[i]
                
        for i in range(len(cycle_times)):
            if layup_times[i] >= 275:
                saturated.append(True)
                continue
            elif close_times[i] >= 90:
                saturated.append(True)
                continue
            elif resin_times[i] >= 180:
                saturated.append(True)
                continue
            else:
                saturated.append(False)
                
        repeated_rows = []
        for i in range(len(cycle_times)):
            if i == 0:
                continue
            if layup_times[i] == layup_times[i-1]:
                if close_times[i] == close_times[i-1]:
                    if resin_times[i] == resin_times[i-1]:
                        # print("Found repeated row, index {}".format(i))
                        repeated_rows.append(i)
        
        data_equip = {"time": datetimes, "Layup Time": layup_times,
                      "Close Time": close_times, "Resin Time": resin_times,
                      "Cycle Time": cycle_times,
                      "Bag": bagIDs, "Bag Days": bagdays,
                      "Bag Cycles": bagcycles, "Saturated Time": saturated}
    
        df_equip_mold = pd.DataFrame(data=data_equip)
        
        # Filter out rows that are repeated, based on indices listed in 
        # repeated_rows
        delete_rows = []
        for i,row in enumerate(repeated_rows):
            t1 = df_equip_mold["time"].iloc[row]
            t0 = df_equip_mold["time"].iloc[row-1]
            
            tdelta = t1-t0
            tdelta_seconds = tdelta.total_seconds()
            
            cycle_seconds = df_equip_mold["Cycle Time"].iloc[row] * 60
            
            if cycle_seconds > tdelta_seconds:
                delete_rows.append(row)
                
        df_equip_mold = df_equip_mold.drop(df_equip_mold.index[delete_rows])
        df_equip_mold = df_equip_mold.reset_index(drop=True)
        
        # initial_bag_cycles = df_equip_mold["Bag Cycles"].iloc[0]
        # bag_cycles = []
        # for i in range(len(df_equip_mold["Cycle Time"])):
        #     if i == 0:
        #         bag_cycles.append(initial_bag_cycles)
        #     else:
        #         bag_cycles.append(initial_bag_cycles + i)
        
        # df_equip_mold["Bag Cycles"] = bag_cycles
        
        df_equip = pd.concat([df_equip, df_equip_mold], ignore_index=True)
        
    return df_equip
    

def correlate_bag_cycles(df_equip_bag):
    """
    Display the correlation relationship between cycle time and bag usage
    parameters (days in use and number of cycles in use). Generates two plots,
    with linear fit lines drawn.

    Parameters
    ----------
    df_equip_bag : Pandas DataFrame
        The output of organize_bag_data(), which has columns Cycle Time, Bag,
        Bag Days, and Bag Cycles.

    Returns
    -------
    None.

    """
    
    non_saturated = df_equip_bag.loc[df_equip_bag["Saturated Time"] == False]
    
    bagdays_nonsat = non_saturated["Bag Days"]
    cycletimes_nonsat = non_saturated["Cycle Time"]
    bagcycles_nonsat = non_saturated["Bag Cycles"]
    
    bagdays = df_equip_bag["Bag Days"]
    cycletimes = df_equip_bag["Cycle Time"]
    bagcycles = df_equip_bag["Bag Cycles"]
    
    fig1,ax1 = plt.subplots(dpi=300)
    sns.set_theme(style="whitegrid")
    sns.regplot(x=bagdays_nonsat, y=cycletimes_nonsat, color='b', line_kws={"color": "red"})
    ax1.set_title("Bag Age Trends - Non Saturated Times")
    
    fig2,ax2 = plt.subplots(dpi=300)
    sns.set_theme(style="whitegrid")
    sns.regplot(x=bagcycles_nonsat, y=cycletimes_nonsat, color='b', line_kws={"color": "red"})
    ax2.set_title("Bag Usage Trends - Non Saturated Times")
    
    fig3,ax3 = plt.subplots(dpi=300)
    sns.set_theme(style="whitegrid")
    sns.regplot(x=bagdays, y=cycletimes, color='b', line_kws={"color": "red"})
    ax3.set_title("Bag Age Trends - All Times")
    
    fig4,ax4 = plt.subplots(dpi=300)
    sns.set_theme(style="whitegrid")
    sns.regplot(x=bagcycles, y=cycletimes, color='b', line_kws={"color": "red"})
    ax4.set_title("Bag Usage Trends - All Times")
    

def stdev_over_time(df_equip_bag, sweepwindow):
    
    non_saturated = df_equip_bag.loc[df_equip_bag["Saturated Time"] == False]
    
    # bagdays_nonsat = non_saturated["Bag Days"]
    cycletimes_nonsat = non_saturated["Cycle Time"]
    bagcycles_nonsat = non_saturated["Bag Cycles"]
    
    sweep_plot_start = int(sweepwindow) + int(bagcycles_nonsat.min())
    sweep_plot_end = int(bagcycles_nonsat.max())
    sweep_plot_cycles = list(range(sweep_plot_start, sweep_plot_end+1))
    
    # sweep_plot_start_cycle = int(bagcycles_nonsat.min() + sweepwindow/2)
    
    
    # sweep_plot_cycles = list(df_equip_bag["Bag Cycles"].iloc[sweep_plot_indices])
    
    stdev_sweep = []
    for i,idx in enumerate(sweep_plot_cycles):
        sweep_start = idx - int(sweepwindow)
        sweep_end = sweep_start + sweepwindow
        sweep_indices = list(range(sweep_start, sweep_end+1))
        
        stdev = np.std(df_equip_bag["Cycle Time"].iloc[sweep_indices])
        stdev_sweep.append(stdev)
    
    fig1,ax1 = plt.subplots(dpi=300)
    sns.set_theme(style="whitegrid")
    sns.scatterplot(x=bagcycles_nonsat, y=cycletimes_nonsat, color='b', alpha=0.5)
    sns.lineplot(x=sweep_plot_cycles, y=stdev_sweep, color='r')
    
    return sweep_plot_cycles
    


if __name__ == "__main__":
    dtstart = dt.datetime(2022,3,25,16,0,0)
    enddate = dt.date.today()
    # enddate = dt.date(2022,3,17)
    endtime = dt.time(23,59,59)
    dtend = dt.datetime.combine(enddate, endtime)
    
    # df = load_bag_data_single_mold(dtstart, dtend, "Purple")
    df_equip = organize_bag_data(dtstart, dtend)
    
    # correlate_bag_cycles(df_equip)
    
    
    sweepwindow = 50
    sweep_plot_cycles = stdev_over_time(df_equip, sweepwindow)