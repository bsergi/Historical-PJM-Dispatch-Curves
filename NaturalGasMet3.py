import pandas as pd
import os

################## GAS METHOD THREE #########################

## Load data

# note: edit function to be more responsive to year input
def readhenryhuprices(file):
    os.chdir(os.getcwd() + '/Input raw data')   
    price=pd.ExcelFile(file)
    henryhub = price.parse('Prices')
    os.chdir('..') 
    YearPrice=henryhub[henryhub['Date']<'1-1-2017']
    return(YearPrice)
    
## Select price for given date
def gasMethodThree(date, eGrid, henryHubPrices):
    # move this to initial data loading to spead up
    # Price=readhenryhuprices(r'Henry Hub Daily Prices 1998-2018.xls')
    
    Plants=returnGasPlants('NA', eGrid)
    #PlantPrices=filterDate(mergeprice(Plants,henryHubPrices),date)
    
    # find gas price for given date
    price = filterDate(henryHubPrices, date)
    
    return(price["Prices"].item())

# returns natural gas plants in PJM
def returnGasPlants(file, eGrid):
    gas=eGrid[eGrid['Plant primary fuel'] == 'NG']
    return(gas)

# selects price based on date
def filterDate(inputDF,date):
    gas_single_date = inputDF[inputDF['Date']==date]
    return(gas_single_date)

# function returns a date-price entry for each plant
def mergeprice(file, file1):
    file, file1 = file.copy(), file1.copy()
    file['key'] = 1
    file1['key'] = 1
    finalprices=pd.merge(file,file1,on='key')
    del finalprices['key']
    return(finalprices)







'''
OLD CODE

def readegriddata(file):
    EGRID_Data=pd.ExcelFile(file)
    Plantdatabase = EGRID_Data.parse('PLNT16')
    labels = ['Plant name', 'DOE/EIA ORIS plant or facility code',
              'Plant state abbreviation', 'Balancing Authority Code',
              'Plant primary fuel']
    Plantdatabasesub = Plantdatabase.loc[:, Plantdatabase.columns.intersection(labels)]
    dftemp=Plantdatabasesub[Plantdatabasesub['Plant primary fuel'] == 'NG']
    pjmplants=dftemp[dftemp['Balancing Authority Code'] == 'PJM']

    return(pjmplants)

def readhenryhubprices(file):

    price=pd.ExcelFile(file)
    henryhub = price.parse('Prices')
    YearPrice=henryhub[henryhub['Date']<'1-1-2017']
    return(YearPrice)


def mergeprice(file,file1):
    file['key']=1
    file1['key'] =1
    finalprices=pd.merge(file,file1,on='key')
    del finalprices['key']
    return(finalprices)

def filterDate(inputDF,date):
    gas_single_date = inputDF[inputDF['Date']==date]
    return(gas_single_date)

def gasMethodThree(date):

    Price=readhenryhubprices(r'Henry Hub Daily Prices 1998-2018.xls')
    Plants=readegriddata(r'egrid2016_data.xlsx')
    PlantPrices=filterDate(mergeprice(Plants,Price),date)
    return(PlantPrices)

'''



