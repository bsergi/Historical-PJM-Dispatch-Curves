# Main code to call run functions 
# Loads data and then organizes function calls in other scripts based on inputs
# Author: Brian Sergi
# Created: 5/31/18

## Libraries 
import pandas as pd
import numpy as np
import scipy

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.patches as mpatches

import dateutil.parser as parser
import datetime as dt
import calendar
import os

from MarginalCostFunction import *

## Dispatch curve plot

def getPlotInfo(dispatch, marginalResult):
    
    # colors for plotting
    fuelColors = pd.DataFrame(data={'Fuel': ['WIND', 'SOLAR', 'HYDRO', 'NUCLEAR' , 'COAL',  'GAS', 'OIL', 'OTHER'],
                                    'Color': ['#00BFFF', '#FFD700', '#4169E1', 'red', 'brown',  'orange', 'black', '#00CD00']})
                                    
    dispatch = pd.merge(dispatch, fuelColors, how="left", on="Fuel", sort=False)
    dispatch['Color'].where(~dispatch['Color'].isna(), '#00CD00', inplace=True)          # remaining NAs classified as 'OTHER'
    
    demand = marginalResult['System load (MW)']
    cost = marginalResult['Marginal Cost ($/MWh)']
    
    # left coordinate
    capacity = dispatch['Running Capacity (MW)'] - dispatch['Plant nameplate capacity (MW)']
    capacity = capacity.tolist()
    
    # right coordinate
    plantCapacity = dispatch['Running Capacity (MW)'].tolist()
    
    # height (costs)
    operatingCosts = dispatch['Marginal Cost ($/MWh)']
    operatingCosts = operatingCosts.where(operatingCosts != 0, 2).tolist()    # add small cost to zero plants so they are plotted
    
    # plot colors
    colors = dispatch['Color'].tolist()
    
    return fuelColors, demand, cost, capacity, plantCapacity, operatingCosts, colors
    
def plotDipsatchCurve(step, ax1, fuelColors, demand, cost, capacity, plantCapacity, operatingCosts, colors, marker=None):

    if step:
        operatingCosts2 = [0]
        operatingCosts2.extend(operatingCosts)
        operatingCosts2.pop()
        
        ax1.hlines(y=operatingCosts, xmin=capacity, xmax=plantCapacity, color = colors, label='Supply Curve', linewidth=1)
        ax1.vlines(x=capacity, ymin=operatingCosts2, ymax=operatingCosts, color = colors, label='Supply Curve',linewidth=1)
        
        if marker != None:
            mids = [(left + right)/2 for left, right in zip(capacity, plantCapacity)]
            ax1.scatter(mids,operatingCosts, color=colors,label='Supply Curve',marker=marker, s=5)

    else:
        ax1.bar(x=capacity, height=operatingCosts, width = plantCapacity, color=colors, 
                align="edge", linewidth=0)
    
    # lines for load and marginal cost
    ax1.plot([demand,demand],[0,cost],'k--')
    ax1.plot([0,demand],[cost,cost],'k--')
    
    ax1.set_xlim((0,max(plantCapacity)*1.01))
    # ax1.set_ylim((0,max(operatingCosts)*1.01))
    ax1.set_ylim((0,175))
        
def curvePlot(dispatch, marginalResult, show=False, step=False):
        
    fuelColors, demand, cost, capacity, plantCapacity, operatingCosts, colors = getPlotInfo(dispatch, marginalResult)
    
    supplyCurve = plt.figure(num="Figure 1")
    ax1 = supplyCurve.add_subplot(1,1,1)
    
    plotDipsatchCurve(step, ax1, fuelColors, demand, cost, capacity, plantCapacity, operatingCosts, colors)
    
    # legend
    legend_elements = []
    for i in range(0, fuelColors.shape[0]):
        legend_elements.extend([Line2D([0], [0], 
                                lw=4, label=fuelColors.loc[i,'Fuel'].lower(),
                                color=fuelColors.loc[i,'Color'])])
                               
    ax1.legend(handles=legend_elements, loc='upper left', ncol=2, frameon=False)

    plotName = "Hour " + str(marginalResult["Hour"]) + " on " + str(marginalResult["Month"]) + "-" + \
                str(marginalResult["Day"]) + "-" + str(marginalResult["Year"])
                
    plt.title(plotName)
    plt.xlabel("Capacity (MW)")
    plt.ylabel("Maginal cost ($/MWh)")
    
    if not show: 
        os.chdir(os.getcwd() + '/Output plots')
        plt.savefig(plotName + ".pdf")
        os.chdir('..') 
        plt.close()
    else:
        plt.show()
        
def curveComparisonPlot(dispatchResults, marginalResults, plotName, markers, step=True, show=False):
    
    supplyCurve = plt.figure(num="Figure 2")
    ax1 = supplyCurve.add_subplot(1,1,1)
    
    for i in range(0, len(dispatchResults)):
        fuelColors, demand, cost, capacity, plantCapacity, operatingCosts, colors = getPlotInfo(dispatchResults[i], marginalResults[i])
        
        plotDipsatchCurve(step, ax1, fuelColors, demand, cost, capacity, plantCapacity, operatingCosts, colors, marker=markers[i])
    
    # legend 2
    legend_elements2 = []
    
    for i in range(1, len(markers)+1):
        legend_elements2.extend([Line2D([0], [0], 
                                label="Method " + str(i), marker=markers[i-1],
                                color='black', markersize=10)])
                               
    plt.legend(handles=legend_elements2, loc='upper left', ncol=1, frameon=False)
    
    
                
    plt.title(plotName)
    plt.xlabel("Capacity (MW)")
    plt.ylabel("Maginal cost ($/MWh)")
    
    if not show: 
        os.chdir(os.getcwd() + '/Output plots')
        plt.savefig(plotName + ".pdf")
        os.chdir('..') 
        plt.close()
    else:
        plt.show()
    
    
    
    
        