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
import api_config_vars_resin as api_resin
import matplotlib.pyplot as plt
import seaborn as sns
import math
import meteostat as mst
from sklearn.preprocessing import scale
from sklearn.model_selection import RepeatedKFold
from sklearn.decomposition import PCA
from sklearn import model_selection
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

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



def associate_time(df, colname):
    """
    
    
    Parameters
    ----------
    df : TYPE
        DESCRIPTION.
    cyc_ind : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    mask = df[colname].notna()
    times = df["time"][mask]
    stage = df[colname][mask]
    df_stage = pd.concat([times,stage], axis=1)
    # df_stage = df_stage.reset_index(drop=True)
    
    return df_stage


def get_bag_dfs(df):
    bag_starts = get_bag_start_times(df)
    # bag_starts = get_bag_start_times_data_ref(df)
    # Catch duplicate occurrences of bag numbers
    bag_starts = bag_starts[(bag_starts.ne(bag_starts.shift())).any(axis=1)]
    bag_starts = bag_starts.reset_index(drop=True)
    bag_dfs = []
    for i in range(len(bag_starts)):
        if i == len(bag_starts)-1:
            time_min = bag_starts.loc[i,"Start Time"]
            df_bag = df[(df["time"] > time_min)]
        else:
            time_min = bag_starts.loc[i,"Start Time"]
            time_max = bag_starts.loc[i+1,"Start Time"]
            df_bag = df[(df["time"] > time_min) & (df["time"] < time_max)]
        if df_bag["Bag"].isnull().all():
            pass
        else:
            bag_dfs.append(df_bag)
        
    # mask = df[(df["time"] > time_min) & (df["time"] < time_max)]
    
    return bag_dfs

def combine_bag_dfs(bag_dfs_collapsed):
    combined_bag_dfs = pd.concat(bag_dfs_collapsed)
    combined_bag_dfs = combined_bag_dfs.sort_values("time")
    combined_bag_dfs = combined_bag_dfs.reset_index(drop=True)
    return combined_bag_dfs
    
def clean_consecutive_duplicates(combined_bag_dfs):
    a = combined_bag_dfs.copy()
    b = a[["Layup Time", "Close Time", "Resin Time", "Cycle Time", "Bag"]].copy()
    c = a[(b.ne(b.shift())).any(axis=1)]
    return c
    
def collapse_df_bag(df_bag):
    df_layup = associate_time(df_bag, "Layup Time")
    df_close = associate_time(df_bag, "Close Time")
    df_resin = associate_time(df_bag, "Resin Time")
    df_cycle = associate_time(df_bag, "Cycle Time")
    cycle_inds = list(df_cycle.index.values)
    
    
    layup = list(np.zeros((len(df_cycle),1)))
    close = list(np.zeros((len(df_cycle),1)))
    resin = list(np.zeros((len(df_cycle),1)))
    for i in range(len(df_cycle)):
        idx_cycle = cycle_inds[i]
        
        if len(df_layup["time"]) > 0:
            idx_layup = df_layup["time"].sub(df_cycle.loc[idx_cycle,"time"]).abs().idxmin()
            layup[i] = df_layup.loc[idx_layup,"Layup Time"]
        else:
            layup[i] = 0
        
        if len(df_close["time"]) > 0:
            idx_close = df_close["time"].sub(df_cycle.loc[idx_cycle,"time"]).abs().idxmin()
            close[i] = df_close.loc[idx_close,"Close Time"]
        else:
            close[i] = 0
            
        if len(df_resin["time"]) > 0:
            idx_resin = df_resin["time"].sub(df_cycle.loc[idx_cycle,"time"]).abs().idxmin()
            resin[i] = df_resin.loc[idx_resin,"Resin Time"]
        else:
            resin[i] = 0
        
    
    time = list(df_cycle["time"])
    cycle = list(df_cycle["Cycle Time"])
    bagnum = df_bag["Bag"].value_counts().index.tolist()[0]
    bagnum_col = list(bagnum * np.ones(len(df_cycle)))
    
    collapsed = {"time":time, "Layup Time":layup, "Close Time":close,
                 "Resin Time":resin, "Cycle Time":cycle, "Bag": bagnum_col}
    df_bag_collapsed = pd.DataFrame(collapsed)
    # add_bag_days(df_bag_collapsed)
    
    # df_bag_collapsed["Sum"] = df_bag_collapsed["Layup Time"] + df_bag_collapsed["Close Time"] + df_bag_collapsed["Resin Time"]
    # df_bag_collapsed["Diff"] = df_bag_collapsed["Cycle Time"] - df_bag_collapsed["Sum"]
    
    return df_bag_collapsed
        


def get_bag_start_times_data_ref(df):
    df_bag = associate_time(df, "Bag")
    df_bag = df_bag.sort_values("time")
    df_bag = df_bag.reset_index(drop=True)
    # bagnums = list(df_bags["Bag"].unique())
    bagnums = []
    bag_timestamps = []
    # for bag in bagnums:
    #     bag_slice = df_bags[df_bags["Bag"] == bag]
    #     bag_timestamps.append(bag_slice["time"].min())
    for i in range(len(df_bag)):
        if i == 0:
            bag_timestamps.append(df_bag.loc[i,"time"])
            bagnums.append(df_bag.loc[i,"Bag"])
        else:
            if df_bag.loc[i,"Bag"] != df_bag.loc[i-1,"Bag"]:
                bag_timestamps.append(df_bag.loc[i,"time"])
                bagnums.append(df_bag.loc[i,"Bag"])
        
    bag_starts = pd.DataFrame({"Bag":bagnums, "Start Time":bag_timestamps})
    
    # Compare against equipment data for bags
    bag_data = pd.read_excel(data_assets.equip_data)
    for i,bag in enumerate(bag_starts["Bag"]):
        row = bag_data.loc[bag_data["Bag"] == bag]
        if pd.notnull(row.loc[row.index[0],"Built"]):
            date = row.loc[row.index[0],"Built"]
            bag_starts.loc[i,"Start Time"] = date
    
    bag_starts = bag_starts.sort_values("Start Time",ignore_index=True)
        
    return bag_starts

def get_bag_start_times(df):
    df_bag = associate_time(df, "Bag")
    df_bag = df_bag.sort_values("time")
    df_bag = df_bag.reset_index(drop=True)
    bagnums = list(df_bag["Bag"].unique())
    # bagnums = []
    bag_timestamps = []
    for bag in bagnums:
        bag_slice = df_bag[df_bag["Bag"] == bag]
        bag_timestamps.append(bag_slice["time"].min())
        
    bag_starts = pd.DataFrame({"Bag":bagnums, "Start Time":bag_timestamps})
    bag_starts = bag_starts.sort_values("Start Time",ignore_index=True)
    return bag_starts

def add_bag_days_cycles(df):
    bag_starts = get_bag_start_times_data_ref(df)
    
    # Clean out duplicate bag numbers and replace with bag creation date data
    bag_starts = bag_starts.drop_duplicates("Bag")
    bag_starts = bag_starts.sort_values("Start Time",ignore_index=True)
    
    # Compare against equipment data for bags
    bag_data = pd.read_excel(data_assets.equip_data)
    for i,bag in enumerate(bag_starts["Bag"]):
        row = bag_data.loc[bag_data["Bag"] == bag]
        if pd.notnull(row.loc[row.index[0],"Built"]):
            date = row.loc[row.index[0],"Built"]
            bag_starts.loc[i,"Start Time"] = date
    
    bag_starts = bag_starts.sort_values("Start Time",ignore_index=True)
    
    frames = []
    
    for i,bag in enumerate(bag_starts["Bag"]):
        # Slice the full dataframe to just the current bag
        df_bag = df.loc[df["Bag"] == bag]
        # Calculate dates based on basedate found in bag_starts
        row = bag_starts.loc[bag_starts["Bag"] == bag]
        basedate = row.loc[row.index[0],"Start Time"]
        df_bag["Bag Days"] = (df_bag["time"] - basedate).dt.days
        
        # Use index to add cycle count
        df_bag = df_bag.sort_values("time",ignore_index=True)
        df_bag["Bag Cycles"] = df_bag.index
        
        frames.append(df_bag)
    
    df_combine = pd.concat(frames)
    df_combine = df_combine.sort_values("time",ignore_index=True)
    
    # basedate = df["time"].min()
    # basedate = basedate.date()
    # basedate = dt.datetime.combine(basedate, dt.datetime.min.time())
    # df["Bag Days"] = (df["time"] - basedate).dt.days
    return df_combine, bag_starts


def get_cleaned_single_mold(df):
    bag_dfs = get_bag_dfs(df)
    bag_dfs_collapsed = []
    for bag in bag_dfs:
        df_bag_collapsed = collapse_df_bag(bag)
        bag_dfs_collapsed.append(df_bag_collapsed)
        
    combined_bag_dfs = combine_bag_dfs(bag_dfs_collapsed)
    cleaned_df = clean_consecutive_duplicates(combined_bag_dfs)
    return cleaned_df


def get_all_bag_data(dtstart, dtend):
    frames = []
    for moldcolor in api.molds:
        df = load_bag_data_single_mold(dtstart, dtend, moldcolor)
        cleaned_df = get_cleaned_single_mold(df)
        frames.append(cleaned_df)
        
    all_bag_data = pd.concat(frames)
    
    # Sort and reindex
    all_bag_data = all_bag_data.sort_values("time", ignore_index=True)
    
    
    # Add bag days and validation columns
    all_bag_data, bag_starts = add_bag_days_cycles(all_bag_data)
    
    all_bag_data["Sum"] = all_bag_data["Layup Time"] + all_bag_data["Close Time"] + all_bag_data["Resin Time"]
    all_bag_data["Diff"] = all_bag_data["Cycle Time"] - all_bag_data["Sum"]
    
    return all_bag_data, bag_starts

def filter_unsaturated_data(all_bag_data):
    layup_unsaturated = all_bag_data.loc[(all_bag_data["Layup Time"] != 276.0) & (all_bag_data["Layup Time"] != 275.0)]
    close_unsaturated = layup_unsaturated.loc[layup_unsaturated["Close Time"] != 90.0]
    resin_unsaturated = close_unsaturated.loc[close_unsaturated["Resin Time"] != 180.0]
    return resin_unsaturated

def analyze_by_bag_list(bag_list):
    # Find the earliest bag creation date in the data set
    choose_date = dt.date.today()
    enddate = dt.date.today()    
    endtime = dt.time(23,59,59)
    dtend = dt.datetime.combine(enddate, endtime)
    choose_date = dt.datetime.combine(choose_date, endtime)
    
    bag_data = pd.read_excel(data_assets.equip_data)
    for bag in bag_list:
        # Select row where bag is present
        row = bag_data.loc[bag_data["Bag"] == bag]
        check_date = row.loc[int(bag), "Built"]
        
        if check_date < choose_date:
            choose_date = check_date
            
    # Access data and filter it down to the bags of interest
    all_bag_data, bag_starts = get_all_bag_data(choose_date, dtend)
    
    all_bag_data["Bag"] = all_bag_data["Bag"].astype(int)
    
    selected_bag_data = all_bag_data[all_bag_data["Bag"].isin(bag_list)]
    selected_bag_data_unsaturated = filter_unsaturated_data(selected_bag_data)
    
    return selected_bag_data, selected_bag_data_unsaturated
    

def break_out_by_bag(selected_bag_data):
    bag_list = list(selected_bag_data["Bag"].unique())
    frames = []
    for bag in bag_list:
        frames.append(selected_bag_data[selected_bag_data["Bag"] == bag])
    
    return frames


def plot_rolling_avg(selected_bag_data, nobs):
    frames = break_out_by_bag(selected_bag_data)
    # nobs = 50
    
    for frame in frames:
        frame["Layup Avg"] = frame["Layup Time"].rolling(nobs).mean()
        frame["Close Avg"] = frame["Close Time"].rolling(nobs).mean()
        frame["Resin Avg"] = frame["Resin Time"].rolling(nobs).mean()
        frame["Cycle Avg"] = frame["Cycle Time"].rolling(nobs).mean()
        
    # Recombine the dataframes
    df = pd.concat(frames)
    df.sort_values("time",ignore_index=True)
    
    # Plot rolling averages for stage times against number of cycles
    plt.figure(dpi=300)
    sns.lineplot(data=df, x="Bag Cycles", y="Layup Avg", hue="Bag", palette="Paired")
    plt.title("Rolling Average - {} Samples".format(nobs))
    plt.figure(dpi=300)
    sns.lineplot(data=df, x="Bag Cycles", y="Close Avg", hue="Bag", palette="Paired")
    plt.title("Rolling Average - {} Samples".format(nobs))
    plt.figure(dpi=300)
    sns.lineplot(data=df, x="Bag Cycles", y="Resin Avg", hue="Bag", palette="Paired")
    plt.title("Rolling Average - {} Samples".format(nobs))
    plt.figure(dpi=300)
    sns.lineplot(data=df, x="Bag Cycles", y="Cycle Avg", hue="Bag", palette="Paired")
    plt.title("Rolling Average - {} Samples".format(nobs))
    
    plt.figure(dpi=300)
    sns.lineplot(data=df, x="Bag Days", y="Layup Avg", hue="Bag", palette="Paired")
    plt.title("Rolling Average - {} Samples".format(nobs))
    plt.figure(dpi=300)
    sns.lineplot(data=df, x="Bag Days", y="Close Avg", hue="Bag", palette="Paired")
    plt.title("Rolling Average - {} Samples".format(nobs))
    plt.figure(dpi=300)
    sns.lineplot(data=df, x="Bag Days", y="Resin Avg", hue="Bag", palette="Paired")
    plt.title("Rolling Average - {} Samples".format(nobs))
    plt.figure(dpi=300)
    sns.lineplot(data=df, x="Bag Days", y="Cycle Avg", hue="Bag", palette="Paired")
    plt.title("Rolling Average - {} Samples".format(nobs))
    
    plt.figure(dpi=300)
    sns.lineplot(data=df, x="time", y="Layup Avg", hue="Bag", palette="Paired")
    plt.title("Rolling Average - {} Samples".format(nobs))
    plt.figure(dpi=300)
    sns.lineplot(data=df, x="time", y="Close Avg", hue="Bag", palette="Paired")
    plt.title("Rolling Average - {} Samples".format(nobs))
    plt.figure(dpi=300)
    sns.lineplot(data=df, x="time", y="Resin Avg", hue="Bag", palette="Paired")
    plt.title("Rolling Average - {} Samples".format(nobs))
    plt.figure(dpi=300)
    sns.lineplot(data=df, x="time", y="Cycle Avg", hue="Bag", palette="Paired")
    plt.title("Rolling Average - {} Samples".format(nobs))
    
    return df

def temperature_effects(bag_list):
    selected_bag_data, selected_bag_data_unsaturated = analyze_by_bag_list(bag_list)
    
    # Set time period based on the selected bags
    start = selected_bag_data_unsaturated["time"].min().to_pydatetime()
    end = selected_bag_data_unsaturated["time"].max().to_pydatetime()
    
    # Set location parameters
    location_lat = 40.184319
    location_long = -111.624710
    
    # Get the nearest meteorlogical station
    stations = mst.Stations()
    stations = stations.nearby(location_lat, location_long)
    station = stations.fetch(1)
    station_id = station.index[0]
    
    # Get hourly data between start and end
    weather_data = mst.Hourly(station_id, start, end)
    weather_data = weather_data.fetch()
    
    dfcopy = selected_bag_data_unsaturated.copy()
    weather_data = (pd.concat([weather_data, pd.DataFrame(index=dfcopy.time)]).sort_index(kind='stable', ignore_index=False))
    weather_data["temp"] = weather_data["temp"].interpolate()
    
    def celsius_to_fahrenheit(x):
        return (x*1.8)+32
    
    weather_data["temp"] = weather_data["temp"].apply(celsius_to_fahrenheit)
    weather_data.loc[weather_data.index[0],"temp"] = weather_data.loc[weather_data.index[1],"temp"]
    
    list_indices = list(dfcopy["time"])
    weather_data.reset_index(inplace=True)
    
    dfcopy.reset_index(drop=True, inplace=True)
    
    dfcopy["temp"] = list(weather_data["temp"].loc[weather_data["time"].isin(list_indices)])
    
    return dfcopy, weather_data
    

def bag_PCA(selected_bag_data_unsaturated, bag_list, independent_list, dependent_list):
    frames = []
    for bag in bag_list:
        frames.append(selected_bag_data_unsaturated[selected_bag_data_unsaturated["Bag"]==bag])
        
    for i,frame in enumerate(frames):
        print("\n############################################")
        print("Bag:\t{}".format(bag_list[i]))
        print("############################################")
        X = frame[independent_list]
        y = frame[dependent_list]
        
        pca = PCA()
        X_reduced = pca.fit_transform(scale(X))
        
        # define cross validation method
        cv = RepeatedKFold(n_splits=10, n_repeats=3, random_state=1)

        regr = LinearRegression()
        mse = []

        # Calculate MSE (mean squared error) with only the intercept
        score = -1*model_selection.cross_val_score(regr, np.ones((len(X_reduced),1)), y, cv=cv, scoring='neg_mean_squared_error').mean()
        mse.append(score)

        # Calculate MSE using cross-validation, adding one component at a time
        for i in np.arange(1, 6):
            score = -1*model_selection.cross_val_score(regr, X_reduced[:, :i], y, cv=cv, scoring='neg_mean_squared_error').mean()
            mse.append(score)
            
        # Plot cross-validation results
        plt.plot(mse)
        plt.xlabel("Number of Principal Components")
        plt.ylabel("MSE")
        # plt.title("hp")

        # The plot displays the number of principal components along the x-axis and the
        # test MSE (mean squared error) along the y-axis.

        # From the plot we can see that the test MSE decreases by adding in two
        # principal components, yet it begins to increase as we add more than two
        # principal components. Thus, the optimal model includes just the first two
        # principal components.

        # We can also use the following code to calculate the percentage of variance in
        # the response variable explained by adding in each principal component to the
        # model:
        pct_variance = np.cumsum(np.round(pca.explained_variance_ratio_, decimals=4)*100)
        print("% Variance in response explained by adding each principal component: {}".format(pct_variance))
        print("i.e. PC1 explains {}% of response variance".format(pct_variance[0]))
        
        # Number of rows in pca.components_ is the number of principal components.
        # Number of columns in pca.components_ is the number of features
        print("\nPrincipal components: \n{}".format(abs(pca.components_)))
        # Example result is below:
        # [[ 0.52106591  0.26934744  0.5804131   0.56485654]
        #  [ 0.37741762  0.92329566  0.02449161  0.06694199]]
        # Looking at PC1:
        # [ 0.52106591  0.26934744  0.5804131   0.56485654]
        # Features 1, 3, and 4 are most important for PC1
    
def all_bags_PCA(selected_bag_data_unsaturated, independent_list, dependent_list):
    print("\n############################################")
    print("PCA all bags:")
    print("############################################")
    X = selected_bag_data_unsaturated[independent_list]
    y = selected_bag_data_unsaturated[dependent_list]
    
    pca = PCA()
    X_reduced = pca.fit_transform(scale(X))
    
    # define cross validation method
    cv = RepeatedKFold(n_splits=10, n_repeats=3, random_state=1)

    regr = LinearRegression()
    mse = []

    # Calculate MSE (mean squared error) with only the intercept
    score = -1*model_selection.cross_val_score(regr, np.ones((len(X_reduced),1)), y, cv=cv, scoring='neg_mean_squared_error').mean()
    mse.append(score)

    # Calculate MSE using cross-validation, adding one component at a time
    for i in np.arange(1, 6):
        score = -1*model_selection.cross_val_score(regr, X_reduced[:, :i], y, cv=cv, scoring='neg_mean_squared_error').mean()
        mse.append(score)
        
    # Plot cross-validation results
    plt.plot(mse)
    plt.xlabel("Number of Principal Components")
    plt.ylabel("MSE")
    # plt.title("hp")

    # The plot displays the number of principal components along the x-axis and the
    # test MSE (mean squared error) along the y-axis.

    # From the plot we can see that the test MSE decreases by adding in two
    # principal components, yet it begins to increase as we add more than two
    # principal components. Thus, the optimal model includes just the first two
    # principal components.

    # We can also use the following code to calculate the percentage of variance in
    # the response variable explained by adding in each principal component to the
    # model:
    pct_variance = np.cumsum(np.round(pca.explained_variance_ratio_, decimals=4)*100)
    print("% Variance in response explained by adding each principal component: {}".format(pct_variance))
    print("i.e. PC1 explains {}% of response variance".format(pct_variance[0]))
    
    # Number of rows in pca.components_ is the number of principal components.
    # Number of columns in pca.components_ is the number of features
    print("\nPrincipal components: \n{}".format(abs(pca.components_)))
    # Example result is below:
    # [[ 0.52106591  0.26934744  0.5804131   0.56485654]
    #  [ 0.37741762  0.92329566  0.02449161  0.06694199]]
    # Looking at PC1:
    # [ 0.52106591  0.26934744  0.5804131   0.56485654]
    # Features 1, 3, and 4 are most important for PC1
    
    

if __name__ == "__main__":
    # dtstart = dt.datetime(2022,9,25,0,0,0)
    # enddate = dt.date.today()
    # # enddate = dt.date(2022,3,17)
    # endtime = dt.time(23,59,59)
    # dtend = dt.datetime.combine(enddate, endtime)
    
    # all_bag_data, bag_starts = get_all_bag_data(dtstart, dtend)
    
    # all_bag_data_unsaturated = filter_unsaturated_data(all_bag_data)
    start_bag = 10
    end_bag = 19
    bag_list = list(range(start_bag, end_bag+1))
    selected_bag_data, selected_bag_data_unsaturated = analyze_by_bag_list(bag_list)
    
    dfcopy, weather_data = temperature_effects(bag_list)
    
    independent_list = ["temp", "Bag Days", "Bag Cycles"]
    dependent_list = ["Resin Time"]
    # bag_PCA(dfcopy, bag_list, independent_list, dependent_list)
    all_bags_PCA(dfcopy, independent_list, dependent_list)
    
    plt.figure(dpi=300)
    sns.scatterplot(data=dfcopy, x="temp", y="Close Time")
    plt.figure(dpi=300)
    sns.scatterplot(data=dfcopy, x="temp", y="Resin Time")
    
    nobs = 50
    selected_bag_data_unsaturated = plot_rolling_avg(selected_bag_data_unsaturated, nobs)
    # frames = break_out_by_bag(selected_bag_data)
    
    plt.figure(dpi=300)
    sns.scatterplot(data=selected_bag_data_unsaturated, x="Bag Cycles", y="Layup Time", hue="Bag", palette="Paired")
    plt.figure(dpi=300)
    sns.scatterplot(data=selected_bag_data_unsaturated, x="Bag Cycles", y="Close Time", hue="Bag", palette="Paired")
    plt.figure(dpi=300)
    sns.scatterplot(data=selected_bag_data_unsaturated, x="Bag Cycles", y="Resin Time", hue="Bag", palette="Paired")
    plt.figure(dpi=300)
    sns.scatterplot(data=selected_bag_data_unsaturated, x="Bag Cycles", y="Cycle Time", hue="Bag", palette="Paired")
    
    plt.figure(dpi=300)
    sns.scatterplot(data=selected_bag_data_unsaturated, x="Bag Days", y="Layup Time", hue="Bag", palette="Paired")
    plt.figure(dpi=300)
    sns.scatterplot(data=selected_bag_data_unsaturated, x="Bag Days", y="Close Time", hue="Bag", palette="Paired")
    plt.figure(dpi=300)
    sns.scatterplot(data=selected_bag_data_unsaturated, x="Bag Days", y="Resin Time", hue="Bag", palette="Paired")
    plt.figure(dpi=300)
    sns.scatterplot(data=selected_bag_data_unsaturated, x="Bag Days", y="Cycle Time", hue="Bag", palette="Paired")
    
    
    
    # df = load_bag_data_single_mold(dtstart, dtend, "Pink")
    # cleaned_df = get_cleaned_single_mold(df)
    
    # cycles = associate_time(df, "Cycle Time")
    # bag_timestamps = get_bag_start_times_data_ref(df)
    
    # bag_dfs = get_bag_dfs(df)
    # bag_dfs_collapsed = []
    # for bag in bag_dfs:
    #     df_bag_collapsed = collapse_df_bag(bag)
    #     bag_dfs_collapsed.append(df_bag_collapsed)
        
    # combined_bag_dfs = combine_bag_dfs(bag_dfs_collapsed)
    # cleaned_bag_dfs = clean_consecutive_duplicates(combined_bag_dfs)
    # bags = associate_time(df, "Bag")
    # add_bag_days(cycles)
    
    
    
    # df_equip = organize_bag_data(dtstart, dtend)
    
    # df_equip_unsaturated = df_equip[df_equip["Saturated Time"] == False]
    # bagnums = df_equip_unsaturated["Bag"].unique()
    # bag_dataframes = []
    # rollnum = 20
    # for bagnum in bagnums:
    #     df_bag = df_equip_unsaturated[df_equip_unsaturated["Bag"] == bagnum]
    #     df_bag["SMA"] = df_bag["Cycle Time"].rolling(rollnum).mean()
    #     bag_dataframes.append(df_bag)
        
    #     plt.figure()
    #     sns.scatterplot(data=df_bag, x="time", y="Cycle Time")
    #     sns.lineplot(data=df_bag, x="time", y="SMA", color="r").set(title="Bag {}".format(int(bagnum)))
        
    # # correlate_bag_cycles(df_equip)
    
    
    # # sweepwindow = 100
    # # # stdev_over_time(df_equip, sweepwindow)
    # # # avg_over_time(df_equip, sweepwindow)
    # # boxplot_over_time(df_equip, sweepwindow)