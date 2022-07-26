# -*- coding: utf-8 -*-
"""
Created on Tue Jul 26 10:10:52 2022

@author: Ryan.Larson
"""
import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.stats.api as sms


def find_stat_difference_2group(A, B, column_str):
    A_var = np.var(A[column_str])
    B_var = np.var(B[column_str])
    
    if A_var == 0 or B_var == 0:
        var_ratio = 0
        equal_variance = True
    else:
        if A_var/B_var < 1:
            var_ratio = B_var/A_var
        else:
            var_ratio = A_var/B_var
            
        if var_ratio < 4:
            equal_variance = True
        else:
            equal_variance = False
        
    results = stats.ttest_ind(A[column_str], B[column_str], equal_var=equal_variance)
    
    print("\n{}".format(column_str))
    print("Variance ratio = {}".format(var_ratio))
    print("statistic={}, pvalue={}".format(results.statistic, results.pvalue))
    if results.pvalue < 0.05:
        print("Statistical difference: YES")
        
        # If there is a statistical difference, calculate and print the 95%
        # confidence intervals on the means, and then the difference in the
        # measured means
        cm = sms.CompareMeans(sms.DescrStatsW(A[column_str]), sms.DescrStatsW(B[column_str]))
        if equal_variance == True:
            print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='pooled')))
        else:
            print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='unequal')))
    else:
        print("Statistical difference: NO")


def check_variance_equality(A, B, C, column_str):
    # Compute variances
    A_var = np.var(A[column_str])
    B_var = np.var(B[column_str])
    C_var = np.var(C[column_str])
    
    # Compare variances
    var_list = [A_var, B_var, C_var]
    var_list.sort(reverse=True)
    
    var_ratios = [var_list[0]/var_list[1],
                  var_list[0]/var_list[2],
                  var_list[1]/var_list[2]]
    
    if any(ratio > 4 for ratio in var_ratios):
        equal_variance = False
    else:
        equal_variance = True
        
    return equal_variance


def oneway_anova(A, B, C, column_str):
    equal_variance = check_variance_equality(A, B, C, column_str)
    print("\n\n########################")
    print("{}".format(column_str))
    print("########################")
    if equal_variance:
        print("\nOne-way ANOVA:")
        results = stats.f_oneway(A[column_str], B[column_str], C[column_str])
        print("P-value:\t{}".format(results.pvalue))
        if results.pvalue < 0.05:
            print("Statistical difference: YES")
        else:
            print("Statistical difference: NO")
    else:
        print("\nEqual variance assumption is not met. One-way ANOVA is not valid.")
        
    return equal_variance


def combination_ttests(A, B, C, column_str, feature_vals):
    equal_variance = oneway_anova(A, B, C, column_str)
    if equal_variance is False:
        # # Plot histograms of the values of interest
        # plt.hist(A[column_str], alpha=0.5, label=str(feature_vals[0]), color='r')
        # plt.hist(B[column_str], alpha=0.5, label=str(feature_vals[1]), color='b')
        # plt.hist(C[column_str], alpha=0.5, label=str(feature_vals[2]), color='g')
        # plt.legend(loc="upper right")
        # plt.title(column_str)
        # plt.show()
        
        # Perform combinations of t-tests that don't require equal variance
        print("Performing Welch's t-test for unequal variance...")
        A_B = stats.ttest_ind(A[column_str], B[column_str], equal_var=equal_variance)
        A_C = stats.ttest_ind(A[column_str], C[column_str], equal_var=equal_variance)
        B_C = stats.ttest_ind(B[column_str], C[column_str], equal_var=equal_variance)
        
        print("\n{} vs. {}:\tpvalue={}".format(feature_vals[0], feature_vals[1], A_B.pvalue))
        if A_B.pvalue < 0.05:
            print("Statistical difference: YES")
            cm = sms.CompareMeans(sms.DescrStatsW(A[column_str]), sms.DescrStatsW(B[column_str]))
            if equal_variance:
                print("95% Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='pooled')))
            else:
                print("95% Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='unequal')))         
        else:
            print("Statistical difference: NO")
        
        print("\n{} vs. {}:\tpvalue={}".format(feature_vals[0], feature_vals[2], A_C.pvalue))
        if A_C.pvalue < 0.05:
            print("Statistical difference: YES")
            cm = sms.CompareMeans(sms.DescrStatsW(A[column_str]), sms.DescrStatsW(C[column_str]))
            if equal_variance:
                print("95% Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='pooled')))
            else:
                print("95% Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='unequal')))
        else:
            print("Statistical difference: NO")
        
        print("\n{} vs. {}:\tpvalue={}".format(feature_vals[1], feature_vals[2], B_C.pvalue))
        if B_C.pvalue < 0.05:
            print("Statistical difference: YES")
            cm = sms.CompareMeans(sms.DescrStatsW(B[column_str]), sms.DescrStatsW(C[column_str]))
            if equal_variance:
                print("95% Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='pooled')))
            else:
                print("95% Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='unequal')))
        else:
            print("Statistical difference: NO")    
    
    
if __name__ == "__main__":
    # Load and prepare data
    datafile = "Z:/Current Projects/RockWell Profitability/Resin Controlled Experiments.xlsx"
    sheet = "Results_Filler_Low_Catalyst"
    # sheet = "Results_Filler_Extra_Low_Cat"
    # sheet = "Results_Filler_Extra_Low_Cat_2"
    # sheet = "Results_Feed_Hose_Size"
    # sheet = "Results_Feed_Hose_Size_2"
    # sheet = "Results_Diaper_Placement"
    # sheet = "Results_Hose_Number"
    data = pd.read_excel(datafile, sheet_name=sheet)    
    
    column_list = list(data.columns)
    feature = column_list.pop(1)
    del column_list[0]
    column_list.remove("Resin Amt. (lbs)")
    column_list.remove("Catalyst Amt. (mL)")
    
    
    feature_vals = list(data[feature].unique())
    n_feature_vals = len(feature_vals)
    
    if n_feature_vals == 2:
        A = data.where(data[feature] == feature_vals[0])
        B = data.where(data[feature] == feature_vals[1])
        
        A = A.dropna(axis=0)
        B = B.dropna(axis=0)
        
    elif n_feature_vals == 3:
        A = data.where(data[feature] == feature_vals[0])
        B = data.where(data[feature] == feature_vals[1])
        C = data.where(data[feature] == feature_vals[2])
        
        A = A.dropna(axis=0)
        B = B.dropna(axis=0)
        C = C.dropna(axis=0)
    else:
        raise ValueError("ERROR: Wrong number of features")
    
    print("##############################")
    print("Sheet:\t{}".format(sheet))
    print("Parameter:\t{}".format(feature))
    print("Treatments:")
    for val in feature_vals:
        print("\t{}".format(val))
    print("##############################")
        
    for column_str in column_list:
        if n_feature_vals == 2:
            find_stat_difference_2group(A, B, column_str)
        else:
            combination_ttests(A, B, C, column_str, feature_vals)