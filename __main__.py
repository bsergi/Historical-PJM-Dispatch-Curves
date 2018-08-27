# Main code to call run functions 
# Loads data and then organizes function calls in other scripts based on inputs
# Author: Brian Sergi
# Created: 5/31/18
# Modified: 7/13/18

## Notes 

# model takes about 45 minutes to run on all hours in a year
# use 'runModel' call for basic run; see comparison functions below for other otpions

# TO DO:
# Use summer nameplate capacity for summer months
# Modify so model runs easy nearest eGrid (i.e. 2017, 2016 -> 2016 eGrid; 2015, 2014 -> 2014)

## Parameters

# baseWD =  '/Users/Cartographer/Documents/Carnegie Mellon/Box Sync/Research/Dispatch curves/Final model/runModel'
year = 2016

saveDates = [[8,15,18]]          # list of dates to save plots/dispatch curve data (date format: [m,d,h])

## Time update function

# function to provide updates on code progress
import time
import os 

# os.chdir(baseWD)

def timeUpdate(update, start=None):
    if start == None:
        print(update, end="")
        return time.time()
    else:
        elapsed = time.time() - start
        print(update % elapsed)
        
## Libraries

start = timeUpdate("Loading libraries...")

import pandas as pd
import numpy as np
import scipy
import matplotlib.pyplot as plt
import seaborn as sns
import dateutil.parser as parser
import datetime as dt
import calendar

from NaturalGasMet1 import *
from NaturalGasMet2 import *
from NaturalGasMet3 import *
from getHoursAndDates import *
from LoadData import *
from MarginalCostFunction import *
from PlotDispatchCurve import *

timeUpdate("complete (%0.1f seconds).", start=start)

pd.set_option("display.max_columns",10)

## Pre-load variables

start = timeUpdate("Loading data sets...")

# load renewables data from PJM
PJMload = readhourlydemand(r'2016-hourly-loads.xls')
nonFossilGen = readNonFossilGen(year)

# load fuel pricing data from EIA
os.chdir(os.getcwd() + '/Input raw data')   
fuel = pd.read_excel("EIA923_Schedules_2_3_4_5_M_12_2016_Final_Revision.xlsx",sheet_name = "Page 5 Fuel Receipts and Costs", skiprows=4)
generators = pd.read_excel("EIA923_Schedules_2_3_4_5_M_12_2016_Final_Revision.xlsx", sheet_name = "Page 4 Generator Data", skiprows=5)
os.chdir('..') 
fuelData = read923(fuel, generators)

# load eGrid data
eGrid = readEGridPlant(year)
eGrid = calcRetiredGen(year, eGrid)

# load CEMS data
CEMS = readCEMS(year, eGrid, eGridHR=False)

#CEMS = pd.read_csv("Heat_Rate_Data_2017.csv")

# pre-calculate EIA average delivered fuel cost by plant to save time
monthlyPlantFuelCostData = interpolateFuelPrices(fuelData)

# pre-load natural gas prices
CEMS, hubPrices = readHubGasPrices(year, CEMS)  # state-based hub prices
henryHubPrices = readhenryhuprices('Henry Hub Daily Prices 1998-2018.xls') # henry hub

timeUpdate("complete (%0.1f seconds).", start=start)


## Run model

def runModel(runName, saveDates):
    # Data frame to store marginal plant results
    marginalPlants = pd.DataFrame()
    
    # select gas method (input from user)
    gasMethod = methodSelect()
    
    # get dates (input from user)
    monthDayHourList = runGetDates()
    
    start = timeUpdate("Running dispatch model...")
    print('\n')
    
    for date in monthDayHourList:
        month,day,hour = date[0], date[1], date[2]
        print("Hour ", hour,  " on ", month, "/", day, "/", year, sep="", end="  ")
    
        simpleDF = simplifyDF(CEMS)
        simpleDF = calcMarginalCosts(simpleDF, gasMethod, year, month, day, hour, fuelData, eGrid, monthlyPlantFuelCostData, hubPrices, henryHubPrices)
        finalDF = createDispatchCurve(simpleDF, nonFossilGen, month,day,hour)
        
        marginalResult = findMarginalGenerator(finalDF, CEMS, year,month,day,hour, PJMload)
        marginalPlants = marginalPlants.append([marginalResult])
        
        if date in saveDates:
            # option to save specific dispatch stack to file
            os.chdir(os.getcwd() + '/Output data')   
            finalDF.to_csv('Hour ' + str(hour) + " on " + str(month) + "-" + str(day) + "-" + str(year) + '.csv')
            os.chdir('..') 
        
            curvePlot(finalDF, marginalResult)
    
    # set column order
    labels = ['Hour', 'Day', 'Month', 'Year', 
            'System load (MW)', 'ORIS ID', 'Fuel', 'Marginal Cost ($/MWh)',
            'CO2 emissions rate (tons/MWh)', 'NOx emisisons rate (tons/MWh)',
            'SO2 emissions rate (tons/MWh)']
    marginalPlants = marginalPlants[labels]
    
    os.chdir(os.getcwd() + '/Output data')   
    marginalPlants.to_csv('Marginal Generators ' + runName + '.csv', index=False)  
    os.chdir('..')   
    
    timeUpdate("Dispatch model complete (%0.1f seconds).", start=start)
    print("Analysis complete.")

# runModel("Method 2 Full", saveDates)
# see accompanying scripts for post-run analysis

## Comparison functions

# function to compare dispatch curve from three fuel cost methods for a given date
def methodComparison(date, year, CEMS, fuelData, eGrid, monthlyPlantFuelCostData, hubPrices, henryHubPrices, PJMload, nonFossilGen):
    month,day,hour = date[0], date[1], date[2]
    print("Hour ", hour,  " on ", month, "/", day, "/", year, sep="")
    
    marginalResults = []
    dispatchResults = []
    
    for gasMethod in range(1, 4):
        
        simpleDF = simplifyDF(CEMS)
        simpleDF = calcMarginalCosts(simpleDF, gasMethod, year, month, day, hour, fuelData, eGrid, monthlyPlantFuelCostData, hubPrices, henryHubPrices)
        finalDF = createDispatchCurve(simpleDF, nonFossilGen, month,day,hour)
        
        marginalResult = findMarginalGenerator(finalDF, CEMS, year,month,day,hour, PJMload)
        
        marginalResults.extend([marginalResult])
        dispatchResults.extend([finalDF])
    
    plotName = "Method comparison for hour " + str(hour) +  " on " + str(month) + "-" + str(day) + "-" + str(year)
    markers = ["o", ">", "s"]
    curveComparisonPlot(dispatchResults, marginalResults, plotName, markers)
    return(marginalResults)
    
# date = monthDayHourList[0]     
# methodComparison(date, year, CEMS, fuelData, eGrid, monthlyPlantFuelCostData, hubPrices, henryHubPrices, PJMload, nonFossilGen)

# function to compare dispatch curves from multiple dates
def dateComparison(dates, year, gasMethod, CEMS, fuelData, eGrid, monthlyPlantFuelCostData, hubPrices, henryHubPrices, PJMload, nonFossilGen, markers, plotName):
    
    marginalResults = []
    dispatchResults = []
        
    for date in dates:
    
        month,day,hour = date[0], date[1], date[2]
        print("Hour ", hour,  " on ", month, "/", day, "/", year, sep="")
        
        simpleDF = simplifyDF(CEMS)
        simpleDF = calcMarginalCosts(simpleDF, gasMethod, year, month, day, hour, fuelData, eGrid, monthlyPlantFuelCostData, hubPrices, henryHubPrices)
        finalDF = createDispatchCurve(simpleDF, nonFossilGen, month,day,hour)
        
        marginalResult = findMarginalGenerator(finalDF, CEMS, year,month, day, hour, PJMload)
        
        marginalResults.extend([marginalResult])
        dispatchResults.extend([finalDF])
    
    curveComparisonPlot(dispatchResults, marginalResults, plotName, markers)
    return(marginalResults)

# function to compare dispatch curves using different heat rate approaches
def heatRateComparison(dates, year, gasMethod, fuelData, eGrid, monthlyPlantFuelCostData, henryHubPrices, PJMload, nonFossilGen):

    marginalResults = []
    dispatchResults = []
            
    month,day,hour = date[0], date[1], date[2]
    print("Hour ", hour,  " on ", month, "/", day, "/", year, sep="")
    
    for boolHR in [False, True]:
        CEMS = readCEMS(year, eGrid, eGridHR=boolHR)
        CEMS, hubPrices = readHubGasPrices(year, CEMS)  

        simpleDF = simplifyDF(CEMS)
        simpleDF = calcMarginalCosts(simpleDF, gasMethod, year, month, day, hour, fuelData, eGrid, monthlyPlantFuelCostData, hubPrices, henryHubPrices)
        finalDF = createDispatchCurve(simpleDF, nonFossilGen, month,day,hour)
        
        marginalResult = findMarginalGenerator(finalDF, CEMS, year, month, day, hour, PJMload)
        
        marginalResults.extend([marginalResult])
        dispatchResults.extend([finalDF])
        
    plotName = "Heat rate comparison for hour " + str(hour) +  " on " + str(month) + "-" + str(day) + "-" + str(year)
    markers = ["o", ">"]
    curveComparisonPlot(dispatchResults, marginalResults, plotName, markers)
    return(marginalResults)

#resultsHR = heatRateComparison(date, year, gasMethod, fuelData, eGrid, monthlyPlantFuelCostData, henryHubPrices, PJMload, nonFossilGen)
#pd.DataFrame(resultsHR)