"""data_request.py: Practice accessing StrideLinx API
"""

import pandas as pd
import numpy as np

import requests

import api_config_vars as config


def load_operator_data_single_mold(dtstart, dtend, publicID):
    """Load data for a single mold, identified by its publicID
    """
    url = config.url

    payload = {
        "source": {"publicId": publicID},
        "tags": config.operator_tags,
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

def load_operator_data(startstr, endstr):
    """Load the data for all molds and export as a single DataFrame.
    """
    df_all = pd.DataFrame()
    for publicID in config.publicIds:

            resin_frames.append(df_resin)
        cycle_frames.append(df_cycle)

    all_layup = pd.concat(layup_frames)
    all_layup = all_layup.reset_index(drop=True)


if __name__ == "__main__":
    startstr = "2022-02-17T00:00:00Z"
    endstr = "2022-02-18T00:00:00Z"
    df = load_operator_data(startstr, endstr)
