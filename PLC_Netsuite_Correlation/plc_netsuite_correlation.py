# -*- coding: utf-8 -*-
"""
Created on Thu Jan 20 08:01:11 2022

@author: Ryan.Larson

Attempt to find a correlation between the PLC resin tank data for part counts 
and the Netsuite data for the same period. Make adjustments for time delays and
incorrect part inference from PLC.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
# import datetime as dt

# Load the data into Pandas DataFrames
# netsuite = pd.read_csv("Resin_Builds.csv",
#                        parse_dates=["Date"])
netsuite = pd.read_csv("Resin_Builds_with_time.csv",
                       parse_dates=["Date"])
tan = pd.read_csv("tan_2021-12-14T00-00-00_2022-01-19T23-59-59.csv",
                  parse_dates=["DateTime"])
gray = pd.read_csv("gray_2021-12-14T00-00-00_2022-01-19T23-59-59.csv",
                   parse_dates=["DateTime"])

# Get rid of additional resin counts (part number 1111)
tan = tan[tan.PartNumber != 1111]
gray = gray[gray.PartNumber != 1111]

# Apply WRG or WRT prefix to part numbers in tan and gray DataFrames to match
# the netsuite part numbering and allow combining of data
tan["PartNumber"] = tan["PartNumber"].apply(lambda x: "WRT" + str(x))
gray["PartNumber"] = gray["PartNumber"].apply(lambda x: "WRG" + str(x))

# Reset indices after removing rows
tan = tan.reset_index(drop=True)
gray = gray.reset_index(drop=True)

# # Delete extra columns on tan before combining colors
# tan = tan.drop(["Unnamed: 8", "Unnamed: 9", "Unnamed: 10"], axis=1)

### PLC Data Formatting ###
# Combine color data, sort it, and reapply index
plcdata = tan.append(gray)
plcdata = plcdata.sort_values(by=["DateTime"])
plcdata = plcdata.reset_index(drop=True)

# Pull off date alone into new column
plcdata["Date"] = plcdata["DateTime"].dt.date
netsuite["Date"] = netsuite["Date"].dt.date

# Rearrange columns
plcdata = plcdata.reindex(columns=["DateTime", "Date", "PartNumber",
                                   "NominalResinWeight", "TotalWeight",
                                   "ResinWeight", "PigmentWeight",
                                   "CatalystWeight", "ExcessResinWeight"])

# Get unique dates and part numbers from plcdata
plc_unique_dates = list(plcdata.Date.unique())
plc_unique_parts = list(plcdata.PartNumber.unique())
plc_unique_parts = sorted(plc_unique_parts)

# Get the unique days and parts in the netsuite data
netsuite_unique_dates = list(netsuite.Date.unique())
netsuite_unique_parts = list(netsuite.Item.unique())
netsuite_unique_parts = sorted(netsuite_unique_parts)

# Combine and get a list of all the unique parts in any data.
not_common_parts = list(set(netsuite_unique_parts) ^ set(plc_unique_parts))
all_unique_parts = plc_unique_parts
for i, part in enumerate(not_common_parts):
    all_unique_parts.append(part)

all_unique_parts = set(all_unique_parts)
all_unique_parts = list(all_unique_parts)
all_unique_parts = sorted(all_unique_parts)

# For each unique date, get the count of each part from PLC data
plc_day_data = np.zeros((len(plc_unique_dates), len(all_unique_parts)))
for i,day in enumerate(plc_unique_dates):
    for j,partnum in enumerate(all_unique_parts):
        plc_day_data[i][j] = plcdata["PartNumber"][(plcdata.Date == day) & (plcdata.PartNumber == partnum)].count()
        
# Create a DataFrame from plc_day_data for correlation with NetSuite
plc_byday_bypart = pd.DataFrame(data=plc_day_data, columns=all_unique_parts, index=plc_unique_dates)
# Reindex plc_byday_bypart to include missing dates
idx = pd.date_range('12-14-2021', '01-18-2022')
plc_byday_bypart = plc_byday_bypart.reindex(idx, fill_value=0)
plc_byday_bypart.index = plc_byday_bypart.index.date

# For each unique date, get the count of each part from Netsuite data
netsuite_day_data = np.zeros((len(netsuite_unique_dates), len(all_unique_parts)))
for i,day in enumerate(netsuite_unique_dates):
    for j,partnum in enumerate(all_unique_parts):
        netsuite_day_data[i][j] = netsuite.loc[(netsuite["Item"] == partnum) & (netsuite["Date"] == day), "Quantity"].sum()

# Create a DataFrame from netsuite_day_data for correlation with PLC
netsuite_byday_bypart = pd.DataFrame(data=netsuite_day_data, columns=all_unique_parts, index=netsuite_unique_dates)
# Reindex netsuite_byday_bypart to include missing dates
netsuite_byday_bypart = netsuite_byday_bypart.reindex(idx, fill_value=0)
netsuite_byday_bypart.index = netsuite_byday_bypart.index.date

# Get list of dates to use for plotting (only use every nth date)
datetimes = pd.DataFrame(data=netsuite_byday_bypart.index)
dates = pd.to_datetime(datetimes[0]).dt.date
unique_dates = dates.unique()
unique_dates = pd.DataFrame(data=unique_dates)
nth = 5
nth_dates = unique_dates.iloc[::nth, :]
nth_dates = list(nth_dates[0])
nth_dates_noyear = []
j = 0
for i, date in enumerate(nth_dates):
    # print("i = {}".format(i))
    # print("j = {}".format(j))
    month = date.month
    day = date.day
    daystr = str(month) + "/" + str(day)
    nth_dates_noyear.append(daystr)
    j += 1


# Plot the data for each part to see if the difference between the PLC and 
# Netsuite data lag each other relatively constantly.
columns = 4
rows = 5
fig1, ax_array = plt.subplots(rows, columns, figsize=(16,10))
plotcount = 0
for i,ax_row in enumerate(ax_array):
    for j,axes in enumerate(ax_row):
        if plotcount >= 19:
            break
        df_corr = pd.concat([plc_byday_bypart.iloc[:, plotcount], netsuite_byday_bypart.iloc[:, plotcount]], axis=1)
        overall_pearson_r = df_corr.corr().iloc[0,1]
        # print("{} overall correlation: {}".format(plc_byday_bypart.columns[plotcount], overall_pearson_r))
        
        subplot_title = "{}: r = {}".format(netsuite_byday_bypart.columns[plotcount], np.around(overall_pearson_r,2))
        axes.set_title(subplot_title)
        # axes.set_xlabel("Date")
        axes.set_ylabel("Count")
        axes.set_xticks(nth_dates)
        axes.set_xticklabels(nth_dates_noyear, rotation=45)
        axes.plot(plc_byday_bypart.index.values, plc_byday_bypart.iloc[:, plotcount])
        axes.plot(netsuite_byday_bypart.index.values, netsuite_byday_bypart.iloc[:, plotcount], alpha=0.75, color="r")
        
        # axes.legend()
        plotcount += 1

startdate = plc_byday_bypart.index.min()
enddate = plc_byday_bypart.index.max()        
fig1.suptitle("Daily Comparison of PLC and Netsuite Part Counts, {} to {} (PLC=Blue, NetSuite=Red)".format(startdate, enddate))
plt.tight_layout()