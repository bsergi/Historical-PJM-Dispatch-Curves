# Code to load and process CEMS data
# Author: Brian Sergi
# Created: Feb 26 2018
# Updated: March 6, 2018

import numpy as np
import pandas as pd
import string
import xlrd
import os
import re

## NOTES
# Emissions, gross load, and heat input currently summarized at plant level
# We have unit level in CEMS but this doesn't match cleaning with the data in eGrid

# Currently set up with 2017 CEMS data and 2014 eGrid data

# There are some fossil plants that are in eGrid that aren't in CEMS (these may be retirements)
# eGrid plant totals may also be too high (include retired generators)

# Need to investigate the validity of CEMS heat input data (is this max value truly representative of plant efficiency?)


## FUNCTIONS

def readCEMSfacility(filename):
    
    # reads data at unit level     
    os.chdir(os.getcwd() + '/Input raw data')   
    CEMSData = pd.read_csv(filename, parse_dates=True)    
    os.chdir('..')   

    # remove leading/trailing whitespace from column names
    CEMSData.columns = [x.strip() for x in CEMSData.columns]   
    
    # subset to relevant columns
    labels = ['State', 'Facility Name', 'Facility ID (ORISPL)', 
              'County', 'FIPS Code','Source Category', 'Fuel Type (Primary)',
              'Fuel Type (Secondary)', 'Commercial Operation Date', 'Unit ID',
              'Operating Status', 'Max Hourly HI Rate (MMBtu/hr)']
    CEMSData = CEMSData.loc[:,CEMSData.columns.intersection(labels)]
    
    # subset to electric utilities (exclude industrial boilers)
    CEMSData = CEMSData[CEMSData['Source Category'].isin(['Electric Utility',
                                                          'Cogeneration', 
                                                          'Small Power Producer'])]
    # summarize heat input at facility level 
    CEMSData = CEMSData.groupby(['State', 'Facility Name', 'Facility ID (ORISPL)',
                                'County', 'FIPS Code','Source Category'])[['Max Hourly HI Rate (MMBtu/hr)']].sum()
    CEMSData.reset_index(level=CEMSData.index.names, inplace=True)                        
    
    return CEMSData
    
def readCEMSEmissions(filename,time="annual"):    
    # reads annual emissions summary
    if time == "annual":   
        os.chdir(os.getcwd() + '/Input raw data')   
        CEMSData = pd.read_csv(filename, parse_dates=True) 
        os.chdir('..')    
        # remove leading/trailing whitespace from column names
        CEMSData.columns = [x.strip() for x in CEMSData.columns] 
        
        labels = ['State', 'Facility Name', 'Facility ID (ORISPL)', 'Unit ID', 'Unit Type', 
                'County', "Gross Load (MW-h)", "SO2 (tons)", "NOx (tons)", "CO2 (short tons)"]
        CEMSData = CEMSData.loc[:,CEMSData.columns.intersection(labels)]
        
        # mapping of unit types
        CEMSData["Unit Type"] = CEMSData["Unit Type"].str.replace(" \(.*\)", "")
        
        units = pd.DataFrame(data={'Unit Type': ['Combustion turbine', 'Tangentially-fired', 'Combined cycle',
                                                 'Dry bottom wall-fired boiler', 'Cell burner boiler',
                                                 'Other turbine', 'Dry bottom turbo-fired boiler', 'Stoker',
                                                 'Other boiler', 'Circulating fluidized bed boiler',
                                                 'Dry bottom vertically-fired boiler', 'Cyclone boiler',
                                                 'Wet bottom turbo-fired boiler', 'Bubbling fluidized bed boiler',
                                                 'Integrated gasification combined cycle',
                                                 'Wet bottom wall-fired boiler'],
                                   'Unit Group':['Combustion turbine', 'Coal boiler', 'Combined cycle',
                                                 'Coal boiler', 'Coal boiler',
                                                 'Combustion turbine', 'Coal boiler', 'Coal boiler',
                                                 'Coal boiler', 'Coal boiler',
                                                 'Coal boiler', 'Coal boiler',
                                                 'Coal boiler', 'Coal boiler',
                                                 'IGCC','Coal boiler']})
                                                 
        CEMSData = pd.merge(CEMSData, units, how="left", sort=False, on="Unit Type")
        
        # find generation by unit type
        genSummary = CEMSData.groupby(['Facility ID (ORISPL)','Unit Group'])["Gross Load (MW-h)"].sum().reset_index()
        
        # take generator type that produces most electricity
        genSummary.sort_values(by=['Facility ID (ORISPL)', 'Gross Load (MW-h)'], ascending=[True, False], inplace=True)
        
        genSummary = genSummary.loc[~genSummary.duplicated(subset=['Facility ID (ORISPL)'], keep='first'), :]

        
        # summarize emissions at facility level 
        CEMSData = CEMSData.groupby(['State', 'Facility Name', 
                                     'Facility ID (ORISPL)', 'County']).agg({"SO2 (tons)": sum,
                                                                             "NOx (tons)": sum,
                                                                             "CO2 (short tons)": sum,
                                                                             "Gross Load (MW-h)": sum})
                                                                                                                                                          
        CEMSData.reset_index(level=CEMSData.index.names, inplace=True) 
        
        # merge in primary unit type
        CEMSData = pd.merge(CEMSData, genSummary[["Facility ID (ORISPL)", "Unit Group"]], how="left", on = "Facility ID (ORISPL)", sort=False)                                                                    

        return CEMSData

def mergeFacilityEmissions(CEMS, emissions):
    # merge CEMS facility and emmissions data
    commonColumns = ['State', 'Facility Name',  'Facility ID (ORISPL)', 'County']
    CEMS = pd.merge(CEMS, emissions, how = 'outer', 
                    left_on = commonColumns, right_on = commonColumns)
    return CEMS
    

def mergeCEMSandEGRID(CEMS, eGrid):
    # merge CEMS and eGrid data
    CEMS = pd.merge(CEMS, eGrid, how = 'left', 
                    left_on = 'Facility ID (ORISPL)', right_on = 'ORIS')    
    return CEMS
    

def calcPJMcapacity(CEMS):
    # subset to PJM plants
    return  CEMS[CEMS['Balancing Authority Code'] == 'PJM']    

# calculate max heat rate (mmBTU per MWh) 
def calcHeatRate(CEMS, eGridHR=False):  

    # adjust heat rates > 100000 and ensure all heat rates are positive
    # see https://www.eia.gov/electricity/annual/html/epa_08_01.html for example of average heat rates
    CEMS.loc[CEMS['Plant nominal heat rate (Btu/kWh)'] > 100000, 'Plant nominal heat rate (Btu/kWh)'] = np.nan    
    CEMS['Plant nominal heat rate (Btu/kWh)'] = CEMS['Plant nominal heat rate (Btu/kWh)'].abs()

    if eGridHR:
        # convert eGrid heat rates from Btu/kWh to mmbtu/MWh
        CEMS['Heat rate (MMBtu/MWh)'] = CEMS['Plant nominal heat rate (Btu/kWh)'] / 1000         
    else:
        # for fossil plants in CEMS, heat rate = max hourly heat input (plant total) divided by plant nameplate capacity
        CEMS['Heat rate (MMBtu/MWh)'] = CEMS['Max Hourly HI Rate (MMBtu/hr)'] /  CEMS['Plant nameplate capacity (MW)'] 
        
    CEMS['Heat rate (MMBtu/MWh)'] = pd.to_numeric(CEMS['Heat rate (MMBtu/MWh)'])    
    
    # fill in missing heat rates with fuel averages
    heatRateSummary = CEMS.groupby(['Fuel'])['Heat rate (MMBtu/MWh)'].mean().reset_index()    
    heatRateSummary.rename(columns={'Heat rate (MMBtu/MWh)':'Fuel average heat rate'}, inplace=True)
    CEMS = pd.merge(CEMS, heatRateSummary, how = 'outer', on = ['Fuel'])
    
    CEMS['Heat rate (MMBtu/MWh)'].where(~CEMS['Heat rate (MMBtu/MWh)'].isna(), CEMS['Fuel average heat rate'], inplace=True)
                
    return CEMS
    
def calcEmissionsRates(plants):
    # convert short tons to metric tons
    shortToMetric = 0.907185
    plants['CO2 (short tons)'] = plants['CO2 (short tons)'] * shortToMetric
    plants.rename(columns={'CO2 (short tons)': 'CO2 (tons)'}, inplace=True)
    
    # calculate emissions rates
    plants['SO2 emissions rate (tons/MWh)'] = plants['SO2 (tons)'] / plants['Gross Load (MW-h)']
    plants['NOx emissions rate (tons/MWh)'] = plants['NOx (tons)'] / plants['Gross Load (MW-h)']
    plants['CO2 emissions rate (tons/MWh)'] = plants['CO2 (tons)'] / plants['Gross Load (MW-h)']
    
    plantsSub = plants.replace([np.inf, -np.inf, 0], np.nan)
    plantsSub = plantsSub.dropna(subset=['NOx emissions rate (tons/MWh)', 
                                                    'SO2 emissions rate (tons/MWh)', 
                                                    'CO2 emissions rate (tons/MWh)'], how="all")
                                                    
    
    # calculate average rates by fuel 
    emissions = plantsSub.groupby(['Fuel'])['NOx emissions rate (tons/MWh)', 
                                                    'SO2 emissions rate (tons/MWh)', 
                                                    'CO2 emissions rate (tons/MWh)'].mean().reset_index()
                 
    # sanity check needed here
    emissions.rename(columns={'NOx emissions rate (tons/MWh)': 'Average NOx emissions rate by fuel',
                              'SO2 emissions rate (tons/MWh)': 'Average SO2 emissions rate by fuel',
                              'CO2 emissions rate (tons/MWh)': 'Average CO2 emissions rate by fuel'}, inplace=True)
    
    # merge group emissions summary
    plants = pd.merge(plants, emissions, how = 'outer', on = ['Fuel'])

    # iterate through rows and replace if missing or zero
    pollColNames = (['NOx emissions rate (tons/MWh)',
                     'SO2 emissions rate (tons/MWh)',
                     'CO2 emissions rate (tons/MWh)'],
                    ['Average NOx emissions rate by fuel',
                    'Average SO2 emissions rate by fuel', 
                    'Average CO2 emissions rate by fuel'])
         
    # iterate through plants
    for id in range(0, plants.shape[0]):
        
        # cycle through three emissions
        for poll in range(0, 3):        
            rate = plants.iloc[id, plants.columns.get_loc(pollColNames[0][poll])]
            # check if missing value
            if rate == 0 or np.isnan(rate) or np.isinf(rate):
                # replace with fuel average
                newRate = plants.iloc[id, plants.columns.get_loc(pollColNames[1][poll])]
                plants.iloc[id, plantsSub.columns.get_loc(pollColNames[0][poll])] = newRate
                
    return plants


