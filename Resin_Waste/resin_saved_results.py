# -*- coding: utf-8 -*-
"""
Created on Thu Nov  3 14:56:40 2022

@author: Ryan.Larson
"""

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

filename = "Lower_Resin_Use_Results.xlsx"

df = pd.read_excel(filename)

df["Part Size"] = df["Part Size"].values.astype('str')

parts_dict_current = {
    "36": 33.2,
    "48": 38.7,
    "60": 44.2,
    "72": 51.9,
    "84": 60.2,
    "96": 70.7,
    "102": 80.9    
    }

current_weight = [parts_dict_current[key] for key in df["Part Size"]]

df["Part Size"] = df["Part Size"].values.astype("int")
df["Current Weight"] = current_weight

df["Percentage"] = df["Resin Used"] / df["Current Weight"]

fig1 = plt.figure(dpi=300)
sns.scatterplot(data=df, x="Part Size", y="White Area")

fig2 = plt.figure(dpi=300)
sns.scatterplot(data=df, x="Percentage", y="White Area")

sorted_sizes = np.sort(df["Part Size"].unique())
for size in sorted_sizes:
    df_size = df[df["Part Size"] == size]
    whitecount = len(df_size[df_size["White Area"] > 0])
    totalcount = len(df_size)
    print("Size {}: {}% of parts had white spots ({} out of {} parts)".format(size, np.around(100.0*whitecount/totalcount, 2), whitecount, totalcount))
    
whitecount = len(df[df["White Area"] > 0])
totalcount = len(df)

print("\nAll Sizes: {}% of parts had white spots ({} out of {} parts)".format(np.around(100.0*whitecount/totalcount, 2), whitecount, totalcount))

white_amounts = df[df["White Area"] > 0]
avg_white = np.mean(white_amounts["White Area"])
print("\nParts that had white spots averaged {} in^2".format(np.around(avg_white,2)))