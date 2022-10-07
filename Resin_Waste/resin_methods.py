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
    
    # Convert to the relevant data types
    for i,col in enumerate(df.columns):
        if col == "time":
            df[col] = pd.to_datetime(df[col])
        else:
            df[col] = df[col].astype(float)
            
    # Remove the last row that is filled with nan
    df = df.dropna()
    
    df = verify_nominals(df, resincolor)
    
    # Update "additional resin" part numbers to use the total resin weight
    # as the excess resin value instead of the overshoot of the nominal weight
    updated_excess_resin = []
    partnum1_name = resincolor + " - 1st Part Number"
    resin_weight = resincolor + " - Resin Weight"
    for i in range(len(df)):
        updated_excess_resin.append(df.loc[i,resin_weight] - df.loc[i,"True Nominal Resin Weight"])
    # excess_resin_weight = resincolor + " - Excess Resin Weight"
    # for i in range(len(df)):
    #     if df.loc[i,partnum1_name] == 1111:
    #         updated_excess_resin.append(df.loc[i,resin_weight])
    #     else:
    #         updated_excess_resin.append(df.loc[i,excess_resin_weight])
            
    colname = resincolor + " - Updated Excess Resin Weight"
    df[colname] = updated_excess_resin
    
    # Find outliers in excess resin, using updated excess resin weight column
    outlier_bool = []
    Q1 = df[colname].quantile(0.25)
    Q3 = df[colname].quantile(0.75)
    IQR = Q3 - Q1
    for i in range(len(df)):
        if df.loc[i,colname] < (Q1-1.5*IQR) or df.loc[i,colname] > (Q3+1.5*IQR):
            outlier_bool.append(True)
        else:
            outlier_bool.append(False)
            
    df["Outlier"] = outlier_bool
    
    df_no_outliers = df[~((df[colname]<(Q1-1.5*IQR)) | (df[colname]>(Q3+1.5*IQR)))]
    
    n_outliers = len(df) - len(df_no_outliers)
    
    median_excess = np.median(df_no_outliers[colname])
    mean_excess = np.mean(df_no_outliers[colname])
    
    impute_median = []
    impute_mean = []
    for i in range(len(df)):
        if df.loc[i,"Outlier"] == True:
            impute_median.append(median_excess)
            impute_mean.append(mean_excess)
        else:
            impute_median.append(df.loc[i,colname])
            impute_mean.append(df.loc[i,colname])
            
    df["Excess Resin - Median Imputed"] = impute_median
    df["Excess Resin - Mean Imputed"] = impute_mean
            
    return df, df_no_outliers, n_outliers, median_excess


def verify_nominals(df, resincolor):
    # Use standard part weights to determine excess resin
    true_nominal = []
    
    wtgt = 1.0  # Target weight for the product
    part1col = "{} - 1st Part Number".format(resincolor)
    part2col = "{} - 2nd Part Number".format(resincolor)
    for ind in df.index:
        num1 = int(df[part1col][ind])
        num2 = int(df[part2col][ind])
        if num1 == 664436:
            wtgt = 33.2
        elif num1 == 664448:
            wtgt = 38.7
        elif num1 == 664460:
            wtgt = 44.2
        elif num1 == 664472:
            wtgt = 51.9
        elif num1 == 664484:
            wtgt = 60.2
        elif num1 == 664496:
            wtgt = 70.7
        elif num1 == 6644102:
            wtgt = 80.9
        elif num1 == 422324 and num2 == 0:
            wtgt = 7.8
        elif num1 == 422336 and num2 == 0:
            wtgt = 12.2
        elif num1 == 422348 and num2 == 0:
            wtgt = 17.6
        elif num1 == 422324 and num2 == 422324:
            wtgt = 15.6
        elif num1 == 422324 and num2 == 422336:
            wtgt = 20.0
        elif num1 == 422324 and num2 == 422348:
            wtgt = 25.4
        elif num1 == 422336 and num2 == 422324:
            wtgt = 15.6
        elif num1 == 422336 and num2 == 422336:
            wtgt = 24.4
        elif num1 == 422336 and num2 == 422348:
            wtgt = 29.8
        elif num1 == 422348 and num2 == 422324:
            wtgt = 25.4
        elif num1 == 422348 and num2 == 422336:
            wtgt = 29.8
        elif num1 == 422348 and num2 == 422348:
            wtgt = 35.2
        elif num1 == 422360:
            wtgt = 25.0
        elif num1 == 422372:
            wtgt = 41.5
        elif num1 == 422380:
            wtgt = 46.0
        elif num1 == 1111:
            wtgt = 0.0
        else:
            excess_resin_col = "{} - Excess Resin Weight".format(resincolor)
            wtgt = df[excess_resin_col][ind]
            # print("ERROR: PRODUCT NUMBER NOT RECOGNIZED")
            
        true_nominal.append(wtgt)
        
    df["True Nominal Resin Weight"] = true_nominal
    
    return df

def resin_use_plots(df, resincolor):
    """
    

    Parameters
    ----------
    dtstart : TYPE
        DESCRIPTION.
    dtend : TYPE
        DESCRIPTION.
    resincolor : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    # df = load_resin_data_single_plc(dtstart, dtend, resincolor)
    
    sns.set_theme(style="whitegrid")
    customPalette = sns.light_palette("lightblue", 10)
    flierprops = dict(marker='o', markerfacecolor='None', markersize=4)
    partnum1_name = resincolor + " - 1st Part Number"
    partnum2_name = resincolor + " - 2nd Part Number"
    excess_resin_name = resincolor + " - Excess Resin Weight"
    extra_resin_reason_name = resincolor + " - Extra Resin Reason"
    
    plt.figure(figsize=(15,8), dpi=300)
    ax = sns.boxplot(x=df[partnum1_name], y=df[excess_resin_name], flierprops=flierprops, palette=customPalette)
    ax.set_xticklabels(ax.get_xticklabels(),rotation = 30)
    plt.title("Excess Resin by 1st Part Number - {}".format(resincolor))
    plt.ylabel("Excess Resin (lbs)")
    # plt.xlabel("")
    
    
def resin_over_time(df, resincolor):
    tstart = min(df.time)
    tend = max(df.time)
    monthstart = tstart.strftime("%B")
    monthend = tend.strftime("%B")
    timesince = df.time - tstart
    timesince_days = timesince / pd.to_timedelta(1, unit='D')
    df["Days Since {}".format(tstart)] = timesince_days
    
    if monthstart == monthend:
        sns.lmplot(x="Days Since {}".format(tstart), y=resincolor + " - Updated Excess Resin Weight", data=df, fit_reg=False, hue="Outlier").set(title="{} Excess Resin for {}".format(resincolor, monthstart))
        sns.lmplot(x="Days Since {}".format(tstart), y="Excess Resin - Median Imputed", data=df, fit_reg=False, hue="Outlier").set(title="{} Excess Resin for {} - Outlier Filtered".format(resincolor, monthstart))
    else:
        sns.lmplot(x="Days Since {}".format(tstart), y=resincolor + " - Updated Excess Resin Weight", data=df, fit_reg=False, hue="Outlier").set(title="{} Excess Resin for {} to {}".format(resincolor, monthstart, monthend))
        sns.lmplot(x="Days Since {}".format(tstart), y="Excess Resin - Median Imputed", data=df, fit_reg=False, hue="Outlier").set(title="{} Excess Resin for {} to {}- Outlier Filtered".format(resincolor, monthstart, monthend))
        
    # sns.lmplot(x="Days Since {}".format(t0), y="Excess Resin - Mean Imputed", data=df, fit_reg=False, hue="Outlier")
    
    

if __name__ == "__main__":
    months = [4,5,6,7,8,9]
    lastdays = [30,31,30,31,31,30]
    
    tot_excess_raw = []
    tot_excess_filtered = []
    tot_excess_impute = []
    avg_excess_raw = []
    avg_excess_filtered = []
    avg_excess_impute = []
    
    for idx,month in enumerate(months):
        dtstart = dt.datetime(2022,month,1,0,0,0)
        # enddate = dt.date.today()
        enddate = dt.date(2022,month,lastdays[idx])
        endtime = dt.time(23,59,59)
        dtend = dt.datetime.combine(enddate, endtime)
        monthstart = dtstart.strftime("%B")
        monthend = dtend.strftime("%B")
        
        total_excess_resin_raw = []
        total_excess_resin_filtered = []
        total_excess_resin_imputed = []
        n_parts = []
        n_over = []
        median_excesses = []
        n_outliers_all = []
        
        resincolors = ["Tan", "Gray"]
        for i,resincolor in enumerate(resincolors):
            df, df_no_outliers, n_outliers, median_excess = load_resin_data_single_plc(dtstart, dtend, resincolor)
            n_outliers_all.append(n_outliers)
            median_excesses.append(median_excess)
            # resin_over_time(df, resincolor)
            
            excess_col = resincolor + " - Updated Excess Resin Weight"
            total_excess_resin_raw.append(df[excess_col].sum())
            total_excess_resin_filtered.append(df_no_outliers[excess_col].sum())
            
            excess_median_col = "Excess Resin - Median Imputed"
            total_excess_resin_imputed.append(df[excess_median_col].sum())
            
            col_1stpartnum = "{} - 1st Part Number".format(resincolor)
            df_parts = df[~(df[col_1stpartnum]==1111)]
            n_parts.append(len(df_parts))
            df_additional = df[(df[col_1stpartnum]==1111)]
            df_over = df_parts[(df[excess_median_col]>0)]
            
            n_over.append(len(df_over) + len(df_additional)) # Assumes any time you get additional resin it's going over the amount specified
            # over_pct.append(100.0 * n_over/len(df_parts)
            
        
        print("\n##############################")
        if monthstart == monthend:
            print("Total Excess Resin - {}".format(monthstart))
        else:
            print("Total Excess Resin - {} to {}".format(monthstart, monthend))
        print("##############################")
        print("Raw Data:\t{}".format(sum(total_excess_resin_raw)))
        print("Imputed Data:\t{}".format(sum(total_excess_resin_imputed)))
        print("Avg Excess Per Part (Raw):\t{} lbs".format(np.around(sum(total_excess_resin_raw)/sum(n_parts), 2)))
        print("Avg Excess Per Part (Imputed):\t{} lbs".format(np.around(sum(total_excess_resin_imputed)/sum(n_parts), 2)))
        
        over_pct = 100.0 * (sum(n_over)/sum(n_parts))
        print("\nEstimated Parts Using Excess Resin:\t{} ({}%)".format(sum(n_over), np.around(over_pct,1)))
        print("Median Excesses Used for Imputing:\t{}".format({"Tan": median_excesses[0], "Gray": median_excesses[1]}))
        print("N Outliers in Raw Data:\t{}".format(sum(n_outliers_all)))
        
        print("\nTotal Tan Parts:\t{}".format(n_parts[0]))
        print("Total Gray Parts:\t{}".format(n_parts[1]))

        tot_excess_raw.append(sum(total_excess_resin_raw))
        tot_excess_filtered.append(sum(total_excess_resin_filtered))
        tot_excess_impute.append(sum(total_excess_resin_imputed))
        avg_excess_raw.append(np.around(sum(total_excess_resin_raw)/sum(n_parts), 2))
        avg_excess_filtered.append(np.around(sum(total_excess_resin_filtered)/sum(n_parts), 2))
        avg_excess_impute.append(np.around(sum(total_excess_resin_imputed)/sum(n_parts), 2))
        
    # Plot totals and averages per month over time
    plt.figure(dpi=300)
    plt.plot(months,tot_excess_raw,label="Total Excess Resin (Raw)")
    plt.plot(months,tot_excess_filtered,label="Total Excess Resin (Outlier-Filtered)")
    plt.plot(months,tot_excess_impute,label="Total Excess Resin (Imputed)")
    plt.title("Total Excess Resin By Month")
    plt.legend()
    
    plt.figure(dpi=300)
    plt.plot(months,avg_excess_raw,label="Average Excess Resin (Raw)")
    plt.plot(months,avg_excess_filtered,label="Average Excess Resin (Outlier-Filtered)")
    plt.plot(months,avg_excess_impute,label="Average Excess Resin (Imputed)")
    plt.title("Average Excess Resin Per Part By Month")
    plt.legend()
    