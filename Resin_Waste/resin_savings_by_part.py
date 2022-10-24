# -*- coding: utf-8 -*-
"""
Created on Mon Oct 24 10:28:13 2022

@author: Ryan.Larson
"""

import numpy as np

parts_dict_current = {
    "Elite 36": 33.2,
    "Elite 48": 38.7,
    "Elite 60": 44.2,
    "Elite 72": 51.9,
    "Elite 84": 60.2,
    "Elite 96": 70.7,
    "Elite 102": 80.9,
    "Cascade 24": 7.8,
    "Cascade 36": 12.2,
    "Cascade 48": 17.6,
    "Cascade 24/24": 15.6,
    "Cascade 24/36": 20.0,
    "Cascade 24/48": 25.4,
    "Cascade 36/36": 24.4,
    "Cascade 36/48": 29.8,
    "Cascade 48/48": 35.2,
    "Cascade 60": 25.0,
    "Cascade 72": 41.5,
    "Cascade 80": 46.0    
    }

part_sizes = list(parts_dict_current.keys())
single_part_sizes = [part for part in part_sizes if "/" not in part]

pounds_less = 3.0

pounds_72_current = parts_dict_current["Elite 72"]
pounds_72_adjusted = pounds_72_current - pounds_less
pct_adjusted = pounds_72_adjusted / pounds_72_current
parts_dict_adjusted = {key:np.around(value*pct_adjusted,1) for (key,value) in parts_dict_current.items()}

resin_saved = {}
for key in parts_dict_current:
    resin_saved[key] = np.around(parts_dict_current[key] - parts_dict_adjusted[key], 1)

# Estimate savings based on parts sold
parts_sold = {
    "Elite 36": 272,
    "Elite 48": 1148,
    "Elite 60": 7279,
    "Elite 72": 7139,
    "Elite 84": 731,
    "Elite 96": 149,
    "Elite 102": 0,
    "Cascade 24": 166,
    "Cascade 36": 193,
    "Cascade 48": 93,
    "Cascade 60": 6,
    "Cascade 72": 7,
    "Cascade 80": 8    
    }

resin_cost_lb = 2.60

cost_savings = {key:np.around(parts_sold[key]*resin_saved[key]*resin_cost_lb, 2) for (key,value) in parts_sold.items()}

total_parts = 0
total_cost_savings = 0
savings_per_part = {}
for key in cost_savings.keys():
    total_parts += parts_sold[key]
    total_cost_savings += cost_savings[key]
    if parts_sold[key] == 0:
        savings_per_part[key] = 0.0
    else:
        savings_per_part[key] = cost_savings[key] / parts_sold[key]
    
avg_part_savings = total_cost_savings / total_parts

print("Savings results:")
print("Total parts:\t{}".format(total_parts))
print("Total savings:\t${}".format(np.around(total_cost_savings,2)))
print("Average savings per part:\t${}".format(avg_part_savings))
