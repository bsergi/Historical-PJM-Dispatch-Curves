import pandas as pd
import os

################## GAS METHOD TWO #########################


def readHubGasPrices(year, eGrid):
    os.chdir(os.getcwd() + '/Input raw data')   
    Price=readhubprices('Natural_gas_hub_prices_' + str(year) + '.xlsx')
    mapping=readmapgashubs('State_Mapping_to_Gas_Hubs.xlsx')
    os.chdir('..') 

    Planthubmapping=mergedatabase(eGrid,mapping)
    Planthubmappingtemp=mergedatabasewithyear(Price,Planthubmapping)
    return Planthubmappingtemp

# main call
def gasMethodTwo(date,eGrid, hubprices):
    #Plants=readegriddata(egrid)
    Plantprices=filterDate(getprice(Price,hubprices),date)
    # Plantprices.to_csv("Plantprices.csv")
    return(Plantprices)

'''
def readegriddata(egrid):
    Plantdatabase = egrid.parse('PLNT16')
    labels = ['Plant name', 'DOE/EIA ORIS plant or facility code',
              'Plant state abbreviation', 'Balancing Authority Code',
              'Plant primary fuel']
    Plantdatabasesub = Plantdatabase.loc[:, Plantdatabase.columns.intersection(labels)]
    dftemp=Plantdatabasesub[Plantdatabasesub['Plant primary fuel'] == 'NG']
    pjmplants=dftemp[dftemp['Balancing Authority Code'] == 'PJM']
    #print dftemp.head(5)
    return(pjmplants)
    
'''

def readhubprices(file):
    price=pd.ExcelFile(file)
    hubprices = price.parse('Daily Summary')
    #print hubprices.head(5)
    return(hubprices)

def readmapgashubs(file2):
    statemapping = pd.ExcelFile(file2)
    statemappingtoplants = statemapping.parse('Sheet1')
    #print statemappingtoplants
    return(statemappingtoplants)

def mergedatabase(file,file1):
    database=pd.merge(file,file1,on='Plant state abbreviation')
    #print database
    return(database)

def mergedatabasewithyear(file,file1):
    file['key'] = 1
    file1['key'] = 1
    modifieddatabase = pd.merge(file, file1, on='key')
    #del modifieddatabase['key']
    labels = ['Plant name', 'DOE/EIA ORIS plant or facility code',
              'Plant state abbreviation', 'Balancing Authority Code',
              'Plant primary fuel','Gas_Hubs','Date']
    modifieddatabasesub=modifieddatabase.loc[:, modifieddatabase.columns.intersection(labels)]
    dftemp = modifieddatabasesub[modifieddatabasesub['Plant primary fuel'] == 'NG']
    pjmplants = dftemp[dftemp['Balancing Authority Code'] == 'PJM']
    #print database
    return(pjmplants)

def getprice(file,file1):
    #gashubslabel=list(file.column)[1:]
    #print file1.columns
    #print file.columns
    #print file1.Gas_Hubs.unique()
    f2=file1#[file1.Gas_Hubs=='Lebanon'].copy()
    f2['Prices']=file.set_index('Date').lookup(f2.Date,f2.Gas_Hubs)
    #print f2.head(20)
    return(f2)

def filterDate(inputDF,date):
    gas_single_date = inputDF[inputDF['Date']==date]
    return(gas_single_date)



   