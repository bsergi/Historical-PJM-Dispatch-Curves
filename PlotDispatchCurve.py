# Main code to call run functions 
# Loads data and then organizes function calls in other scripts based on inputs
# Author: Brian Sergi
# Created: 5/31/18

## Libraries 
import pandas as pd
import numpy as np
import scipy

import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.lines import Line2D
import matplotlib.patches as mpatches

import dateutil.parser as parser
import datetime as dt
import calendar
import os

from MarginalCostFunction import *

## Dispatch curve plot

def curPlotting(dispatch, marginalResult, show=False):
    
    demand = marginalResult['System load (MW)']
    cost = marginalResult['Marginal Cost ($/MWh)']
    
    fuelColors = {'WIND':'blue',  'SOLAR':'yellow', 'BIOMASS':'green', 
                  'COAL':'brown', 'OIL':'black', 'GAS':'orange',
                  'HYDRO':'magenta', 'NUCLEAR': 'red', 'OTHER': 'purple'}
                
    colors = []
    plantCapacity = []
    capacity = []
    operatingCosts = []
    
    for i in range(len(dispatch)):
        currentPlant = dispatch.loc[i]['Plant nameplate capacity (MW)']
        
        # left coordinate for plot
        capacity = capacity + [dispatch.loc[i]['Running Capacity (MW)'] - currentPlant]
        plantCapacity = plantCapacity + [currentPlant] 

        
        currentCost = dispatch.loc[i]['Marginal Cost ($/MWh)']
        # assign small cost to renewables and nuclear so they are plotted
        if currentCost == 0:
            operatingCosts = operatingCosts + [1]
        else:
            operatingCosts = operatingCosts + [currentCost]
        
        # fuel type of generator
        genType = dispatch.loc[i]['Plant primary coal/oil/gas/ other fossil fuel category']
        
        if genType in fuelColors:
            colors = colors + [fuelColors[genType]]
        else:
            colors = colors + ["purple"]
        
    supplyCurve = plt.figure(num="Figure 1")
    ax1 = supplyCurve.add_subplot(1,1,1)
    
    #ax1.scatter(capacity,operatingCosts,color=colors,label='Supply Curve',linewidth=2)
    ax1.bar(x=capacity, height=operatingCosts, width = plantCapacity, color=colors, 
            align="edge", linewidth=0)
    
    
    # lines for load and marginal cost
    ax1.plot([demand,demand],[0,cost],'k--')
    ax1.plot([0,demand],[cost,cost],'k--')
    
    ax1.set_xlim((0,max(capacity)*1.01))
    ax1.set_ylim((0,max(operatingCosts)*1.01))
    
    #ax1.legend()
    legend_elements = []
    for fuel in fuelColors:
    
        legend_elements.extend([Line2D([0], [0], 
                                marker='o', color='w', label=fuel.lower(),
                                markerfacecolor=fuelColors[fuel], markersize=10)])
                               
    ax1.legend(handles=legend_elements, loc='upper left', ncol=2, frameon=False)

    plotName = "Hour " + str(marginalResult["Hour"]) + " on " + str(marginalResult["Month"]) + "-" + \
                str(marginalResult["Day"]) + "-" + str(marginalResult["Year"])
                
    plt.title(plotName)
    plt.xlabel("Capacity (MW)")
    plt.ylabel("Maginal cost ($/MWh)")
    #supplyCurve.tight_layout()
    
    # could include function to save dispatch stack here for comparative plots
    if not show: 
        os.chdir(os.getcwd() + '/Output plots')
        plt.savefig(plotName + ".png")
        os.chdir('..') 
        plt.close()
    else:
        plt.show()
        