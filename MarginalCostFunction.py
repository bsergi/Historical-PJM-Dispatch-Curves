# Module for creating dispatch curve
# Author: Jadon Grove

## Notes
    
# Gas pricing method 1 currently not operational
# When first gas pricing method set up, integrate with coal method for 
# greater variability in coal prices
    
# Biomass costs: https://www.epa.gov/sites/production/files/2015-07/documents/biomass_combined_heat_and_power_catalog_of_technologies_7._representative_biomass_chp_system_cost_and_performance_profiles.pdf
# Nuclear fuel costs: https://www.eia.gov/electricity/annual/html/epa_08_04.html
# VOM costs from NREL ATB: https://atb.nrel.gov/electricity/2018/summary.html
    
# check units on PJM load data

# check date order (D-M or M-D?) between methods 2 and 3

## Libraries

import pandas as pd
import numpy as np
import scipy
import matplotlib.pyplot as plt
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
    # Drop any plants without heat rates (note: not needed since NAs will be sorted last by marginal cost) 
    # df = df.loc[~df['Heat rate (MMBtu/MWh)'].isna(), :]
    
    # SimpleDF dataframe simplifies original dataframe by removing unneeded columns
    # change primary coal to general fuel category
    simpleLabels = ['State','Facility Name','ORIS',
                    'Fuel', 'Plant nameplate capacity (MW)','Heat rate (MMBtu/MWh)', 'Gas_Hubs', 'Unit Group']
    simpleDF = df.loc[:,simpleLabels]
    
    # reset index
    simpleDF.reset_index(drop=True, inplace=True)                        

    return(simpleDF)
    
# Function to calculate operating costs in $/MWh for each plant
def calcMarginalCosts(simpleDF,gasMethod,year,month,day,hour,fuelData, eGrid, monthlyPlantFuelCostData, hubPrices, henryHubPrices):

    # different formatting for extracting coal and gas fuel info
    dateGas = str(month)+'-'+str(day)+'-'+str(year)
    dateCoal = str(month)+'/'+str(day)+'/'+str(year)
    
    # average coal price for given month
    coalPrice = coalMethodOne(dateCoal, fuelData)
    
    # Henry Hub gas price for that date (used for Method 3)
    gasPrice = gasMethodThree(dateGas,eGrid,henryHubPrices)
    
    # Estimated costs for nuclear, biomass, and oil (see sources above)
    # Could potentially include changing oil prices over time
    # Also in data: OTHF (Other fuel) -- could be number of options
    prices = pd.DataFrame(data={'Fuel': ['OIL', 'BIOMASS', 'NUCLEAR', 'COAL', 'GAS'], 
                                'Fuel Cost ($/MMBtu)': [10, 2, 7.5, coalPrice, gasPrice]})
    
    simpleDF = pd.merge(simpleDF, prices, on=['Fuel'], how='left', sort=False)      
    # gas prices: three methods available
    # Method 1: Plant-specific monthly average from EIA (under construction)
    # Method 2: State-based hub daily values
    # Method 3: Henry Hub daily values (baseline, constructed above)
    if gasMethod == 1:        
        fuelCostDataSub = monthlyPlantFuelCostData.loc[monthlyPlantFuelCostData['MONTH'] == 1, ['ORIS', 'EIA Fuel Cost']]        
        # merge montly data set
        simpleDF = pd.merge(simpleDF, fuelCostDataSub, on="ORIS", how="left", sort=False)                
        # use plant fuel cost average whenever data not missing (otherwise use fuel average values)         
        simpleDF['Fuel Cost ($/MMBtu)'].where(simpleDF['EIA Fuel Cost'].isna(), simpleDF['EIA Fuel Cost'], inplace=True)  
    elif gasMethod == 2:
        # get hub prices for specified day
        gasDF = gasMethodTwo(dateGas, hubPrices)         
        # merge hub gas prices with main data set data frame     
        simpleDF = pd.merge(simpleDF, gasDF, on="Gas_Hubs", how="left", sort=False)        
        # replace gas plants with hub-based gas prices        
        simpleDF['Fuel Cost ($/MMBtu)'].where(simpleDF['Fuel'] != 'GAS', simpleDF['Gas price'], inplace=True)   
            
    # Calculate marginal cost of operation in $/MWh for given fuel prices for given time snapshot    
    simpleDF.loc[:, "Marginal Cost ($/MWh)"] = simpleDF["Fuel Cost ($/MMBtu)"] * simpleDF["Heat rate (MMBtu/MWh)"]  
    
    # VOM in $ per MWh (from NREL 2018 ATB) (no data for oil at the moment)       
    # Note: need  to check out these are added to cost in PJM market 
    # Gas VOM depends on CT or CC                  
    VOM = pd.DataFrame(data={'Fuel': ['OIL', 'BIOMASS', 'NUCLEAR', 'COAL', 'GAS'], 
                             'VOM ($/MWh)': [0, 5, 2, 5, 3]})
                      
                                                        
    simpleDF = pd.merge(simpleDF, VOM, on=['Fuel'], how='left', sort=False)      
    
    # convert NAs to 0's
    simpleDF['VOM ($/MWh)'].where(~simpleDF['VOM ($/MWh)'].isna(), 0, inplace=True) 
    
    # assign higher price to combustion turbines
    simpleDF['VOM ($/MWh)'].where(simpleDF['Unit Group'] != "Combustion turbine", 7, inplace=True) 
    
    # add in VOM
    simpleDF.loc[:, "Marginal Cost ($/MWh)"] = simpleDF["Marginal Cost ($/MWh)"] + simpleDF['VOM ($/MWh)'] 

    return(simpleDF)
    
        
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
    
    inputString = 'What method would you like to use to determine natural gas prices? Please enter 1, 2, or 3.\n1 = EIA monthly fuel price averages\n2 = State-based daily hub values\n3 = Henry Hub daily values\nMethod choice: '
    while x == True:
        try:
            y = int(input(inputString))
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
        newRow["Fuel"] = fuel.upper()        
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
    
    sortedDF['Fuel'] = pd.Categorical(sortedDF['Fuel'],
                            ['WIND', 'SOLAR', 'HYDRO', 'NUCLEAR',  'GAS', 'COAL', 'OIL', 'STORAGE', 'OTHER RENEWABLES', 'OTHF'])
    
    sortedDF = sortedDF.sort_values(by=['Marginal Cost ($/MWh)', 'Fuel'])
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
    if load > dispatch['Running Capacity (MW)'].max() or load <= 0 or np.isnan(load):
        margin = -1
    else:
    # otherwise select first generator where cumulative capacity meets load
        margin = dispatch.loc[dispatch['Running Capacity (MW)'] >= load, 'Running Capacity (MW)'].idxmin()
                
    marginalGen = dict()
    marginalGen["Hour"], marginalGen["Day"], marginalGen["Month"], marginalGen["Year"] = hour, day, month, year  
    marginalGen["System load (MW)"] = load 
        
    if margin != -1:
        # store marginal cost and plant ID
        marginalGen["Marginal Cost ($/MWh)"] = [dispatch.loc[margin, 'Marginal Cost ($/MWh)']][0]
        marginalGen["ORIS ID"] = [dispatch.loc[margin, 'ORIS']][0]
        
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
        fuelType = df.loc[df['ORIS'] == ORIS, 'Fuel'].item()
        CO2 = df.loc[df['ORIS'] == ORIS, 'CO2 emissions rate (tons/MWh)'].item()
        SO2 = df.loc[df['ORIS'] == ORIS, 'SO2 emissions rate (tons/MWh)'].item()
        NOx = df.loc[df['ORIS'] == ORIS, 'NOx emissions rate (tons/MWh)'].item()
        
        emissionsInfo = {'Fuel': fuelType,
                        'CO2 emissions rate (tons/MWh)': CO2,
                        'NOx emisisons rate (tons/MWh)': NOx,
                        'SO2 emissions rate (tons/MWh)': SO2}    
    return emissionsInfo

    





