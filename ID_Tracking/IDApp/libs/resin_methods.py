# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 14:28:35 2022

@author: Ryan.Larson
"""

import numpy as np
import pandas as pd
import requests
import datetime as dt
import pytz
import api_config_vars_resin as api
import sys
import seaborn as sns
import matplotlib.pyplot as plt
from dateutil import rrule
from calendar import monthrange

sys.path.append("..")

# import ID_Tracking.IDApp.libs.cycle_time_methods_v2 as cycle



def load_resin_data_single_plc(dtstart, dtend, resincolor):
    
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
    
    
    ### Load in resin tank data
    url = api.url
    
    publicID = api.publicIds[resincolor]
    tags = api.resin_tags[resincolor]
    
    payload = {
        "source": {"publicId": publicID},
        "tags": tags,
        "start": dtstart,
        "end": dtend,
        "timeZone": "America/Denver"
    }
    headers = api.resin_headers
    
    response = requests.request("POST", url, json=payload, headers=headers)
    
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
    
    # Remove the last row that is filled with nan
    df = df.dropna() 
    
    def convert_short_flag(x):
        if "True" in x:
            y = True
        else:
            y = False
        return y
    
    # Convert to the relevant data types
    for i,col in enumerate(df.columns):
        if col == "time":
            df[col] = pd.to_datetime(df[col])
        elif col == "Short Flag":
            # pass
            df[col] = df[col].apply(convert_short_flag)
            # df[col] = df[col].map({"True ": True, "False ": False})
        else:
            df[col] = df[col].astype(float)        
            
    return df
    

def calculate_machine_error(df):    
    df["Extra Resin"] = np.where((df["Extra Resin Start Weight"] != 0) | (df["1st Part Number"] == 0), True, False)
    
    df_extra = df[df["Extra Resin"] == True]
    df_no_extra = df[df["Extra Resin"] == False]
    
    df_extra["Machine Error"] = df_extra["Extra Resin Start Weight"] - df_extra["Nominal Resin Weight"]
    df_no_extra["Machine Error"] = df_no_extra["Total Weight"] - df_no_extra["Nominal Resin Weight"]
    
    dfupdate = pd.concat([df_extra, df_no_extra])
    df_no_short = dfupdate[dfupdate["Short Flag"] == False]
    dfupdate = dfupdate.sort_index()
    return dfupdate, df_no_short

def summarize_variability(dfupdate):
    ### Machine Error ###
    avg_machine_error = dfupdate["Machine Error"].mean()
    print("Machine Error:")
    print("Average:\t{}".format(avg_machine_error))
    
    ### Extra Resin ###
    # Total extra resin
    tot_extra_resin = dfupdate["Extra Resin Weight"].sum()
    # % of dispensed resin cases that are extra resin
    pct_extra = len(dfupdate[dfupdate["Extra Resin"]==True])/len(dfupdate)
    # Average extra resin per part
    avg_extra_resin = dfupdate["Extra Resin Weight"].mean()
    print("\nExtra Resin:")
    print("Total Pounds Extra:\t{}".format(tot_extra_resin))
    print("Percentage of Parts with Extra:\t{}".format(pct_extra))
    print("Average Extra Resin Per Part:\t{}".format(avg_extra_resin))
    
    ### Short Flag Cases ###
    short_count = len(dfupdate[dfupdate["Short Flag"]==True])
    pct_short = short_count/len(dfupdate)
    print("\nShort Cases:")
    print("Short Count:\t{}".format(short_count))
    print("Percentage of Parts Short of Nominal:\t{}".format(pct_short))
    
    

def plot_machine_error(dfgray, dftan):
    # Prepare dataframes for combination
    dfgray["Color"] = "Gray"
    dftan["Color"] = "Tan"
    
    dfgray_auto = dfgray[dfgray["1st Part Number"] != 0]
    dftan_auto = dftan[dftan["1st Part Number"] != 0]
    
    dfall = pd.concat([dfgray_auto, dftan_auto])
    dfall = dfall.reset_index(drop=True)
    
    sns.set_theme(style="whitegrid")
    customPalette = sns.light_palette("lightblue", 2)
    flierprops = dict(marker='o', markerfacecolor='None', markersize=4)
    # Plot with outliers
    plt.figure(dpi=300)
    sns.boxplot(x="Color", y="Machine Error", data=dfall, flierprops=flierprops, palette=customPalette)
    plt.title("Resin Dispenser Machine Error")
    # Plot without outliers
    plt.figure(dpi=300)
    sns.boxplot(x="Color", y="Machine Error", data=dfall, showfliers=False, palette=customPalette)
    plt.title("Resin Dispenser Machine Error (No Outliers)")
    
    return dfgray_auto, dftan_auto
    

if __name__ == "__main__":
    # startdate = dt.date(2022,3,1)
    # enddate = dt.date.today()
    
    dtstart = dt.datetime(2023,3,13,0,0,0)
    dtend = dt.datetime.now()
    resincolors = ["Gray", "Tan"]
    
    sizes = [0.0, 1111.0, 422324.0, 422336.0, 422348.0, 422360.0, 422372.0,
              422380.0, 664436.0, 664448.0, 664460.0, 664472.0, 664484.0,
              664496.0, 6644102.0]
    
    partslist = []
    
    # df_partcounts = pd.DataFrame()
    # df_partcounts = df_partcounts.set_axis(sizes)
    
    dfgray = load_resin_data_single_plc(dtstart, dtend, "Gray")    
    dfgray, gray_no_short = calculate_machine_error(dfgray)
    print("\n##### Gray Resin Summary #####")
    summarize_variability(dfgray)
    
    partnums = dfgray.iloc[:,1].value_counts()
    partnums2 = dfgray.iloc[:,2].value_counts()
    partsgray = partnums.append(partnums2)
    partsgray.rename("Gray", inplace=True)
    
    # df_partcounts.append(parts)
    
    dftan = load_resin_data_single_plc(dtstart, dtend, "Tan")
    dftan, tan_no_short = calculate_machine_error(dftan)
    print("\n\n##### Tan Resin Summary #####")
    summarize_variability(dftan)
    
    partnums = dftan.iloc[:,1].value_counts()
    partnums2 = dftan.iloc[:,2].value_counts()
    partstan = partnums.append(partnums2)
    partstan.rename("Tan", inplace=True)
    
    parts_gray = partsgray.to_dict()
    parts_tan = partstan.to_dict()
    
    parts_sum = {}
    
    for size in sizes:
        if size in parts_gray.keys() and size in parts_tan.keys():
            parts_sum[size] = parts_gray[size] + parts_tan[size]
        elif size in parts_gray.keys() and size not in parts_tan.keys():
            parts_sum[size] = parts_gray[size]
        elif size in parts_tan.keys() and size not in parts_gray.keys():
            parts_sum[size] = parts_tan[size]
            
    dfgray_auto, dftan_auto = plot_machine_error(gray_no_short, tan_no_short)