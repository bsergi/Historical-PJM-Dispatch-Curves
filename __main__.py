# Main code to call run functions 
# Loads data and then organizes function calls in other scripts based on inputs
# Author: Brian Sergi
# Created: 5/31/18

## Notes 

# model takes about 2.75 hours to run on all hours in a year

# TO DO:
# Get natural gas methods 1 & 2 working
# Adjust saving functionality for dispatch curves (consider vectorizing?)
# Use summer nameplate capacity for summer months
# Add O&M costs, refine cost estimates for nuclear, oil, and biomass
# Modify so model runs easy nearest eGrid (i.e. 2017, 2016 -> 2016 eGrid; 2015, 2014 -> 2014)
# Update date functionality (simplify into tuple?)
# Complete commenting of code

## Parameters

year = 2016
savePlots = True
runName = "Test run"

## Time update function

# function to provide updates on code progress
import time
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

# load CEMS data
CEMS = readCEMS(year, eGrid)
#CEMS = pd.read_csv("Heat_Rate_Data_2017.csv")

# pre-calculate EIA average delivered fuel cost by plant to save time
monthlyPlantFuelCostData = interpolateFuelPrices(fuelData)

# pre-load natural gas prices
hubPrices = readHubGasPrices(year, eGrid)  # state-based hub prices
henryHubPrices = readhenryhuprices('Henry Hub Daily Prices 1998-2018.xls') # henry hub

timeUpdate("complete (%0.1f seconds).", start=start)

## Run model

# Data frame to store marginal plant results
marginalPlants = pd.DataFrame()

simpleDF = simplifyDF(CEMS)
gasMethod = methodSelect()

# get dates
monthDayHourList = runGetDates()


start = timeUpdate("Running dispatch model...")
print('\n')

for date in monthDayHourList:
    month,day,hour = date[0], date[1], date[2]
    print("Hour ", hour,  " on ", month, "/", day, "/", year, sep="", end="  ")

    calcMarginalCosts(simpleDF, gasMethod,year,month,day,hour,fuelData, eGrid, monthlyPlantFuelCostData, hubPrices, henryHubPrices)
    finalDF = createDispatchCurve(simpleDF, nonFossilGen, month,day,hour)
    
    # option to save specific dispatch stack to file
    #os.chdir(os.getcwd() + '/Output data')   
    #finalDF.to_csv('Dispatch_Curve - ' + "H" + str(hour) + "D" + str(day) + str(month) + str(year) + '.csv')
    #os.chdir('..') 
    
    marginalResult = findMarginalGenerator(finalDF, CEMS, year,month,day,hour, PJMload)
    marginalPlants = marginalPlants.append([marginalResult])
    
    if savePlots:
        curPlotting(finalDF, marginalResult)

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

# see accompanying scripts for post-run analysis
