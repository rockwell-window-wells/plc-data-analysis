# -*- coding: utf-8 -*-
"""
Created on Wed Feb  2 09:27:39 2022

@author: Ryan.Larson
"""

import numpy as np
import pandas as pd

cycle_inds = [4, 11, 17, 25, 39, 54, 65, 80, 95, 107, 118]
resin_inds = [4, 11, 17, 25, 39, 54, 65, 80, 95, 106, 118]
close_inds = [1, 8, 16, 22, 34, 49, 56, 71, 90, 101, 113, 120]
layup_inds = [0, 7, 12, 21, 33, 40, 55, 70, 85, 96, 112, 119]

cycle_times = list(np.random.uniform(low=80, high=200, size=np.shape(cycle_inds)))
resin_times = list(np.random.uniform(low=80, high=200, size=np.shape(resin_inds)))
close_times = list(np.random.uniform(low=80, high=200, size=np.shape(close_inds)))
layup_times = list(np.random.uniform(low=80, high=200, size=np.shape(layup_inds)))

longest_len = max([len(cycle_inds),len(resin_inds),len(close_inds),len(layup_inds)])
longest_inds = None
for i, inds in enumerate([layup_inds, close_inds, resin_inds, cycle_inds]):
    if len(inds) == longest_len:
        longest_inds = inds
        # break

# Get layup indices and times to match the longest indices vector
while len(layup_inds) < longest_len:
    for i in range(len(layup_inds)):
        layup_diff = close_inds[i] - layup_inds[i]
        if layup_diff < 0:
            layup_inds.insert(i, i)
            layup_times.insert(i, np.nan)
            print("Added an index and time to layup")
            break
    if len(layup_inds) < len(longest_inds):
        layup_inds.append(longest_inds[len(layup_inds)])
        layup_times.append(np.nan)
        
# Get close indices and times to match the longest indices vector
while len(close_inds) < longest_len:
    for i in range(len(close_inds)):
        close_diff = resin_inds[i] - close_inds[i]
        if close_diff < 0:
            close_inds.insert(i, i)
            close_times.insert(i, np.nan)
            print("Added an index and time to close")
            break
    if len(close_inds) < len(longest_inds):
        close_inds.append(longest_inds[len(close_inds)])
        close_times.append(np.nan)
        
# Get resin indices and times to match the longest indices vector
while len(resin_inds) < longest_len:
    for i in range(len(resin_inds)):
        resin_diff = cycle_inds[i] - resin_inds[i]
        if resin_diff < 0:
            resin_inds.insert(i, i)
            resin_times.insert(i, np.nan)
            print("Added an index and time to resin")
            break
    if len(resin_inds) < len(longest_inds):
        resin_inds.append(longest_inds[len(resin_inds)])
        resin_times.append(np.nan)
        
# Get cycle indices and times to match the longest indices vector
while len(cycle_inds) < longest_len:
    for i in range(len(cycle_inds)):
        cycle_diff = cycle_inds[i] - resin_inds[i]
        if cycle_diff < 0:
            cycle_inds.insert(i, i)
            cycle_times.insert(i, np.nan)
            print("Added an index and time to resin")
            break
    if len(cycle_inds) < len(longest_inds):
        cycle_inds.append(longest_inds[len(cycle_inds)])
        cycle_times.append(np.nan)
        
# Combine indices data
indices = {"Layup Inds": layup_inds,
           "Close Inds": close_inds,
           "Resin Inds": resin_inds,
           "Cycle Inds": cycle_inds}
df_inds = pd.DataFrame.from_dict(indices)
        

# Combine times data
times = {"Layup Time": layup_times,
         "Close Time": close_times,
         "Resin Time": resin_times,
         "Cycle Time": cycle_times}
df_times = pd.DataFrame.from_dict(times)  


        