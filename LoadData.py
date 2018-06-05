# Script for data loading functions
# Author: Brian Sergi
# Created: 5/31/18

import pandas as pd
import os
import scipy
from CEMSProcessing import * 

## Notes

# When using new CEMS data, pre-processing must be done to avoid blank rows in the 
# first row of the data (this causes off-by-one error for columns)

## Functions to read in data sets
def readhourlydemand(file):
    os.chdir(os.getcwd() + '/Input raw data')   
    Energy_price = pd.ExcelFile(file) #Read Excel Data from my original data base
    os.chdir('..') 
    dataframe = Energy_price.parse('RTO') #Read only the tab name RTO
    dataframe2=dataframe.set_index('DATE') #Change the row index such that the date column in the data frame now becomes row label
    return dataframe2
    
def readNonFossilGen(year):
    file = "PJM_gen_by_fuel_" + str(year) + ".csv"
    
    os.chdir(os.getcwd() + '/Input raw data')   
    nonFossil = pd.read_csv(file)
    os.chdir('..') 
    
    nonFossil = splitDateHour(nonFossil)
    nonFossil = subsetRenewables(nonFossil)
    
    return nonFossil
    
def splitDateHour(data):
    # EPT = Eastern Prevailing Time
    data['timedate'] = pd.to_datetime(data['datetime_beginning_ept'])
    data['Hour'] = data.loc[:,'timedate'].apply(lambda x: x.hour)
    data['Day'] = data.loc[:,'timedate'].apply(lambda x: x.day)
    data['Month'] = data.loc[:,'timedate'].apply(lambda x: x.month)
    data['Year'] = data.loc[:,'timedate'].apply(lambda x: x.year)
    
    data = data.sort_values(by='timedate').reset_index(drop=True)

    return data
    
def subsetRenewables(data):
    # use PJM "is_renewable" flag
    # sub = data.loc[data['is_renewable'],:]
    
    # use actual generation from wind, solar, hydro, and nuclear
    fuels = ['Hydro', 'Solar', 'Wind', 'Nuclear', 'Other Renewables','Storage']
       
    sub = data.loc[data["fuel_type"].isin(fuels)]
    return sub    
    # further work could also make use of nuclear generation, and compare actual
    # coal/gas generation to predictions
    
# combined with eGrid function from marginal cost function
def readEGridPlant(eGridYear):
    filenameEGRID = "egrid" + str(eGridYear) + "_data.xlsx"
    sheetName = "PLNT" + str(eGridYear % 100) 
    
    os.chdir(os.getcwd() + '/Input raw data')   
    eGrid = pd.read_excel(pd.ExcelFile(filenameEGRID), sheetName)
    os.chdir('..') 
    #eGrid = readEGrid(filenameEGRID, sheetName)  
    #eGrid data takes about 30 seconds to load   
    
    #Plantdatabase = EGRID_Data.parse('PLNT16')
    labels = ['Plant name', 'DOE/EIA ORIS plant or facility code',
              'Plant state abbreviation', 'Balancing Authority Code',
              'Plant primary fuel','Plant primary coal/oil/gas/ other fossil fuel category',
              'Plant capacity factor', 'Plant nameplate capacity (MW)']
    eGrid = eGrid.loc[:, eGrid.columns.intersection(labels)]
    pjmplants=eGrid[eGrid['Balancing Authority Code'] == 'PJM']
    return pjmplants
    
def readCEMS(CEMSyear, eGrid):
    
    # CEMS at unit level, eGrid capacity data (MW) at plant level
    filenameCEMSfacility = "CEMS facility data " + str(CEMSyear) + ".csv"    
    filenameCEMSemissions = "CEMS emissions data " + str(CEMSyear) + ".csv"  
    
    # facility data
    CEMS = readCEMSfacility(filenameCEMSfacility)
    # emissions data
    annualEmissions = readCEMSEmissions(filenameCEMSemissions)
    
    # combine and merge with eGrid (only fossil)
    CEMS = mergeFacilityEmissions(CEMS, annualEmissions)
    plants = mergeCEMSandEGRID(CEMS, eGrid)
    plants = calcPJMcapacity(plants)
    plants = calcHeatRate(plants)
    plants = calcEmissionsRates(plants)
    
    # sort by heat rate
    plants = plants.sort_values(by=['Heat rate (MMBtu/MWh)'])
        
    # save to csv
    os.chdir(os.getcwd() + '/Output data')   
    plants.to_csv("Heat rate data " + str(CEMSyear) + ".csv", index=False)
    os.chdir('..') 

    plants['Fuel Cost ($/MMBtu)'] = 0
    plants['Marginal Cost ($/MWh)'] = 0
    
    return plants
    

def read923(fuel, generators):    
    # read fuel data
    fuel = fuel[["YEAR", "MONTH", "Plant Id", "Plant Name", "Plant State", 
                "Purchase Type", "FUEL_GROUP", "FUEL_COST", "ENERGY_SOURCE",
                "Natural Gas Supply Contract Type", "Natural Gas Delivery Contract Type"]]
    
    # FUEL_GROUP = Natural gas, Coal, Petroleum, Petroleum Coke, [missing]
    # Energy Source = more specific fuel info, mostly for coal (e.g. Anthtracite, bituminous, 
    # FUEL_COST = "All costs incurred in the purchase and delivery of the fuel to the plant in cents per million Btu(MMBtu) to the nearest 0.1 cent. Numeric."
    # Purchase type = C: contract, NC: new contract, S: spot purchase, T: tolling agreement
        
    # generator data (use to subset to PJM plants
    generators = generators[["Plant Id", "Plant Name", "NERC Region"]]

    # collapse duplicate generator rows
    generators = generators.drop_duplicates()
    
    # merge generator and plant data
    fuels = pd.merge(fuel, generators, how = 'outer', on = ['Plant Id', 'Plant Name'])
    
    fuels = fuels[fuels['NERC Region'] == 'RFC']   
    
    # replace missing values with NAs
    fuels["FUEL_COST"].replace(".", scipy.NaN, inplace=True)
    fuels["FUEL_COST"] = pd.to_numeric(fuels["FUEL_COST"])
    
    # convert to $ per mmbtu
    fuels["FUEL_COST"] = fuels["FUEL_COST"]/100 
    
    return(fuels)
    
    
