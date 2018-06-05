# Script for analyzing results
# currently set up for 2016 results

## Notes

# to do: adjust LMP plot to plot multiple price results after updating methods 1 and 2

## Libraries

import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt
import seaborn as sns
import os
import datetime as dt

## Read results

os.chdir(os.getcwd() + '/Output data')   
resultsFile = "Marginal Generators All 2016.csv"
results = pd.read_csv(resultsFile, parse_dates=True, index_col=0)  
os.chdir('..') 

## Table of fuels

# calculate count by fuel
# adjust group vars to slice by other values

def fuelShareTable(results, groupVars):
    fuels = results.groupby(groupVars)[['Fuel']].count() 
    fuels = fuels / results.shape[0]
    os.chdir(os.getcwd() + '/Output analysis')   
    fuels.to_csv("Share of fuel.csv")
    os.chdir('..') 
    return fuels
    
fuelShareHourly = fuelShareTable(results, groupVars=['Hour', 'Fuel'])
fuelShareAnnual = fuelShareTable(results, groupVars=['Fuel'])


## Comparison to PJM LMP

# subset to appropriate hours to match results
def readPJMLMPs(filename, subsetHours=None):
    
    hours = []
    for i in range(1, 25):
        hours.extend([i]) 
        
    # read in LMP data
    os.chdir(os.getcwd() + '/Input raw data')   
    LMPs = pd.read_excel(filename, sheet_name="Summary", skiprows=3)
    os.chdir('..') 

    LMPs.drop(['Unnamed: 0',  'Unnamed: 1'], axis=1, inplace=True) # drop two initial columns

    i, colDict = 0, dict()
    for col in LMPs.columns:
        if i == 0:
            colDict[col] = "Date"
        else:
            colDict[col] = hours[i-1]
        i += 1
        
    # rename all columns
    LMPs.rename(columns=colDict, inplace=True)

    if subsetHours == None:
        subsetHours = hours
        
    LMPsub = LMPs[["Date"] + subsetHours]
    
    # melt date frame
    LMPmelt = LMPsub.melt(id_vars=['Date'])
    
    # add additional fields
    LMPmelt['Day'] = LMPmelt.loc[:,'Date'].apply(lambda x: x.day)
    LMPmelt['Month'] = LMPmelt.loc[:,'Date'].apply(lambda x: x.month)
    LMPmelt['Year'] = LMPmelt.loc[:,'Date'].apply(lambda x: x.year)
    
    # rename columns and sort    
    LMPmelt.rename(columns={'variable':'Hour', 'value':'LMP'}, inplace=True)
    LMPmelt = LMPmelt[ ["Date", "Hour", "Day", "Month", "Year", "LMP"] ]
    return LMPmelt
    
def mergeLMPandResults(LMPs, results):
    merged = pd.merge(LMPs, results, how = 'outer', on = ['Hour', 'Day', 'Month', 'Year'])
    return merged


# Note: rows of LMP and marginal costs must match
# set up to plot results from several runs?
def plotLMPs(mergedData, filename=None):
    
    numX = mergedData.shape[0]
    xAxis = list(range(1,numX+1))
    
    series1 = mergedData['Marginal Cost ($/MWh)'].tolist()
    series2 = mergedData['LMP'].tolist()

    MGen = plt.figure(num=None)
    ax1 = MGen.add_subplot(111)
    ax1.plot(xAxis,series2, 'b-', label = "PJM LMPs")
    ax1.plot(xAxis,series1,'r-',label='Modeled',linewidth=2)
    
    #ax1.plot(xAxis,marginalCost_3,'b-', label='Method 3')

    ax1.set_xlim((1,numX))
    ax1.set_ylim((0,1.25*max(max(series1), max(series2))))
    ax1.set_xlabel('Numbered hour of the year')
    ax1.set_ylabel('Marginal Cost ($/MWh)')  
    
    # ax2 = ax1.twinx()
    # CO2emis = df['CO2 emissions rate (tons/MWh)']
    # ax2.plot(xAxis, CO2emis, 'b--',linewidth=.5)
    # ax2.set_ylabel('CO2 Emissions Rate by the Marginal Generator (tons/MWh)')
    
    #ax1.legend()
    plt.legend()
    plt.title(filename)
    
    if filename != None:
        os.chdir(os.getcwd() + '/Output analysis')
        plt.savefig(filename + ".png")
        os.chdir('..') 
        plt.close()
    else:
        plt.show()


# read PJM LMPs
LMPs = readPJMLMPs("Summary 2016 DA Price.xlsx")        # subsetHour should be list of strings e.g. ["Hour 1", "Hour 15"]

# merge reslts and PJM LMPs
mergedResults = mergeLMPandResults(LMPs, results)

plotLMPs(mergedResults, filename='Marginal Cost vs PJM LMP - All hours for Jan-Dec 2016')


