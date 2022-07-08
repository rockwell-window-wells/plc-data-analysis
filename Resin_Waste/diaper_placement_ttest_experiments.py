# -*- coding: utf-8 -*-
"""
Created on Thu Jul  7 14:59:13 2022

@author: Ryan.Larson
"""

import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.stats.api as sms
import matplotlib.pyplot as plt


def check_variance_equality(halfway, top, bottom, column_str):
    # Compute variances
    halfway_var = np.var(halfway[column_str])
    top_var = np.var(top[column_str])
    bottom_var = np.var(bottom[column_str])
    
    # Compare variances
    var_list = [halfway_var, top_var, bottom_var]
    var_list.sort(reverse=True)
    
    var_ratios = [var_list[0]/var_list[1],
                  var_list[0]/var_list[2],
                  var_list[1]/var_list[2]]
    
    if any(ratio > 4 for ratio in var_ratios):
        equal_variance = False
    else:
        equal_variance = True
        
    return equal_variance


def oneway_anova(halfway, top, bottom, column_str):
    equal_variance = check_variance_equality(halfway, top, bottom, column_str)
    print("\n\n########################")
    print("{}".format(column_str))
    print("########################")
    if equal_variance:
        print("\nOne-way ANOVA:")
        results = stats.f_oneway(halfway[column_str], top[column_str], bottom[column_str])
        print("P-value:\t{}".format(results.pvalue))
        if results.pvalue < 0.05:
            print("Statistical difference: YES")
        else:
            print("Statistical difference: NO")
    else:
        print("\nEqual variance assumption is not met. One-way ANOVA is not valid.")
        
    return equal_variance
    

    
# Load and prepare data
datafile = "Z:/Current Projects/RockWell Profitability/Resin Controlled Experiments.xlsx"
# datafile = "Z:/Research & Development/Resin Experiments/Hose Randomized Study.xlsx"
data = pd.read_excel(datafile, sheet_name="Results_Diaper_Placement")

halfway = data.where(data["Diaper Placement on Capstone"] == "Halfway")
top = data.where(data["Diaper Placement on Capstone"] == "Top")
bottom = data.where(data["Diaper Placement on Capstone"] == "Bottom")

halfway = halfway.dropna(axis=0)
top = top.dropna(axis=0)
bottom = bottom.dropna(axis=0)


column_list = ["Ambient Temp. (F)", "Mold Temp. (F)", "Purple 72 Mark Length (in)",
               "Hit Flange (min)", "Empty Bucket (min)", "Full Part (min)",
               "Full Cure (min)", "Total White Area (in^2)"]

for column_str in column_list:
    equal_variance = oneway_anova(halfway, top, bottom, column_str)
    if equal_variance is False:
        # # Plot histograms of the values of interest
        # plt.hist(halfway[column_str], alpha=0.5, label="Halfway", color='r')
        # plt.hist(top[column_str], alpha=0.5, label="Top", color='b')
        # plt.hist(bottom[column_str], alpha=0.5, label="Bottom", color='g')
        # plt.legend(loc="upper right")
        # plt.title(column_str)
        # plt.show()
        
        # Perform combinations of t-tests that don't require equal variance
        print("Performing Welch's t-test for unequal variance...")
        halfway_top = stats.ttest_ind(halfway[column_str], top[column_str], equal_var=equal_variance)
        halfway_bottom = stats.ttest_ind(halfway[column_str], bottom[column_str], equal_var=equal_variance)
        top_bottom = stats.ttest_ind(top[column_str], bottom[column_str], equal_var=equal_variance)
        
        print("\nHalfway vs. Top:\tpvalue={}".format(halfway_top.pvalue))
        if halfway_top.pvalue < 0.05:
            print("Statistical difference: YES")
            cm = sms.CompareMeans(sms.DescrStatsW(halfway[column_str]), sms.DescrStatsW(top[column_str]))
            if equal_variance:
                print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='pooled')))
            else:
                print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='unequal')))
                
        else:
            print("Statistical difference: NO")
        
        print("\nHalfway vs. Bottom:\tpvalue={}".format(halfway_bottom.pvalue))
        if halfway_bottom.pvalue < 0.05:
            print("Statistical difference: YES")
            cm = sms.CompareMeans(sms.DescrStatsW(halfway[column_str]), sms.DescrStatsW(bottom[column_str]))
            if equal_variance:
                print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='pooled')))
            else:
                print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='unequal')))
        else:
            print("Statistical difference: NO")
        
        print("\nTop vs. Bottom:\tpvalue={}".format(top_bottom.pvalue))
        if top_bottom.pvalue < 0.05:
            print("Statistical difference: YES")
            cm = sms.CompareMeans(sms.DescrStatsW(top[column_str]), sms.DescrStatsW(bottom[column_str]))
            if equal_variance:
                print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='pooled')))
            else:
                print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='unequal')))
        else:
            print("Statistical difference: NO")