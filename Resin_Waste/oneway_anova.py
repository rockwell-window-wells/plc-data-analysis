# -*- coding: utf-8 -*-
"""
Created on Mon Aug 29 13:10:32 2022

@author: Ryan.Larson
"""

import numpy as np
from scipy import stats
import pandas as pd
from itertools import combinations


def check_variance_equality(feature_data, column_str):
    # Compute variances
    var_list = []
    for i in range(len(feature_data)):
        var_list.append(np.var(feature_data[i][column_str]))
    var_list.sort(reverse=True)
    
    # Get all combinations of 2 and check ratios. If a variance of 0 is found,
    # return 0 for that variance ratio
    var_ratios = []
    var_combos = list(combinations(var_list, 2))
    for i,combo in enumerate(var_combos):
        if (var_combos[i][0] == 0) or (var_combos[i][1] == 0):
            var_ratios.append(0.0)
        else:
            var_ratios.append(var_combos[i][0] / var_combos[i][1])
    
    if any(ratio > 4 for ratio in var_ratios):
        equal_variance = False
    else:
        equal_variance = True
        
    return equal_variance


def oneway_anova(feature_data, column_str):
    equal_variance = check_variance_equality(feature_data, column_str)
    print("\n\n########################")
    print("{}".format(column_str))
    print("########################")
    if equal_variance:
        print("\nOne-way ANOVA:")
        # results = stats.f_oneway(A[column_str], B[column_str], C[column_str], D[column_str])
        results = stats.f_oneway(*(data[column_str] for data in feature_data))
        print("P-value:\t{}".format(results.pvalue))
        if results.pvalue < 0.05:
            print("Statistical difference: YES")
        else:
            print("Statistical difference: NO")
    else:
        print("\nEqual variance assumption is not met. One-way ANOVA is not valid.")
        
    return equal_variance


if __name__ == "__main__":
    # Load and prepare data
    datafile = "Z:/Current Projects/RockWell Profitability/Resin Controlled Experiments.xlsx"
    sheet = "Results_Resin_Regression (2)"
    data = pd.read_excel(datafile, sheet_name=sheet)
    
    # Remove any unnamed columns
    data = data[data.columns.drop(list(data.filter(regex='Unnamed')))]
    
    column_list = list(data.columns)
    feature = column_list.pop(0)
    
    column_list.remove("Resin Amt. (lbs)")
    column_list.remove("Catalyst Amt. (mL)")
    
    # Work through the feature values (flexible, doesn't expect a specific
    # number of features)
    feature_vals = list(data[feature].unique())
    feature_data = [data.where(data[feature] == val) for val in feature_vals]
    for i,df in enumerate(feature_data):
        feature_data[i] = feature_data[i].dropna(axis=0)
    
    print("##############################")
    print("Sheet:\t{}".format(sheet))
    print("Parameter:\t{}".format(feature))
    print("Treatments:")
    for val in feature_vals:
        print("\t{}".format(val))
    print("##############################")
    
    for column_str in column_list:
        oneway_anova(feature_data, column_str)