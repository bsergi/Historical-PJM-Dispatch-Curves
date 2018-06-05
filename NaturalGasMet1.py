import pandas as pd

################## EIA AVERAGE FUEL COSTS #########################

def interpolateFuelPrices(plants):
    # find average by fuel group (gas or coal), purchase type (contract or spot), 
    # state, and month (1-12)
    summary1 = plants.groupby(['MONTH', 'Plant State', 'FUEL_GROUP', 'Purchase Type'])['FUEL_COST'].mean().reset_index()
    summary2 = plants.groupby(['MONTH', 'FUEL_GROUP', 'Purchase Type'])['FUEL_COST'].mean().reset_index()
    summary3 = plants.groupby(['MONTH', 'FUEL_GROUP'])['FUEL_COST'].mean().reset_index()
    
    summary1.rename(columns={'FUEL_COST':'FUEL_COST_V1'}, inplace=True)
    summary2.rename(columns={'FUEL_COST':'FUEL_COST_V2'}, inplace=True)
    summary3.rename(columns={'FUEL_COST':'FUEL_COST_V3'}, inplace=True)
    
    # merge price summaries as new column
    plants = pd.merge(plants, summary1, how = 'outer', on = ['MONTH', 'Plant State', 'FUEL_GROUP', 'Purchase Type'])
    plants = pd.merge(plants, summary2, how = 'outer', on = ['MONTH', 'FUEL_GROUP', 'Purchase Type'])
    plants = pd.merge(plants, summary3, how = 'outer', on = ['MONTH', 'FUEL_GROUP'])
    
    # iterate through rows
    for id in range(0,plants.shape[0]):
        i, missing = 1, pd.isnull(plants.iloc[id, plants.columns.get_loc("FUEL_COST")])
        
        # if missing, iterate through other columns
        while missing and i < 4: 
            
            newCost = plants.iloc[id, plants.columns.get_loc("FUEL_COST_V" + str(i))]
            plants.iloc[id, plants.columns.get_loc("FUEL_COST")] = newCost
        
            # check if still missing data
            if not pd.isnull(plants.iloc[id, plants.columns.get_loc("FUEL_COST")]):
                missing = False
            i += 1

    sortVars = ['Plant Id', 'MONTH']
    
    # take plant average
    # note: this obscures some variability in fuel at the unit level
    plantSummary = plants.groupby(['MONTH', 'Plant State', 'Plant Id'])['FUEL_COST'].mean().reset_index()

    return plantSummary.sort_values(by=sortVars).reset_index(drop=True)
    

def plotFuelPrice(plants, filename):
    
    # copy and reset index
    plants = plants.copy()
    plants = plants.reset_index(drop=True)  
    
    # dataframe without major outlier
    plants2 = plants.copy()
    plants2 = plants2.loc[plants2['FUEL_COST'] < plants2['FUEL_COST'].max()]  
    #plants2 = plants2.loc[plants2['FUEL_COST'] < 20]  

    # convert to wide format for plot (1 column per plant)
    plants = plants.pivot_table(values="FUEL_COST", index=['FUEL_GROUP', 'MONTH'], columns='Plant Name').reset_index()
    plants2 = plants2.pivot_table(values="FUEL_COST", index=['FUEL_GROUP', 'MONTH'], columns='Plant Name').reset_index()
    
    # seaborn style for plotting
    # plt.style.use('seaborn-darkgrid')
    # create a color palette (can be used to give lines different colors)
    # palette = plt.get_cmap('Set1')

    # subset to only gas plants
    gasPlants = plants[plants["FUEL_GROUP"] == "Natural Gas"]
    gasPlants2 = plants2[plants2["FUEL_GROUP"] == "Natural Gas"]
    
    return gasPlants
    
