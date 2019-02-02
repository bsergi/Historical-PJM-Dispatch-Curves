# Script for analyzing results

# In this Analysis file:
# 1. Table of marginal fuels
# 2. Boxplots of marginal emissions factors
# 3. Monthly marginal emissions average line plot
# 4. Comparison to PJM LMP

## Notes

# to do: adjust LMP plot to plot multiple price results after updating methods 1 and 2

## Libraries / data loading

import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt
import os
import datetime as dt

os.chdir(os.getcwd() + '/Output data')   
resultsFile = "Marginal Generators All 2016.csv"
results = pd.read_csv(resultsFile, parse_dates=True, index_col=0)  
os.chdir('..') 


## 1. Table of fuels

# calculate count by fuel
# adjust group vars to slice by other values

def fuelShareTable(results, groupVars):
    fuels = results.groupby(groupVars)[['Fuel']].count() 
    fuels = fuels / results.shape[0]
    os.chdir(os.getcwd() + '/Output analysis')   
    fuels.to_csv("Share of fuel.csv")
    os.chdir('..') 
    return fuels
    
fuelShareHourly = fuelShareTable(results, groupVars=['Hour', 'Fuel'])
fuelShareAnnual = fuelShareTable(results, groupVars=['Fuel'])


## 2. Boxplots of marginal emissions factors

def readdata2(file):
    Sheet=pd.ExcelFile(file)
    Monthly_Data= Sheet.parse('2016_Method_Two_correctOil')
    #Monthly_Data = Data.set_index('Date')
    Monthly_Data['month']= Monthly_Data['Date'].map(lambda x:x.month)
    #dftemp = Monthly_Data[Monthly_Data['month'] == 2]
    #print dftemp
    return Monthly_Data


def plotboxplot(file):
    file.boxplot(column='CO2 emissions rate (tons/MWh)', by='month')
    plt.title("Boxplot of Emissions")
    plt.ylabel('tons/MWh', fontdict=None, labelpad=None)
    plt.legend(loc='upper right')
    plt.show()


Data=readdata2(r'C:\Users\joshg\Desktop\Research\2016_Method_Two_correctOil.xlsx')
boxplot_file=plotboxplot(Data)

def readdata2(file):
    Sheet=pd.ExcelFile(file)
    Monthly_Data= Sheet.parse('2016_Method_Two')
    #Monthly_Data = Data.set_index('Date')
    Monthly_Data['month']= Monthly_Data['Date'].map(lambda x:x.month)
    #dftemp = Monthly_Data[Monthly_Data['month'] == 2]
    #print dftemp
    return Monthly_Data

def readdata3(file):
    Sheet=pd.ExcelFile(file)
    Data= Sheet.parse('Season')
    return Data

def mergedatabase(file,file1):
    database=pd.merge(file,file1,on='month')
    #print database
    return database

def plotboxplot(file):

    file.boxplot(column='CO2 emissions rate (tons/MWh)', by='Season')
    #file.plot(kind='scatter',x='month', y='Emission Rate')
    #file.scatter('Season', 'Emission Rate ', alpha=0.5)
    plt.title("Boxplot of Emissions By Season")
    plt.ylabel('tons/MWh', fontdict=None, labelpad=None)
    plt.show()

def mergedatabase(file,file1):
    database=pd.merge(file,file1,on='month')
    #print database
    return database

Data=readdata2(r'C:\Users\joshg\Desktop\Research\Outputs.xlsx')
Seasons=readdata3(r'C:\Users\joshg\Desktop\Research\seasons.xlsx')
Plantseasonmapping=mergedatabase(Data,Seasons)
boxplot_file=plotboxplot(Plantseasonmapping)

## 3. Monthly marginal emissions average line plot

def readdata(file):
    Sheet=pd.ExcelFile(file)
    Data= Sheet.parse('2016_Method_Two_correctOil')
    Monthly_Data=Data.set_index('Date').groupby([pd.TimeGrouper(freq='M')])['CO2 emissions rate (tons/MWh)'].mean()
    #print Monthly_Data.head(12)
    return Monthly_Data

def readdata2(file):
    Sheet=pd.ExcelFile(file)
    Data= Sheet.parse('2016_Method_Two_correctOil')
    Monthly_Data = Data.set_index('Date')
    #DF = Data['CO2 emissions rate (tons/MWh)']
    return Monthly_Data

def plotlinegraph(file):
    file.plot(title='Hour 15 Average Marginal CO2 Emission in 2016 by Months',y='CO2 emissions rate (tons/MWh)')
    plt.ylabel('tons/MWh', fontdict=None, labelpad=None)
    plt.legend(loc='upper right')
    plt.show()

def plotlinegraph2(file):
    file.plot(title='Hour 15 Marginal CO2 Emission in 2016',y='CO2 emissions rate (tons/MWh)')
    plt.ylabel('tons/MWh', fontdict=None, labelpad=None)
    plt.legend(loc='upper right')
    #plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    plt.show()


Database=readdata(r'C:\Users\joshg\Desktop\Research\2016_Method_Two_correctOil.xlsx')
Data=readdata2(r'C:\Users\joshg\Desktop\Research\2016_Method_Two_correctOil.xlsx')
Plot_file2=plotlinegraph2(Data)
Plot_file=plotlinegraph(Database)

## 4. Comparison to PJM LMP

# subset to appropriate hours to match results
def readPJMLMPs(filename, subsetHours=None):
    
    hours = []
    for i in range(1, 25):
        hours.extend([i]) 
        
    # read in LMP data
    os.chdir(os.getcwd() + '/Input raw data')   
    LMPs = pd.read_excel(filename, sheet_name="Summary", skiprows=3)
    os.chdir('..') 

    LMPs.drop(['Unnamed: 0',  'Unnamed: 1'], axis=1, inplace=True) # drop two initial columns

    i, colDict = 0, dict()
    for col in LMPs.columns:
        if i == 0:
            colDict[col] = "Date"
        else:
            colDict[col] = hours[i-1]
        i += 1
        
    # rename all columns
    LMPs.rename(columns=colDict, inplace=True)

    if subsetHours == None:
        subsetHours = hours
        
    LMPsub = LMPs[["Date"] + subsetHours]
    
    # melt date frame
    LMPmelt = LMPsub.melt(id_vars=['Date'])
    
    # add additional fields
    LMPmelt['Day'] = LMPmelt.loc[:,'Date'].apply(lambda x: x.day)
    LMPmelt['Month'] = LMPmelt.loc[:,'Date'].apply(lambda x: x.month)
    LMPmelt['Year'] = LMPmelt.loc[:,'Date'].apply(lambda x: x.year)
    
    # rename columns and sort    
    LMPmelt.rename(columns={'variable':'Hour', 'value':'LMP'}, inplace=True)
    LMPmelt = LMPmelt[ ["Date", "Hour", "Day", "Month", "Year", "LMP"] ]
    return LMPmelt
    
def mergeLMPandResults(LMPs, results):
    merged = pd.merge(LMPs, results, how = 'outer', on = ['Hour', 'Day', 'Month', 'Year'])
    return merged


# Note: rows of LMP and marginal costs must match
# set up to plot results from several runs?
def plotLMPs(mergedData, filename=None):
    
    numX = mergedData.shape[0]
    xAxis = list(range(1,numX+1))
    
    series1 = mergedData['Marginal Cost ($/MWh)'].tolist()
    series2 = mergedData['LMP'].tolist()

    MGen = plt.figure(num=None)
    ax1 = MGen.add_subplot(111)
    ax1.plot(xAxis,series2, 'b-', label = "PJM LMPs")
    ax1.plot(xAxis,series1,'r-',label='Modeled',linewidth=2)
    
    #ax1.plot(xAxis,marginalCost_3,'b-', label='Method 3')

    ax1.set_xlim((1,numX))
    ax1.set_ylim((0,1.25*max(max(series1), max(series2))))
    ax1.set_xlabel('Numbered hour of the year')
    ax1.set_ylabel('Marginal Cost ($/MWh)')  
    
    # ax2 = ax1.twinx()
    # CO2emis = df['CO2 emissions rate (tons/MWh)']
    # ax2.plot(xAxis, CO2emis, 'b--',linewidth=.5)
    # ax2.set_ylabel('CO2 Emissions Rate by the Marginal Generator (tons/MWh)')
    
    #ax1.legend()
    plt.legend()
    plt.title(filename)
    
    if filename != None:
        os.chdir(os.getcwd() + '/Output analysis')
        plt.savefig(filename + ".png")
        os.chdir('..') 
        plt.close()
    else:
        plt.show()


# read PJM LMPs
LMPs = readPJMLMPs("Summary 2016 DA Price.xlsx")        # subsetHour should be list of strings e.g. ["Hour 1", "Hour 15"]

# merge reslts and PJM LMPs
mergedResults = mergeLMPandResults(LMPs, results)

plotLMPs(mergedResults, filename='Marginal Cost vs PJM LMP - All hours for Jan-Dec 2016')


