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

from cycle_time_methods_v2 import between, closest_before


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
        
        # For each cycle time, get the most recent bag number, bag days, and
        # bag cycle count
        for i, cyc_ind in enumerate(cycle_inds):
            
            if i == 0:
                bagIDs.append(df_cleaned["Bag"][bagid_inds[0]])
                bagdays.append(df_cleaned["Bag Days"][bagdays_inds[0]])
                bagcycles.append(df_cleaned["Bag Cycles"][bagcycles_inds[0]])
            else:            
                input_idx = cycle_inds[i-1]
                idx = closest_before(input_idx, bagid_inds)
                bagIDs.append(df_cleaned["Bag"][idx])
                idx = closest_before(input_idx, bagdays_inds)
                bagdays.append(df_cleaned["Bag Days"][idx])
                idx = closest_before(input_idx, bagcycles_inds)
                bagcycles.append(df_cleaned["Bag Cycles"][idx])
                
            
            
        
        
        cycle_times = list(df_cleaned["Cycle Time"][cycle_inds])
        datetimes = list(df_cleaned["time"][cycle_inds])
        
        
        data_equip = {"time": datetimes, "Cycle Time": cycle_times,
                      "Bag": bagIDs, "Bag Days": bagdays,
                      "Bag Cycles": bagcycles}
    
        df_equip_mold = pd.DataFrame(data=data_equip)
        
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
    bagdays = df_equip_bag["Bag Days"]
    cycletimes = df_equip_bag["Cycle Time"]
    bagcycles = df_equip_bag["Bag Cycles"]
    
    fig1,ax1 = plt.subplots(dpi=300)
    sns.set_theme(style="whitegrid")
    sns.regplot(x=bagdays, y=cycletimes, color='b', line_kws={"color": "red"})
    ax1.set_title("Bag Age Trends")
    
    fig2,ax2 = plt.subplots(dpi=300)
    sns.set_theme(style="whitegrid")
    sns.regplot(x=bagcycles, y=cycletimes, color='b', line_kws={"color": "red"})
    ax2.set_title("Bag Usage Trends")
    



if __name__ == "__main__":
    dtstart = dt.datetime(2022,3,25,16,0,0)
    enddate = dt.date.today()
    # enddate = dt.date(2022,3,17)
    endtime = dt.time(23,59,59)
    dtend = dt.datetime.combine(enddate, endtime)
    
    # df = load_bag_data_single_mold(dtstart, dtend, "Purple")
    df_equip = organize_bag_data(dtstart, dtend)
    
    correlate_bag_cycles(df_equip)