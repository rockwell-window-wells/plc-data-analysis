# -*- coding: utf-8 -*-
"""
Code for visualizing the effect of lunchtime cycle time increases on box plots.

Created on Tue Mar 22 13:57:23 2022

@author: Ryan.Larson
"""

import matplotlib.pyplot as plt
import numpy as np

nlunch = 1000
ntypical = 4*nlunch

typical_loc = 90.0
# typical_scale = 15.0
lunch_time = 30.0
lunch_loc = typical_loc + lunch_time

# typical_data = np.random.normal(loc=typical_loc, scale=typical_scale, size=ntypical)
# lunch_data = np.random.normal(loc=lunch_loc, scale=typical_scale, size=nlunch)


scale_vals = [1.0, 5.0, 10.0, 15.0]

nscales = len(scale_vals)

lunch_times = [20.0, 30.0, 45.0, 60.0]

for j, lunch_time in enumerate(lunch_times):
    lunch_loc = typical_loc + lunch_time

    fig, ax = plt.subplots(nscales,2)
    fig.set_size_inches(8.5, 11)
    fig.set_dpi(300)
    
    for i, scale in enumerate(scale_vals):
        typical_data = np.random.normal(loc=typical_loc, scale=scale, size=ntypical)
        lunch_data = np.random.normal(loc=lunch_loc, scale=scale, size=nlunch)
        
        all_data = np.concatenate((typical_data, lunch_data), axis=0)
        
        typical_median = np.median(typical_data)
        all_median = np.median(all_data)
        
        ax[i,0].boxplot(typical_data)
        ax[i,0].title.set_text("Typical times with std.dev {}".format(scale))
        ax[i,0].set_xticks([])
        labelheight = 0.75*(np.max(typical_data) - np.min(typical_data)) + np.min(typical_data)
        ax[i,0].text(0.55, labelheight, "Median: {}".format(np.around(typical_median,2)))
        
        ax[i,1].boxplot(all_data)
        ax[i,1].title.set_text("Lunchtime included with std.dev {}".format(scale))
        ax[i,1].set_xticks([])
        labelheight = 0.75*(np.max(all_data) - np.min(all_data)) + np.min(all_data)
        ax[i,1].text(0.55, labelheight, "Median: {}".format(np.around(all_median,2)))
        
    fig.suptitle("Effect on Median with {} minute lunch".format(lunch_time))
    fig.tight_layout()
    plt.show()