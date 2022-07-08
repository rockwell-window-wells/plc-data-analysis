# -*- coding: utf-8 -*-
"""
Created on Thu Jun 30 10:04:29 2022

@author: Ryan.Larson
"""

import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.stats.api as sms

# Load and prepare data
datafile = "Z:/Current Projects/RockWell Profitability/Resin Controlled Experiments.xlsx"
# datafile = "Z:/Research & Development/Resin Experiments/Hose Randomized Study.xlsx"
data = pd.read_excel(datafile, sheet_name="Results_Feed_Hose_Size")

# Drop comment column
# data = data.drop(["Unnamed: 13"], axis=1)

# # Drop incomplete rows
# data = data.drop([10,11,12,13,14,15,16,17,18,19])

# Set a specific case full part time to 20 minutes based on comment (didn't fill)
# data.at[1,"Full Part (min)"] = 20


### Ambient Temperature ###
# Filter data and load into lists
three_eighths_amb = list(data["Ambient Temp. (F)"].where(data["Feed Hose Size"] == 0.375))
three_eighths_amb = [x for x in three_eighths_amb if np.isnan(x) == False]
half_amb = list(data["Ambient Temp. (F)"].where(data["Feed Hose Size"] == 0.5))
half_amb = [x for x in half_amb if np.isnan(x) == False]

# Compute variance, run t-tests, and print results
three_eighths_amb_var = np.var(three_eighths_amb)
half_amb_var = np.var(half_amb)

if three_eighths_amb_var/half_amb_var < 1:
    var_ratio_amb = half_amb_var/three_eighths_amb_var
else:
    var_ratio_amb = three_eighths_amb_var/half_amb_var
    
if var_ratio_amb < 4:
    equal_variance = True
else:
    equal_variance = False
    
amb_results = stats.ttest_ind(three_eighths_amb, half_amb, equal_var=equal_variance)
print("\nAmbient Temperature:")
print("Variance ratio = {}".format(var_ratio_amb))
print("statistic={}, pvalue={}".format(amb_results.statistic, amb_results.pvalue))
if amb_results.pvalue < 0.05:
    print("Statistical difference: YES")
    
    # If there is a statistical difference, calculate and print the 95%
    # confidence intervals on the means, and then the difference in the
    # measured means
    cm = sms.CompareMeans(sms.DescrStatsW(three_eighths_amb), sms.DescrStatsW(half_amb))
    if equal_variance == True:
        print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='pooled')))
    else:
        print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='unequal')))
else:
    print("Statistical difference: NO")


### Mold Temperature ###
# Filter data and load into lists
three_eighths_mold = list(data["Mold Temp. (F)"].where(data["Feed Hose Size"] == 0.375))
three_eighths_mold = [x for x in three_eighths_mold if np.isnan(x) == False]
half_mold = list(data["Mold Temp. (F)"].where(data["Feed Hose Size"] == 0.5))
half_mold = [x for x in half_mold if np.isnan(x) == False]

# Compute variance, run t-tests, and print results
three_eighths_mold_var = np.var(three_eighths_mold)
half_mold_var = np.var(half_mold)

if three_eighths_mold_var/half_mold_var < 1:
    var_ratio_mold = half_mold_var/three_eighths_mold_var
else:
    var_ratio_mold = three_eighths_mold_var/half_mold_var
    
if var_ratio_mold < 4:
    equal_variance = True
else:
    equal_variance = False
    
mold_results = stats.ttest_ind(three_eighths_mold, half_mold, equal_var=equal_variance)
print("\nMold Temperature:")
print("Variance ratio = {}".format(var_ratio_mold))
print("statistic={}, pvalue={}".format(mold_results.statistic, mold_results.pvalue))
if mold_results.pvalue < 0.05:
    print("Statistical difference: YES")
    
    # If there is a statistical difference, calculate and print the 95%
    # confidence intervals on the means, and then the difference in the
    # measured means
    cm = sms.CompareMeans(sms.DescrStatsW(three_eighths_mold), sms.DescrStatsW(half_mold))
    if equal_variance == True:
        print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='pooled')))
    else:
        print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='unequal')))
else:
    print("Statistical difference: NO")
    
    
### Time to hit flange ###
# Filter data and load into lists
three_eighths_flange = list(data["Hit Flange (min)"].where(data["Feed Hose Size"] == 0.375))
three_eighths_flange = [x for x in three_eighths_flange if np.isnan(x) == False]
half_flange = list(data["Hit Flange (min)"].where(data["Feed Hose Size"] == 0.5))
half_flange = [x for x in half_flange if np.isnan(x) == False]

# Compute variance, run t-tests, and print results
three_eighths_flange_var = np.var(three_eighths_flange)
half_flange_var = np.var(half_flange)

if three_eighths_flange_var/half_flange_var < 1:
    var_ratio_flange = half_flange_var/three_eighths_flange_var
else:
    var_ratio_flange = three_eighths_flange_var/half_flange_var
    
if var_ratio_flange < 4:
    equal_variance = True
else:
    equal_variance = False
    
flange_results = stats.ttest_ind(three_eighths_flange, half_flange, equal_var=equal_variance)
print("\nTime to Hit Flange:")
print("Variance ratio = {}".format(var_ratio_flange))
print("statistic={}, pvalue={}".format(flange_results.statistic, flange_results.pvalue))
if flange_results.pvalue < 0.05:
    print("Statistical difference: YES")
    
    # If there is a statistical difference, calculate and print the 95%
    # confidence intervals on the means, and then the difference in the
    # measured means
    cm = sms.CompareMeans(sms.DescrStatsW(three_eighths_flange), sms.DescrStatsW(half_flange))
    if equal_variance == True:
        print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='pooled')))
    else:
        print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='unequal')))
else:
    print("Statistical difference: NO")


### Time to empty bucket ###
# Filter data and load into lists
three_eighths_bucket = list(data["Empty Bucket (min)"].where(data["Feed Hose Size"] == 0.375))
three_eighths_bucket = [x for x in three_eighths_bucket if np.isnan(x) == False]
half_bucket = list(data["Empty Bucket (min)"].where(data["Feed Hose Size"] == 0.5))
half_bucket = [x for x in half_bucket if np.isnan(x) == False]

# Compute variance, run t-tests, and print results
three_eighths_bucket_var = np.var(three_eighths_bucket)
half_bucket_var = np.var(half_bucket)

if three_eighths_bucket_var/half_bucket_var < 1:
    var_ratio_bucket = half_bucket_var/three_eighths_bucket_var
else:
    var_ratio_bucket = three_eighths_bucket_var/half_bucket_var
    
if var_ratio_bucket < 4:
    equal_variance = True
else:
    equal_variance = False
    
bucket_results = stats.ttest_ind(three_eighths_bucket, half_bucket, equal_var=equal_variance)
print("\nTime to Empty Bucket:")
print("Variance ratio = {}".format(var_ratio_bucket))
print("statistic={}, pvalue={}".format(bucket_results.statistic, bucket_results.pvalue))
if bucket_results.pvalue < 0.05:
    print("Statistical difference: YES")
    
    # If there is a statistical difference, calculate and print the 95%
    # confidence intervals on the means, and then the difference in the
    # measured means
    cm = sms.CompareMeans(sms.DescrStatsW(three_eighths_bucket), sms.DescrStatsW(half_bucket))
    if equal_variance == True:
        print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='pooled')))
    else:
        print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='unequal')))
else:
    print("Statistical difference: NO")


### Time to full part ###
# Filter data and load into lists
three_eighths_full = list(data["Full Part (min)"].where(data["Feed Hose Size"] == 0.375))
three_eighths_full = [x for x in three_eighths_full if np.isnan(x) == False]
half_full = list(data["Full Part (min)"].where(data["Feed Hose Size"] == 0.5))
half_full = [x for x in half_full if np.isnan(x) == False]

# Compute variance, run t-tests, and print results
three_eighths_full_var = np.var(three_eighths_full)
half_full_var = np.var(half_full)

if three_eighths_full_var/half_full_var < 1:
    var_ratio_full = half_full_var/three_eighths_full_var
else:
    var_ratio_full = three_eighths_full_var/half_full_var
    
if var_ratio_full < 4:
    equal_variance = True
else:
    equal_variance = False
    
full_results = stats.ttest_ind(three_eighths_full, half_full, equal_var=equal_variance)
print("\nTime to Full Part:")
print("Variance ratio = {}".format(var_ratio_full))
print("statistic={}, pvalue={}".format(full_results.statistic, full_results.pvalue))
if full_results.pvalue < 0.05:
    print("Statistical difference: YES")
    
    # If there is a statistical difference, calculate and print the 95%
    # confidence intervals on the means, and then the difference in the
    # measured means
    cm = sms.CompareMeans(sms.DescrStatsW(three_eighths_full), sms.DescrStatsW(half_full))
    if equal_variance == True:
        print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='pooled')))
    else:
        print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='unequal')))
else:
    print("Statistical difference: NO")


### Time to full cure ###
# Filter data and load into lists
three_eighths_cure = list(data["Full Cure (min)"].where(data["Feed Hose Size"] == 0.375))
three_eighths_cure = [x for x in three_eighths_cure if np.isnan(x) == False]
half_cure = list(data["Full Cure (min)"].where(data["Feed Hose Size"] == 0.5))
half_cure = [x for x in half_cure if np.isnan(x) == False]

# Compute variance, run t-tests, and print results
three_eighths_cure_var = np.var(three_eighths_cure)
half_cure_var = np.var(half_cure)

if three_eighths_cure_var/half_cure_var < 1:
    var_ratio_cure = half_cure_var/three_eighths_cure_var
else:
    var_ratio_cure = three_eighths_cure_var/half_cure_var
    
if var_ratio_cure < 4:
    equal_variance = True
else:
    equal_variance = False
    
cure_results = stats.ttest_ind(three_eighths_cure, half_cure, equal_var=equal_variance)
print("\nTime to Full Cure:")
print("Variance ratio = {}".format(var_ratio_cure))
print("statistic={}, pvalue={}".format(cure_results.statistic, cure_results.pvalue))
if cure_results.pvalue < 0.05:
    print("Statistical difference: YES")
    
    # If there is a statistical difference, calculate and print the 95%
    # confidence intervals on the means, and then the difference in the
    # measured means
    cm = sms.CompareMeans(sms.DescrStatsW(three_eighths_cure), sms.DescrStatsW(half_cure))
    if equal_variance == True:
        print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='pooled')))
    else:
        print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='unequal')))
else:
    print("Statistical difference: NO")


### Total White Area ###
# Filter data and load into lists
three_eighths_white = list(data["Total White Area (in^2)"].where(data["Feed Hose Size"] == 0.375))
three_eighths_white = [x for x in three_eighths_white if np.isnan(x) == False]
half_white = list(data["Total White Area (in^2)"].where(data["Feed Hose Size"] == 0.5))
half_white = [x for x in half_white if np.isnan(x) == False]

# Compute variance, run t-tests, and print results
three_eighths_white_var = np.var(three_eighths_white)
half_white_var = np.var(half_white)

if three_eighths_white_var < half_white_var:
    var_ratio_white = three_eighths_white_var/half_white_var
else:
    var_ratio_white = half_white_var/three_eighths_white_var

# var_ratio_white = three_eighths_white_var/half_white_var

if var_ratio_white < 4:
    equal_variance = True
else:
    equal_variance = False
    
white_results = stats.ttest_ind(three_eighths_white, half_white, equal_var=equal_variance)
print("\nTotal White Area:")
print("Variance ratio = {}".format(var_ratio_white))
print("statistic={}, pvalue={}".format(white_results.statistic, white_results.pvalue))
if white_results.pvalue < 0.05:
    print("Statistical difference: YES")
    
    # If there is a statistical difference, calculate and print the 95%
    # confidence intervals on the means, and then the difference in the
    # measured means
    cm = sms.CompareMeans(sms.DescrStatsW(three_eighths_white), sms.DescrStatsW(half_white))
    if equal_variance == True:
        print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='pooled')))
    else:
        print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='unequal')))
else:
    print("Statistical difference: NO")

