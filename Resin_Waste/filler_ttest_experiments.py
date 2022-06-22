# -*- coding: utf-8 -*-
"""
Created on Thu Jun  9 13:56:53 2022

@author: Ryan.Larson
"""

import pandas as pd
import numpy as np
from scipy import stats

# Load and prepare data
datafile = "Z:/Research & Development/Resin Experiments/Filler Randomized Study.xlsx"
data = pd.read_excel(datafile, sheet_name="Results")

# Drop comment column
data = data.drop(["Unnamed: 13"], axis=1)

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
else:
    print("Statistical difference: NO")

