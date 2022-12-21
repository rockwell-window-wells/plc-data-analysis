# -*- coding: utf-8 -*-
"""
Created on Tue Dec 20 09:22:44 2022

@author: Ryan.Larson
"""

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import resin_ttest_experiments as rtt

filename = "Less_Resin_Data.xlsx"

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

df["Percentage"] = df["Resin Amount"] / df["Current Weight"]

df["Round"] = np.around(df["Percentage"],2)

treatment = ["Less" if x < 0.99 else "Standard" for x in df["Round"]]
df["Treatment"] = treatment




# df36 = df[df["Part Size"] == 36]
# df48 = df[df["Part Size"] == 48]
df60 = df[df["Part Size"] == 60]
df72 = df[df["Part Size"] == 72]
# df84 = df[df["Part Size"] == 84]
# df96 = df[df["Part Size"] == 96]
# df102 = df[df["Part Size"] == 102]

dataframes = [df60, df72]

for dataframe in dataframes:
    A = dataframe[dataframe["Treatment"] == "Standard"]
    B = dataframe[dataframe["Treatment"] == "Less"]
    
    partsize = int(np.mean(dataframe["Part Size"]))
    print("\n###############################################")
    print("Part Size:\t{}".format(partsize))
    print("Treatments:")
    print(dataframe["Treatment"].value_counts())
    
    rtt.find_stat_difference_2group(A, B, "White Area")


fig1 = plt.figure(dpi=300)
sns.scatterplot(data=df, x="Part Size", y="White Area")

fig2 = plt.figure(dpi=300)
sns.scatterplot(data=df, x="Percentage", y="White Area")

sorted_sizes = np.sort(df["Part Size"].unique())
print("\n################################################")
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