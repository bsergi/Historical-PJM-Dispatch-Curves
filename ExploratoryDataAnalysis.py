# Exploratory data analysis
# Misc. code fragments for looking at the datasets
# Will need to have loaded key variables from __main__.py 
# Author: Brian Sergi
# Created: 7/10/2018

## Load data

import matplotlib.mlab as mlab
import matplotlib.pyplot as plt

year = 2016

# load eGrid data
eGrid = readEGridPlant(year)

# load CEMS data
# CEMS = readCEMS(year, eGrid)

# CEMS at unit level, eGrid capacity data (MW) at plant level
filenameCEMSfacility = "CEMS facility data " + str(year) + ".csv"    
filenameCEMSemissions = "CEMS emissions data " + str(year) + ".csv"  

# facility data
facility = readCEMSfacility(filenameCEMSfacility)
    
# emissions data
annualEmissions = readCEMSEmissions(filenameCEMSemissions)

# combine and merge with eGrid (only fossil)
fullCEMS = mergeFacilityEmissions(facility, annualEmissions)

## CEMS vs eGrid and data availability


superCEMS = pd.merge(CEMS, eGrid, how = 'outer', left_on = 'Facility ID (ORISPL)', right_on = 'ORIS')   
# for 2016, 1215 total facilities listed in CEMS and 1366 listed in eGrid



## Heat rates

# Note: for comparison, need to load CEMS data with eGridHR=False

# mmBTU = 1 million BTU (1 MMBtu/MWh = 1000 Btu/kWh)
CEMS.loc[:,['Heat rate (MMBtu/MWh)', 'Plant nominal heat rate (Btu/kWh)'] ]

# MFE

def calcMFE(col1, col2):
    diffs = col1 - col2
    diffs = diffs.abs()    
    sums = (col1 + col2) / 2   
    MFEs = diffs / sums
    return MFEs.sum() / MFEs.shape[0]
    

def calcMFB(col1, col2):
    diffs = col1 - col2
    sums = (col1 + col2) / 2   
    MFBs = diffs / sums
    return MFBs.sum() / MFBs.shape[0]
    
# boxplots

CEMS['Heat rate diff'] = CEMS['Heat rate (MMBtu/MWh)'] * 1000 - CEMS['Plant nominal heat rate (Btu/kWh)']
CEMS['Heat rate diff percent'] = (CEMS['Heat rate (MMBtu/MWh)'] * 1000 - CEMS['Plant nominal heat rate (Btu/kWh)'] ) / CEMS['Plant nominal heat rate (Btu/kWh)'] 

CEMS.boxplot(column='Heat rate diff', by='Fuel', 
             patch_artist=True)
plt.show()

# test = calcMFE(pd.Series([1,2]), pd.Series([0,3]))

MFE_HR = calcMFE(CEMS['Heat rate (MMBtu/MWh)'] * 1000, CEMS['Plant nominal heat rate (Btu/kWh)'])
MFB_HR = calcMFB(CEMS['Heat rate (MMBtu/MWh)'] * 1000, CEMS['Plant nominal heat rate (Btu/kWh)'])

# histogram

num_bins = 5
n, bins, patches = plt.hist(diffs, num_bins, facecolor='blue', alpha=0.5)
plt.show()

diffs.describe()
diffs.quantile(q=[0, 0.25, 0.5, 0.75, 1])
percents.quantile(q=[0, 0.25, 0.5, 0.75, 1])

sum(CEMS['Heat rate (MMBtu/MWh)'].isna())
sum(CEMS['Plant nominal heat rate (Btu/kWh)'].isna())

# extreme values 
CEMS.loc[CEMS['Heat rate diff'].abs() > 15000,['Plant nameplate capacity (MW)','Max Hourly HI Rate (MMBtu/hr)', 
                                            'Heat rate (MMBtu/MWh)', 'Plant nominal heat rate (Btu/kWh)']]
                                            
CEMS.loc[CEMS['Plant nominal heat rate (Btu/kWh)'] > 100000,:]   


# missing values (8 missing from eGrid calculated value)
CEMS['Plant nominal heat rate (Btu/kWh)'].isna().sum()
CEMS.loc[CEMS['Plant nominal heat rate (Btu/kWh)'].isna(), ['Facility Name', 'Fuel',
                                                            'Plant nominal heat rate (Btu/kWh)']]


CEMS.loc[CEMS['Heat rate (MMBtu/MWh)'].isna(),:]


                                
## Total gen. capacity
CEMS['Plant nameplate capacity (MW)'].sum()
# PJM total installed capacity of 182,410 MW January 2017
# http://www.pjm.com/-/media/committees-groups/committees/mc/20180322-state-of-market-report-review/20180322-2017-state-of-the-market-report-review.ashx

eGrid.groupby(['Fuel'])['Plant nameplate capacity (MW)'].sum()
CEMS.groupby(['Fuel'])['Plant nameplate capacity (MW)'].sum()
# aligns relatively well with table

# Large number of plants within PJM from eGrid that are not listed in CEMS
# possible reasons:
# non-fossil (i.e. non-emitting) plants
# CEMS only includes plants > 25
# plants may have closed between 2016 and 2017 



## Emissions rates


def scatterPlot(data, xVar, yVar, colVar, colors, saveName, xLims=None, yLims=None):
    
    # copy and drop missing values
    data = data.copy()
    data = data.dropna(subset = [xVar, yVar, colVar])
    
    if xFactor != None:
        data[xVar] = data[xVar] * xFactor
    
    plt.scatter(data[xVar], data[yVar], 
                            c=data[colVar].apply(lambda x: colors[x]), alpha=0.25)
    
    if xLims != None:
        plt.xlim(xmin=xLims[0],xmax=xLims[1])
    else:
        xLims = (data[xVar].min(), data[xVar].max())
        
    if yLims != None:
        plt.ylim(ymin=yLims[0],ymax=yLims[1])
    else:
        yLims = (data[yVar].min(), data[yVar].max())
        
    upper = max(xLims[1], yLims[1])
        
    plt.plot([0,upper], [0,upper], color="grey")
    # legend formatting
    legend_elements = []
    for item in colors:
        legend_elements.extend([Line2D([0], [0], 
                               marker='o', color='w', label=item,
                               markerfacecolor=colors[item], markersize=10)])
    
    plt.legend(handles=legend_elements, loc='upper left')
    
    plt.xlabel(xVar)
    plt.ylabel(yVar)
    plt.tight_layout()

    os.chdir(os.getcwd() + '/Analysis')
    plt.savefig(saveName + ".pdf")
    os.chdir('..') 
    plt.close()
    
    
fuelColors = {'COAL': 'brown', 'GAS':'orange',  'OIL': 'black', 'BIOMASS': '#00CD00', 'OTHF': 'purple'}
              
scatterPlot(data=CEMS, xVar='eGrid annual SO2 rate (ton/MWh)',
                       yVar='SO2 emissions rate (tons/MWh)', colVar='Fuel',
                       colors = fuelColors, saveName = 'Emissions scatterplot - SO2',
                       xLims = (0, 0.01), yLims = (0, 0.01))
                       
scatterPlot(data=CEMS, xVar='eGrid annual CO2 rate (ton/MWh)',
                       yVar='CO2 emissions rate (tons/MWh)', colVar='Fuel',
                       colors = fuelColors, saveName = 'Emissions scatterplot - CO2',
                       xLims = (0, 2.5), yLims = (0, 2.5))
                       
scatterPlot(data=CEMS, xVar='eGrid annual NOx rate (ton/MWh)',
                       yVar='NOx emissions rate (tons/MWh)', colVar='Fuel',
                       colors = fuelColors, saveName = 'Emissions scatterplot - NOx',
                       xLims = (0, 0.0035), yLims = (0, 0.0035))
                       
# two plants that are very large outliers
outliers = CEMS.loc[CEMS['eGrid annual SO2 rate (ton/MWh)'] > 0.02, :]


outliers[['State', 'Facility Name', 'Fuel', 'SO2 emissions rate (tons/MWh)', 'eGrid annual SO2 rate (ton/MWh)', 
                                            'CO2 emissions rate (tons/MWh)', 'eGrid annual CO2 rate (ton/MWh)', 
                                            'NOx emissions rate (tons/MWh)', 'eGrid annual NOx rate (ton/MWh)']]
                                            
# scatterplot (load below)
CEMS['eGrid heat rate (MMBtu/MWh)'] = CEMS['Plant nominal heat rate (Btu/kWh)'] / 1000

scatterPlot(data=CEMS, xVar='eGrid heat rate (MMBtu/MWh)',
                       yVar='Heat rate (MMBtu/MWh)', colVar='Fuel',
                       colors = fuelColors, saveName = 'Heat rate scatterplot')