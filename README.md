# Historical-PJM-Dispatch-Curves
Code for a simple model that attempts to recreate historical dispatch curves in PJM using data from EPA and PJM in order to estimate marginal emissions factors. 

Run model from the __main__.py script. User will be prompted to enter a start and end date, as well as start and ending hours; the model will build dispatch curves and calculate marginal generators for each hour in that range. The user will also be prompted to choose method for calculating natural gas prices. 

Currently the model only works for hours/dates in 2016 using natural gas method 3.

Generator dispatch curves for each hour are saved to "Output plots" (saving option controlled by 'savePlots' boolean). A dataframe of the marginal generator in each hour from the model run is saved to an excel file "Marginal generators" + runName (where runName is a string specified at the beginning on __main__.py) in "Output data". 

Additional analysis of the results is supported in Analyis.py. 

Further documentation of the model mechanics and methods forthcoming. 

