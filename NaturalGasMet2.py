import pandas as pd
import os

################## GAS METHOD TWO #########################

# Note: confirm that these prices are in $ per MMBtu

## Load data (called by __main__)
def readHubGasPrices(year, CEMS):
    os.chdir(os.getcwd() + '/Input raw data')   
    Price=readhubprices('Natural_gas_hub_prices_' + str(year) + '.xlsx')
    mapping=readmapgashubs('State_Mapping_to_Gas_Hubs.xlsx')
    os.chdir('..') 
    
    mapping = mapping.loc[:, ['Plant state abbreviation', 'Gas_Hubs']]

    # merge CEMS data and hub identifier 
    CEMS = pd.merge(CEMS, mapping, on="Plant state abbreviation", how="left", sort=False)
                
    return CEMS, Price
    
def readhubprices(file):
    price=pd.ExcelFile(file)
    hubprices = price.parse('Daily Summary')
    return(hubprices)

def readmapgashubs(file):
    statemapping = pd.ExcelFile(file)
    statemappingtoplants = statemapping.parse('Sheet1')
    return(statemappingtoplants)
        
## Select date (called by MarginalCostFunction) 
def gasMethodTwo(date, hubPrices):
    
    # subset to hub prices on one day    
    hubSubset = hubPrices.loc[hubPrices['Date'] == date, :]
    hubSubset = pd.melt(hubSubset, id_vars="Date")
    hubSubset.rename(columns={'variable':'Gas_Hubs', 'value':'Gas price'}, inplace=True)
    hubSubset = hubSubset[['Gas_Hubs', 'Gas price']]

    return(hubSubset)