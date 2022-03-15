# -*- coding: utf-8 -*-
"""
Code for visualizing box plot data as a target
Created on Fri Mar 11 09:40:34 2022

@author: Ryan.Larson
"""

import matplotlib.pyplot as plt
import numpy as np


# def get_dists(target:tuple, x, y):
#     """
#     Get the linear distance to each point using Pythagorean theorem, and output
#     a list of distances.

#     Parameters
#     ----------
#     target : tuple
#         DESCRIPTION.
#     x : TYPE
#         DESCRIPTION.
#     y : TYPE
#         DESCRIPTION.

#     Returns
#     -------
#     None.

#     """
#     # Make sure x and y are lists
#     x = list(x)
#     y = list(y)
    
#     target_x = target[0]
#     target_y = target[1]
    
#     dists = []
#     for i in range(len(x)):
#         dist = np.sqrt((x[i]-target_x)**2 + (y[i]-target_y)**2)
#         dists.append(dist)
        
#     return dists
        
def plot_target(fig, axes, subplot_m, subplot_n, target_center:tuple):
    circle_1 = plt.Circle(target_center, 1, fill=False)
    circle_2 = plt.Circle(target_center, 2, fill=False)
    circle_3 = plt.Circle(target_center, 3, fill=False)
    circle_4 = plt.Circle(target_center, 4, fill=False)
    circle_5 = plt.Circle(target_center, 5, fill=False)

    axes[subplot_m, subplot_n].set_aspect(1)
    axes[subplot_m, subplot_n].add_artist(circle_1)
    axes[subplot_m, subplot_n].add_artist(circle_2)
    axes[subplot_m, subplot_n].add_artist(circle_3)
    axes[subplot_m, subplot_n].add_artist(circle_4)
    axes[subplot_m, subplot_n].add_artist(circle_5)
    axes[subplot_m, subplot_n].set_xlim(-6,6)
    axes[subplot_m, subplot_n].set_ylim(-6,6)
    



target_center = (0,0)

##### Accurate but spread examples #####
figure1, axes1 = plt.subplots(3,2)
figure1.set_size_inches(8.5, 11)
figure1.set_dpi(300)

npts = 50

# Accurate shots
plot_target(figure1, axes1, 0, 0, target_center)
accurate_data = np.random.normal(loc=0.0, scale=0.35, size=(npts,2))
axes1[0,0].scatter(accurate_data[:,0], accurate_data[:,1])
axes1[0,0].set_xticks([])
axes1[0,1].boxplot(accurate_data[:,1])
axes1[0,1].set_ylim(-6,6)
axes1[0,1].set_xticks([])
# axes1[0,1].grid(True)


# Medium accurate shots
plot_target(figure1, axes1, 1, 0, target_center)
med_accurate_data = np.random.normal(loc=0.0, scale=0.85, size=(npts,2))
axes1[1,0].scatter(med_accurate_data[:,0], med_accurate_data[:,1])
axes1[1,0].set_xticks([])
axes1[1,1].boxplot(med_accurate_data[:,1])
axes1[1,1].set_ylim(-6,6)
axes1[1,1].set_xticks([])
# axes1[1,1].grid(True)


# Inaccurate shots
plot_target(figure1, axes1, 2, 0, target_center)
inaccurate_data = np.random.normal(loc=0.0, scale=1.75, size=(npts,2))
axes1[2,0].scatter(inaccurate_data[:,0], inaccurate_data[:,1])
axes1[2,0].set_xticks([])
axes1[2,1].boxplot(inaccurate_data[:,1])
axes1[2,1].set_ylim(-6,6)
axes1[2,1].set_xticks([])
# axes1[2,1].grid(True)



##### Shifted shots #####
figure2, axes2 = plt.subplots(3,2)
figure2.set_size_inches(8.5, 11)
figure2.set_dpi(300)

# Accurate, upward shifted shots
plot_target(figure2, axes2, 0, 0, target_center)
accurate_data_x = np.random.normal(loc=0.0, scale=0.5, size=(npts))
accurate_data_y = np.random.normal(loc=2.0, scale=0.5, size=(npts))
axes2[0,0].scatter(accurate_data_x, accurate_data_y)
axes2[0,0].set_xticks([])
axes2[0,1].boxplot(accurate_data_y)
axes2[0,1].set_ylim(-6,6)
axes2[0,1].set_xticks([])
# axes2[0,1].grid(True)

# Accurate, more upward shifted shots
plot_target(figure2, axes2, 1, 0, target_center)
accurate_data_x = np.random.normal(loc=0.0, scale=0.5, size=(npts))
accurate_data_y = np.random.normal(loc=4.0, scale=0.5, size=(npts))
axes2[1,0].scatter(accurate_data_x, accurate_data_y)
axes2[1,0].set_xticks([])
axes2[1,1].boxplot(accurate_data_y)
axes2[1,1].set_ylim(-6,6)
axes2[1,1].set_xticks([])
# axes2[1,1].grid(True)

# Accurate, downward shifted shots
plot_target(figure2, axes2, 2, 0, target_center)
accurate_data_x = np.random.normal(loc=0.0, scale=0.5, size=(npts))
accurate_data_y = np.random.normal(loc=-3.0, scale=0.5, size=(npts))
axes2[2,0].scatter(accurate_data_x, accurate_data_y)
axes2[2,0].set_xticks([])
axes2[2,1].boxplot(accurate_data_y)
axes2[2,1].set_ylim(-6,6)
axes2[2,1].set_xticks([])
# axes2[2,1].grid(True)

plt.show()

