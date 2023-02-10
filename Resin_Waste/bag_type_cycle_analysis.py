# -*- coding: utf-8 -*-
"""
Created on Wed Jan  4 09:43:49 2023

@author: Ryan.Larson
"""

import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.stats.api as sms
import resin_ttest_experiments as rtt

purple = "purple2_resin.csv"
red = "red2_resin.csv"
orange = "orange2_resin.csv"
pink = "pink2_resin.csv"
# purple = "purple.csv"
# red = "red.csv"
# orange = "orange.csv"
# pink = "pink.csv"

old_bags = [purple, red]
new_bags = [orange, pink]
colors = [purple, red, orange, pink]

# sheet = "Data"

dropcols = ["time", "Leak Time", "Leak Count", "Parts Count", "Weekly Count",
            "Monthly Count", "Trash Count", "Lead", "Assistant 1", "Assistant 2",
            "Assistant 3", "Bag", "Bag Days", "Bag Cycles"]

# for bag in colors:
#     df = pd.read_csv(bag)
#     # for col in dropcols:
#     #     df = df.drop(col,axis=1)
#     df = df.dropna(how="all")
#     # df = df.dropna(axis=0)
#     df.to_csv(bag, index=False)

frames = []

for bag in colors:
    df = pd.read_csv(bag)
    if bag == purple or bag == red:
        df["Bag"] = pd.Series(["Old" for x in range(len(df.index))])
    else:
        df["Bag"] = pd.Series(["New" for x in range(len(df.index))])
        
    frames.append(df)
    
alldata = pd.concat(frames)

feature_vals = list(alldata["Bag"].unique())
n_feature_vals = len(feature_vals)

df_features = [alldata.where(alldata["Bag"] == feature_val) for feature_val in feature_vals]
df_features = [df_feature.dropna(axis=0) for df_feature in df_features]


# rtt.oneway_anova(df_features, "Cycle Time")

rtt.find_stat_difference_2group(df_features[0], df_features[1], "Resin Time")
# rtt.find_stat_difference_2group(df_features[0], df_features[1], "Cycle Time")
