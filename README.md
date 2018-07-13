# Historical-PJM-Dispatch-Curves
Code for a simple model that attempts to recreate historical dispatch curves in PJM using data from EPA and PJM in order to estimate marginal emissions factors. Scripts are formatted to run with Python 3.6. 

Run the basic model using the runModel(runName, saveDates) function from the __main__.py script. User will be prompted to enter a start and end date, as well as start and ending hours; the model will build dispatch curves and calculate marginal generators for each hour in that range. The user will also be prompted to choose method for calculating natural gas prices. 

Generator dispatch curves for each hour are saved to "Output plots" (specify which dates should be saved in a list, saveDates). A dataframe of the marginal generator in each hour from the model run is saved to an excel file "Marginal generators" + runName in "Output data". 

Additional analysis and plotting of the results is supported in Analysis.py. 

Further documentation of the model mechanics and methods forthcoming. 

