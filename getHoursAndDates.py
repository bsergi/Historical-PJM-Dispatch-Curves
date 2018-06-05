# This function will take a start date and an end date and then 
# return a list of the hourly dates in the format needed for the
# marginal cost function 
import dateutil.parser as parser
import datetime as dt
import calendar

def getStartDate():
    try:
        startDate = parser.parse(input("Start date: "))

    except:
        print("Your input has an incorrect date format. Please try month-date-year. \n")
        startDate = getStartDate()
    return(startDate)

def getEndDate(startDate):
    try:
        endDate = parser.parse(input("End date: "))
        if endDate < startDate:
            print("Please enter a date that is after the start date. \n")
            endDate = getEndDate(startDate)
    except:
        print("Your input has an incorrect date format. Please try month-date-year. \n")
        endDate = getEndDate(startDate)

    # The following if-statement will ask for the year and then overwrite both dates' year values if the inputs are not the same.    
    if endDate.year != startDate.year:
        inputYear = input("Your years do not match. What year are you looking for? Use the full 20XX notation.\n")
        startDate = dt.date(int(inputYear),startDate.month,startDate.day)
        endDate = dt.date(int(inputYear),endDate.month,endDate.day)

    return(startDate,endDate)

def grabMonths(start,end):
    if start.month == end.month and start.day == end.day:
        monthList = [[start.month, start.day]]
        return (monthList)
    monthDiff = end.month - start.month
    monthList = [0]*(monthDiff+1)
    for i in range(monthDiff + 1):
        monthList[i] = start.month + i
    return (monthList)

def grabDays(start,end,months):
    if start == end:
        return ([[[start.month,start.day]]])
    if len(months) == 1:
        monthDays = list(range(start.day,end.day+1))
        day_count = 0
        for day in monthDays:
            monthDays[day_count] = [months[0], day]
            day_count += 1
        months[0] = monthDays
        return (months)
    for val in months:
        if val != start.month and val != end.month:
            (discard, days) = calendar.monthrange(start.year,val) # Discard value is the weekday of the first day of the month
            monthDays = list(range(1,days+1))
            for day in range(len(monthDays)):
                monthDays[day] = [val, day+1]
            months[val-start.month] = monthDays
        if val == start.month:
            (discard, days) = calendar.monthrange(start.year,val) # Discard value is the weekday of the first day of the month
            monthDays = list(range(start.day,days+1))
            for day in range(len(monthDays)):
                monthDays[day] = [val, start.day+day]
            months[val - start.month] = monthDays
        if val == end.month:
            monthDays = list(range(end.day))
            for day in range(len(monthDays)):
                monthDays[day] = [val, day+1]
            months[val - start.month] = monthDays
    return(months)


# You can now input hour values that will return a 2D array of each day and the desired hours in each day.
# The startHour will become the first hour checked on the startDate. The endHour will become the
# last hour checked on the endDate. These are inclusive. The remainder of the days will run from
# 0 - 23 hours.
def grabHours(monthDayList,startDate,endDate):
    monthDayHourList = []
    
    hourNeeded = True
    
    while hourNeeded:
        print("Enter the first hour for the start date and the last hour on the end date (1-24).")
        startHour = int(input("First hour: "))
        endHour = int(input("Last hour: "))
        
        if startHour < 25 and startHour > 0 and endHour < 25 and endHour > 0:
            hourNeeded = False
        
    listLen = len(monthDayList)
    count = 0
    modMonthDayList = []
    for val in monthDayList: # val represents a list of a month's days, shorter if the first or last month in the desired range
        for subVal in val:
            if subVal == [startDate.month,startDate.day] and subVal == [endDate.month,endDate.day]:
                for i in range(startHour,endHour+1):
                    newVal = subVal + [i]
                    modMonthDayList.append(newVal)
            elif subVal == [startDate.month,startDate.day]:
                for i in range(startHour,25):
                    newVal = subVal + [i]
                    modMonthDayList.append(newVal)
            elif subVal == [endDate.month,endDate.day]:
                for i in range(1,endHour+1):
                    newVal = subVal + [i]
                    modMonthDayList.append(newVal)
            else:
                for i in range(1, 24):
                    newVal = subVal + [i]
                    modMonthDayList.append(newVal)
    return(modMonthDayList)

def runGetDates():
    print("Please enter start and end dates for the analysis (MM/DD/YY).")
    startDate = getStartDate()
    startDate,endDate = getEndDate(startDate)
    monthList = grabMonths(startDate,endDate)
    monthDayList = grabDays(startDate,endDate,monthList)
    monthDayHourList = grabHours(monthDayList,startDate,endDate)
    return(monthDayHourList)






