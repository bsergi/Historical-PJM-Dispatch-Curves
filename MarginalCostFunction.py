# Module for creating dispatch curve
# Author: Jadon Grove

## Notes
    
# Gas pricing method 1 currently not operational
# When first gas pricing method set up, integrate with coal method for 
# greater variability in coal prices
    
# Source for biomass costs: https://www.epa.gov/sites/production/files/2015-07/documents/biomass_combined_heat_and_power_catalog_of_technologies_7._representative_biomass_chp_system_cost_and_performance_profiles.pdf
    
# check units on PJM load data

# check date order (D-M or M-D?) between methods 2 and 3

## Libraries

import pandas as pd
import numpy as np
import scipy
import matplotlib.pyplot as plt
import seaborn as sns
import dateutil.parser as parser
import datetime as dt
import calendar
import os

from NaturalGasMet1 import *
from NaturalGasMet2 import *
from NaturalGasMet3 import *
from getHoursAndDates import *
# from coalPrice_methodOne import *

## Functions to calculate costs

# removes excess columns from CEMS data for ease of use
def simplifyDF(df):
    # Code below counts rows that do have heat rate values
    hrCount = 0
    for i in range(len(df)):
        val = df.loc[i]['Heat rate (MMBtu/MWh)']
        if not pd.isnull(val):
            continue
        else:
            hrCount = i-1
            break

    # SimpleDF dataframe simplifies original dataframe by removing unneeded columns
    # change primary coal to general fuel category
    simpleLabels = ['State','Facility Name','DOE/EIA ORIS plant or facility code',
        'Plant primary coal/oil/gas/ other fossil fuel category',
        'Plant nameplate capacity (MW)','Heat rate (MMBtu/MWh)','Fuel Cost ($/MMBtu)','Marginal Cost ($/MWh)']

    simpleDF = df.loc[:hrCount,simpleLabels]
    
    # reset index
    simpleDF.reset_index(drop=True, inplace=True)                        

    return(simpleDF)
    
# Function to calculate operating costs in $/MWh for each plant
def calcMarginalCosts(simpleDF,gasMethod,yr,month,day,hour,fuelData, eGrid, monthlyPlantFuelCostData, hubPrices, henryHubPrices):

    # estimate costs for oil and biomass 
    # note: nuclear cost is not a real estimate, currently a placeholder
    # source for biomass costs above
    # should include oil prices over time
    oilCost, biomassCost, nuclearCost = [10, 2, 5] # [Oil Biomass Nuclear] $/MMBtu
    
    # different formatting for extracting coal and gas fuel info
    dateGas = str(month)+'-'+str(day)+'-'+str(yr)
    dateCoal = str(month)+'/'+str(day)+'/'+str(yr)
    
    # average coal price for given month
    coalPrice = coalMethodOne(dateCoal, fuelData)
        
    # gas prices: three methods available
    # Method 1: Plant-specific monthly average from EIA (not yet running)
    # Method 2: State-based hub daily values
    # Method 3: Henry Hub daily values
    if gasMethod == 1:
        gasDF = monthlyPlantFuelCostData
    if gasMethod == 2:
        gasDF = gasMethodTwo(dateGas,eGrid, hubPrices)        
    if gasMethod == 3:
        # gasDF should become a dataframe with just NG plants, their ORIS ID,
        # a single date, and the fuel price ($/ton) for each plant
        #gasDF = gasMethodThree(dateGas,eGrid,henryHubPrices)
        gasPrice =  gasMethodThree(dateGas,eGrid,henryHubPrices)

    for i in range(len(simpleDF)):
        
        fuelType = simpleDF.loc[i, "Plant primary coal/oil/gas/ other fossil fuel category"].lower()
        ORIS_id = simpleDF.loc[i, "DOE/EIA ORIS plant or facility code"]
    
        if fuelType == "gas":
            
            if gasMethod == 1:
                # check that ORIS code is present for method 1
                gasPrice = gasDF.loc[gasDF["DOE/EIA ORIS plant or facility code"] == ORIS_id, "Prices"].item()
                simpleDF.loc[i,"Fuel Cost ($/MMBtu)"] = gasPrice
            elif gasMethod == 2:
                gasPrice = gasDF.loc[gasDF["DOE/EIA ORIS plant or facility code"] == ORIS_id, "Prices"].item()
                simpleDF.loc[i,"Fuel Cost ($/MMBtu)"] = gasPrice
            
            simpleDF.loc[i,"Fuel Cost ($/MMBtu)"] = gasPrice    
            
        elif fuelType =="coal":
            simpleDF.loc[i, "Fuel Cost ($/MMBtu)"] = coalPrice
        elif fuelType =="oil":
            simpleDF.loc[i, "Fuel Cost ($/MMBtu)"] = oilCost
        elif fuelType == "biomass":
            simpleDF.loc[i,"Fuel Cost ($/MMBtu)"] = biomassCost
        elif fuelType == "nuclear": 
            simpleDF.loc[i,"Plant nameplate capacity (MW)"] = nuclearCost
            
    
    # Calculate marginal cost of operation given fuel prices
    for i in range(len(simpleDF)):
        fuelCost = simpleDF.loc[i]["Fuel Cost ($/MMBtu)"]
        heatRate = simpleDF.loc[i]["Heat rate (MMBtu/MWh)"]
        
        # Calculate variable operating costs in $/MWh for snapshot in time
        marginalCost = fuelCost*heatRate 
        simpleDF.loc[i,"Marginal Cost ($/MWh)"] = marginalCost
        
## Coal prices

# call function to fill in missing price data
def coalMethodOne(date, fuelData):
    date = parser.parse(date)
    
    # monthly coal price average
    coalSummary = getFuelMonthlyAverage(fuelData, "Coal")
    coalPriceForDate = coalSummary[coalSummary['MONTH'] == date.month]
    
    return(coalPriceForDate.loc[:]["FUEL_COST"].item())
    
def getFuelMonthlyAverage(plants, fuel):
    # summarize cost data (mean) by month and fuel group
    df = plants.groupby(['MONTH', 'FUEL_GROUP'])['FUEL_COST'].mean().reset_index() 
    df = df[df['FUEL_GROUP']==fuel]    
    return df.reset_index()
    
## Function to select natural gas method
# This function protects against any sort of improper entries of methods
def methodSelect():
    x = True
    
    inputString = 'What method would you like to use to determine natural gas prices? Please enter 1, 2, or 3. (Note: Methods 1 and 2 currently unavailable.)\n1 = EIA monthly fuel price averages\n2 = State-based daily hub values\n3 = Henry Hub daily values\nMethod choice: '
    while x == True:
        try:
            y = int(input(inputString))
            if y == 1 or y == 2:
                print("Methods 1 and 2 are still under construction. Please select 3 :)")
            elif y == 3:
                return(y)
        except:
            continue

## Functions to build dispatch curve

# select non-fossil generation given hour + date and adds to stack       
def addNonFossilGen(plants, renewables, hour, day, month):
    sub = renewables.loc[(renewables["Hour"] == hour) & (renewables["Day"] == day) & (renewables["Month"] == month),]
    
    blankRow = dict.fromkeys(plants.columns.tolist())
    blankRow['Marginal Cost ($/MWh)'] = 0
    
    for fuel in sub["fuel_type"].unique().tolist():
        newRow = blankRow.copy()
        newRow["Plant primary coal/oil/gas/ other fossil fuel category"] = fuel.upper()        
        newRow["Plant nameplate capacity (MW)"]  = sub.loc[sub["fuel_type"] == fuel, "mw"].reset_index(drop=True)[0]
        
        plants = pd.concat([pd.DataFrame([newRow]), plants], ignore_index = True)
        
    return plants

# caclulate running capacity total for system   
def sumCapacity(sortedDF):
    sortedDF['Running Capacity (MW)'] = 0
    countCapacity = 0
    for i in range(len(sortedDF)):
        countCapacity += sortedDF.loc[i]['Plant nameplate capacity (MW)']
        sortedDF.loc[i, 'Running Capacity (MW)'] = countCapacity
    # sortedDF.to_csv('MarginalCost.csv')
    return(sortedDF)
    
# creates dispatch stack by sorting on marginal costs
# adds in actual generation by renewables
def createDispatchCurve(simpleDF, renewables, month,day,hour): 
    sortedDF = addNonFossilGen(simpleDF, renewables, hour, day, month)
    sortedDF = sortedDF.sort_values(by=['Marginal Cost ($/MWh)'])
    sortedDF = sortedDF.reset_index(drop=True)
    return(sumCapacity(sortedDF))



## Identify marginal generator

# get PJM load at given time
def loadCall(date,hour,demand):
    # For gethourlydemand(x,y), x needs to be the desired date in proper formatting, 
    # and y needs to be the hour in PJM semantics
    if int(hour) < 10:
        y = 'HE0' + str(hour)
    else:
        y = 'HE' + str(hour)
    load_of_inputDate=gethourlydemand(date,y,demand)
    return (load_of_inputDate)
    
def gethourlydemand(date,hourtype,df):
    df1 = (df.loc[date][hourtype])
    return (df1)

    
# identify marginal generator at given time
def findMarginalGenerator(dispatch, CEMS, year, month, day, hour, demand):
    
    # call to get load
    loadDate = str(month)+'/'+str(day)+'/'+str(year)
    load = loadCall(loadDate, hour, demand)
    print("System load %0.1f MW" % load)
    
    margin = 0
    loadServed = 0
    
    # check that load is not zero or above total capacity  
    if load > dispatch['Running Capacity (MW)'].max() or load <= 0:
        margin = -1
    
    while margin < len(dispatch) and loadServed < load and margin != -1:
        loadServed = dispatch.loc[margin]['Running Capacity (MW)']
        margin += 1
        
    marginalGen = dict()
    marginalGen["Hour"], marginalGen["Day"], marginalGen["Month"], marginalGen["Year"] = hour, day, month, year  
    marginalGen["System load (MW)"] = load 
        
    if margin != -1:
        # store marginal cost and plant ID
        marginalGen["Marginal Cost ($/MWh)"] = [dispatch.loc[margin, 'Marginal Cost ($/MWh)']][0]
        marginalGen["ORIS ID"] = [dispatch.loc[margin, 'DOE/EIA ORIS plant or facility code']][0]
        
        # find fuel type and marginal emissions info        
        emissions = genEmissionsInfo(CEMS, marginalGen["ORIS ID"], margin)
        marginalGen.update(emissions)
    else:
        marginalGen["Marginal Cost ($/MWh)"] = None
        marginalGen["ORIS ID"] = None
        
        marginalGen.update({'Fuel': None,
                            'CO2 emissions rate (tons/MWh)': None,
                            'NOx emisisons rate (tons/MWh)': None,
                            'SO2 emissions rate (tons/MWh)': None})

    return marginalGen
    
    
# extract emissions information on marginal generator
def genEmissionsInfo(df, ORIS, margin):
    if ORIS == None:
        emissionsInfo = {'Fuel': "Non-fossil",
                        'CO2 emissions rate (tons/MWh)': 0,
                        'NOx emisisons rate (tons/MWh)': 0,
                        'SO2 emissions rate (tons/MWh)': 0}
    else:            
        fuelType = df.loc[df['DOE/EIA ORIS plant or facility code'] == ORIS, 'Plant primary coal/oil/gas/ other fossil fuel category'].item()
        CO2 = df.loc[df['DOE/EIA ORIS plant or facility code'] == ORIS, 'CO2 emissions rate (tons/MWh)'].item()
        SO2 = df.loc[df['DOE/EIA ORIS plant or facility code'] == ORIS, 'SO2 emissions rate (tons/MWh)'].item()
        NOx = df.loc[df['DOE/EIA ORIS plant or facility code'] == ORIS, 'NOx emissions rate (tons/MWh)'].item()
        
        emissionsInfo = {'Fuel': fuelType,
                        'CO2 emissions rate (tons/MWh)': CO2,
                        'NOx emisisons rate (tons/MWh)': NOx,
                        'SO2 emissions rate (tons/MWh)': SO2}    
    return emissionsInfo

    





