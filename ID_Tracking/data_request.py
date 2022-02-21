"""data_request.py: Practice accessing StrideLinx API
"""

import pandas as pd
import numpy as np

import requests

import api_config_vars as config
from employee_cycle_times import align_operator_times


def load_operator_data_single_mold(dtstart, dtend, moldcolor):
    """Load data for a single mold, identified by its publicID
    """
    url = config.url
    
    publicID = config.publicIds[moldcolor]
    tags = config.operator_tags[moldcolor]

    payload = {
        "source": {"publicId": publicID},
        "tags": tags,
        "start": dtstart,
        "end": dtend,
        "timeZone": "America/Denver"
    }
    headers = config.operator_headers

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

    return df

def load_operator_data(dtstart, dtend):
    """Load the data for all molds and export as a single DataFrame.
    """
    # operator_frames = []
    layup_frames = []
    close_frames = []
    resin_frames = []
    cycle_frames = []
    
    for moldcolor in config.molds:
        df_raw = load_operator_data_single_mold(dtstart, dtend, moldcolor)
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

        df_layup = align_operator_times(df_cleaned, layup_datetimes, "Layup Time",
                                        layup_inds, layup_times, lead_inds,
                                        assistant1_inds, assistant2_inds,
                                        assistant3_inds)
        df_close = align_operator_times(df_cleaned, close_datetimes, "Close Time",
                                        close_inds, close_times, lead_inds,
                                        assistant1_inds, assistant2_inds,
                                        assistant3_inds)
        df_resin = align_operator_times(df_cleaned, resin_datetimes, "Resin Time",
                                        resin_inds, resin_times, lead_inds,
                                        assistant1_inds, assistant2_inds,
                                        assistant3_inds)
        df_cycle = align_operator_times(df_cleaned, cycle_datetimes, "Cycle Time",
                                        cycle_inds, cycle_times, lead_inds,
                                        assistant1_inds, assistant2_inds,
                                        assistant3_inds)
        
        
        # operator_frames.append(df)
        layup_frames.append(df_layup)
        close_frames.append(df_close)
        resin_frames.append(df_resin)
        cycle_frames.append(df_cycle)
    
    # for publicID in config.publicIds.values():
    #     df = load_operator_data_single_mold(dtstart, dtend, publicID)
    #     operator_frames.append(df)
    
    # all_frames = pd.concat(operator_frames)
    # all_frames = all_frames.reset_index(drop=True)
    all_layup = pd.concat(layup_frames)
    all_layup = all_layup.reset_index(drop=True)
    all_close = pd.concat(close_frames)
    all_close = all_close.reset_index(drop=True)
    all_resin = pd.concat(resin_frames)
    all_resin = all_resin.reset_index(drop=True)
    all_cycle = pd.concat(cycle_frames)
    all_cycle = all_cycle.reset_index(drop=True)
    
    return all_layup, all_close, all_resin, all_cycle


if __name__ == "__main__":
    startstr = "2022-02-17T00:00:00Z"
    endstr = "2022-02-18T00:00:00Z"
    all_layup, all_close, all_resin, all_cycle = load_operator_data(startstr, endstr)
