# -*- coding: utf-8 -*-
"""
Created on Thu Jun  9 13:56:53 2022

@author: Ryan.Larson
"""

import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.stats.api as sms

# Load and prepare data
datafile = "Z:/Current Projects/RockWell Profitability/Resin Controlled Experiments.xlsx"
# datafile = "Z:/Research & Development/Resin Experiments/Filler Randomized Study.xlsx"

# data = pd.read_excel(datafile, sheet_name="Results_Filler_Low_Catalyst")
data = pd.read_excel(datafile, sheet_name="Results_Filler_Extra_Low_Cat")


# Drop comment column
# data = data.drop(["Unnamed: 13"], axis=1)

# # Drop incomplete rows
# data = data.drop([10,11,12,13,14,15,16,17,18,19])

# Set a specific case full part time to 20 minutes based on comment (didn't fill)
# data.at[1,"Full Part (min)"] = 20


### Ambient Temperature ###
# Filter data and load into lists
nofiller_amb = list(data["Ambient Temp. (F)"].where(data["Filler"] == 0.0))
nofiller_amb = [x for x in nofiller_amb if np.isnan(x) == False]
filler_amb = list(data["Ambient Temp. (F)"].where(data["Filler"] == 0.1))
filler_amb = [x for x in filler_amb if np.isnan(x) == False]

# Compute variance, run t-tests, and print results
nofiller_amb_var = np.var(nofiller_amb)
filler_amb_var = np.var(filler_amb)

if nofiller_amb_var/filler_amb_var < 1:
    var_ratio_amb = filler_amb_var/nofiller_amb_var
else:
    var_ratio_amb = nofiller_amb_var/filler_amb_var
    
if var_ratio_amb < 4:
    equal_variance = True
else:
    equal_variance = False
    
amb_results = stats.ttest_ind(nofiller_amb, filler_amb, equal_var=equal_variance)
print("\nAmbient Temperature:")
print("Variance ratio = {}".format(var_ratio_amb))
print("statistic={}, pvalue={}".format(amb_results.statistic, amb_results.pvalue))
if amb_results.pvalue < 0.05:
    print("Statistical difference: YES")
    
    # If there is a statistical difference, calculate and print the 95%
    # confidence intervals on the means, and then the difference in the
    # measured means
    cm = sms.CompareMeans(sms.DescrStatsW(nofiller_amb), sms.DescrStatsW(filler_amb))
    if equal_variance == True:
        print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='pooled')))
    else:
        print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='unequal')))
else:
    print("Statistical difference: NO")


### Mold Temperature ###
# Filter data and load into lists
nofiller_mold = list(data["Mold Temp. (F)"].where(data["Filler"] == 0.0))
nofiller_mold = [x for x in nofiller_mold if np.isnan(x) == False]
filler_mold = list(data["Mold Temp. (F)"].where(data["Filler"] == 0.1))
filler_mold = [x for x in filler_mold if np.isnan(x) == False]

# Compute variance, run t-tests, and print results
nofiller_mold_var = np.var(nofiller_mold)
filler_mold_var = np.var(filler_mold)

if nofiller_mold_var/filler_mold_var < 1:
    var_ratio_mold = filler_mold_var/nofiller_mold_var
else:
    var_ratio_mold = nofiller_mold_var/filler_mold_var
    
if var_ratio_mold < 4:
    equal_variance = True
else:
    equal_variance = False
    
mold_results = stats.ttest_ind(nofiller_mold, filler_mold, equal_var=equal_variance)
print("\nMold Temperature:")
print("Variance ratio = {}".format(var_ratio_mold))
print("statistic={}, pvalue={}".format(mold_results.statistic, mold_results.pvalue))
if mold_results.pvalue < 0.05:
    print("Statistical difference: YES")
    
    # If there is a statistical difference, calculate and print the 95%
    # confidence intervals on the means, and then the difference in the
    # measured means
    cm = sms.CompareMeans(sms.DescrStatsW(nofiller_mold), sms.DescrStatsW(filler_mold))
    if equal_variance == True:
        print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='pooled')))
    else:
        print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='unequal')))
else:
    print("Statistical difference: NO")
    
### Purple Length to 72 Mark ###
# Filter data and load into lists
nofiller_purple = list(data["Purple 72 Mark Length (in)"].where(data["Filler"] == 0.0))
nofiller_purple = [x for x in nofiller_purple if np.isnan(x) == False]
filler_purple = list(data["Purple 72 Mark Length (in)"].where(data["Filler"] == 0.1))
filler_purple = [x for x in filler_purple if np.isnan(x) == False]

# Compute variance, run t-tests, and print results
nofiller_purple_var = np.var(nofiller_purple)
filler_purple_var = np.var(filler_purple)

if nofiller_purple_var/filler_purple_var < 1:
    var_ratio_purple = filler_purple_var/nofiller_purple_var
else:
    var_ratio_purple = nofiller_purple_var/filler_purple_var
    
if var_ratio_purple < 4:
    equal_variance = True
else:
    equal_variance = False
    
purple_results = stats.ttest_ind(nofiller_purple, filler_purple, equal_var=equal_variance)
print("\nPurple Length:")
print("Variance ratio = {}".format(var_ratio_purple))
print("statistic={}, pvalue={}".format(purple_results.statistic, purple_results.pvalue))
if purple_results.pvalue < 0.05:
    print("Statistical difference: YES")
    
    # If there is a statistical difference, calculate and print the 95%
    # confidence intervals on the means, and then the difference in the
    # measured means
    cm = sms.CompareMeans(sms.DescrStatsW(nofiller_purple), sms.DescrStatsW(filler_purple))
    if equal_variance == True:
        print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='pooled')))
    else:
        print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='unequal')))
else:
    print("Statistical difference: NO")
    
    
### Time to hit flange ###
# Filter data and load into lists
nofiller_flange = list(data["Hit Flange (min)"].where(data["Filler"] == 0.0))
nofiller_flange = [x for x in nofiller_flange if np.isnan(x) == False]
filler_flange = list(data["Hit Flange (min)"].where(data["Filler"] == 0.1))
filler_flange = [x for x in filler_flange if np.isnan(x) == False]

# Compute variance, run t-tests, and print results
nofiller_flange_var = np.var(nofiller_flange)
filler_flange_var = np.var(filler_flange)

if nofiller_flange_var/filler_flange_var < 1:
    var_ratio_flange = filler_flange_var/nofiller_flange_var
else:
    var_ratio_flange = nofiller_flange_var/filler_flange_var
    
if var_ratio_flange < 4:
    equal_variance = True
else:
    equal_variance = False
    
flange_results = stats.ttest_ind(nofiller_flange, filler_flange, equal_var=equal_variance)
print("\nTime to Hit Flange:")
print("Variance ratio = {}".format(var_ratio_flange))
print("statistic={}, pvalue={}".format(flange_results.statistic, flange_results.pvalue))
if flange_results.pvalue < 0.05:
    print("Statistical difference: YES")
    
    # If there is a statistical difference, calculate and print the 95%
    # confidence intervals on the means, and then the difference in the
    # measured means
    cm = sms.CompareMeans(sms.DescrStatsW(nofiller_flange), sms.DescrStatsW(filler_flange))
    if equal_variance == True:
        print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='pooled')))
    else:
        print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='unequal')))
else:
    print("Statistical difference: NO")


### Time to empty bucket ###
# Filter data and load into lists
nofiller_bucket = list(data["Empty Bucket (min)"].where(data["Filler"] == 0.0))
nofiller_bucket = [x for x in nofiller_bucket if np.isnan(x) == False]
filler_bucket = list(data["Empty Bucket (min)"].where(data["Filler"] == 0.1))
filler_bucket = [x for x in filler_bucket if np.isnan(x) == False]

# Compute variance, run t-tests, and print results
nofiller_bucket_var = np.var(nofiller_bucket)
filler_bucket_var = np.var(filler_bucket)

if nofiller_bucket_var/filler_bucket_var < 1:
    var_ratio_bucket = filler_bucket_var/nofiller_bucket_var
else:
    var_ratio_bucket = nofiller_bucket_var/filler_bucket_var
    
if var_ratio_bucket < 4:
    equal_variance = True
else:
    equal_variance = False
    
bucket_results = stats.ttest_ind(nofiller_bucket, filler_bucket, equal_var=equal_variance)
print("\nTime to Empty Bucket:")
print("Variance ratio = {}".format(var_ratio_bucket))
print("statistic={}, pvalue={}".format(bucket_results.statistic, bucket_results.pvalue))
if bucket_results.pvalue < 0.05:
    print("Statistical difference: YES")
    
    # If there is a statistical difference, calculate and print the 95%
    # confidence intervals on the means, and then the difference in the
    # measured means
    cm = sms.CompareMeans(sms.DescrStatsW(nofiller_bucket), sms.DescrStatsW(filler_bucket))
    if equal_variance == True:
        print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='pooled')))
    else:
        print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='unequal')))
else:
    print("Statistical difference: NO")


### Time to full part ###
# Filter data and load into lists
nofiller_full = list(data["Full Part (min)"].where(data["Filler"] == 0.0))
nofiller_full = [x for x in nofiller_full if np.isnan(x) == False]
filler_full = list(data["Full Part (min)"].where(data["Filler"] == 0.1))
filler_full = [x for x in filler_full if np.isnan(x) == False]

# Compute variance, run t-tests, and print results
nofiller_full_var = np.var(nofiller_full)
filler_full_var = np.var(filler_full)

if nofiller_full_var/filler_full_var < 1:
    var_ratio_full = filler_full_var/nofiller_full_var
else:
    var_ratio_full = nofiller_full_var/filler_full_var
    
if var_ratio_full < 4:
    equal_variance = True
else:
    equal_variance = False
    
full_results = stats.ttest_ind(nofiller_full, filler_full, equal_var=equal_variance)
print("\nTime to Full Part:")
print("Variance ratio = {}".format(var_ratio_full))
print("statistic={}, pvalue={}".format(full_results.statistic, full_results.pvalue))
if full_results.pvalue < 0.05:
    print("Statistical difference: YES")
    
    # If there is a statistical difference, calculate and print the 95%
    # confidence intervals on the means, and then the difference in the
    # measured means
    cm = sms.CompareMeans(sms.DescrStatsW(nofiller_full), sms.DescrStatsW(filler_full))
    if equal_variance == True:
        print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='pooled')))
    else:
        print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='unequal')))
else:
    print("Statistical difference: NO")


### Time to full cure ###
# Filter data and load into lists
nofiller_cure = list(data["Full Cure (min)"].where(data["Filler"] == 0.0))
nofiller_cure = [x for x in nofiller_cure if np.isnan(x) == False]
filler_cure = list(data["Full Cure (min)"].where(data["Filler"] == 0.1))
filler_cure = [x for x in filler_cure if np.isnan(x) == False]

# Compute variance, run t-tests, and print results
nofiller_cure_var = np.var(nofiller_cure)
filler_cure_var = np.var(filler_cure)

if nofiller_cure_var/filler_cure_var < 1:
    var_ratio_cure = filler_cure_var/nofiller_cure_var
else:
    var_ratio_cure = nofiller_cure_var/filler_cure_var
    
if var_ratio_cure < 4:
    equal_variance = True
else:
    equal_variance = False
    
cure_results = stats.ttest_ind(nofiller_cure, filler_cure, equal_var=equal_variance)
print("\nTime to Full Cure:")
print("Variance ratio = {}".format(var_ratio_cure))
print("statistic={}, pvalue={}".format(cure_results.statistic, cure_results.pvalue))
if cure_results.pvalue < 0.05:
    print("Statistical difference: YES")
    
    # If there is a statistical difference, calculate and print the 95%
    # confidence intervals on the means, and then the difference in the
    # measured means
    cm = sms.CompareMeans(sms.DescrStatsW(nofiller_cure), sms.DescrStatsW(filler_cure))
    if equal_variance == True:
        print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='pooled')))
    else:
        print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='unequal')))
else:
    print("Statistical difference: NO")


### Total White Area ###
# Filter data and load into lists
nofiller_white = list(data["Total White Area (in^2)"].where(data["Filler"] == 0.0))
nofiller_white = [x for x in nofiller_white if np.isnan(x) == False]
filler_white = list(data["Total White Area (in^2)"].where(data["Filler"] == 0.1))
filler_white = [x for x in filler_white if np.isnan(x) == False]

# Compute variance, run t-tests, and print results
nofiller_white_var = np.var(nofiller_white)
filler_white_var = np.var(filler_white)

var_ratio_white = nofiller_white_var/filler_white_var

if var_ratio_white < 4:
    equal_variance = True
else:
    equal_variance = False
    
white_results = stats.ttest_ind(nofiller_white, filler_white, equal_var=equal_variance)
print("\nTotal White Area:")
print("Variance ratio = {}".format(var_ratio_white))
print("statistic={}, pvalue={}".format(white_results.statistic, white_results.pvalue))
if white_results.pvalue < 0.05:
    print("Statistical difference: YES")
    
    # If there is a statistical difference, calculate and print the 95%
    # confidence intervals on the means, and then the difference in the
    # measured means
    cm = sms.CompareMeans(sms.DescrStatsW(nofiller_white), sms.DescrStatsW(filler_white))
    if equal_variance == True:
        print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='pooled')))
    else:
        print("Confidence interval on mean diff: {}".format(cm.tconfint_diff(usevar='unequal')))
else:
    print("Statistical difference: NO")

