import re
import csv
import urllib.request, urllib.parse, urllib.error
from bs4 import BeautifulSoup

def win_safe_name(cityname):
    """Edit the string so that it can be used as a valid file name in
    Windows
    """
    cityname = cityname.strip()
    if cityname.endswith("."):
        cityname = cityname[:-1] + "_"
    for chr in cityname:
        if chr in ("<", ">", ":", "/", "\\", "|", "?", "*", "\""):
            cityname = cityname.replace(chr, "_")
    return cityname

city = input("Enter the city name: ")
city = win_safe_name(city)
logfile = city + "_log.txt"
base_url = input("Link to the climate monitor: ")
if not base_url.startswith("http://www.pogodaiklimat.ru/monitor"):
    print("Wrong URL format")
    quit()
base_url = base_url + "&"

# Average temperature by year, including monthly averages.  Yearly
# average is calculated, others are obtained.
temp_by_years = [[
    "year", "jan", "feb", "mar",
    "apr", "may", "jun", "jul",
    "aug", "sep", "oct", "nov",
    "dec", "avg"
    ]]

# "Hot / warm" stats (the amount of days in a given year that fit
# certain criteria):
# low - daily minimum doesn't fall below 20;
# avg - daily average doesn't fall below 20;
# high_30 - daily maximum hits or exceeds 30;
# high_32 - daily max hits or exceeds 32.
temp_high_values = [[
    "year", "low", "avg",
    "high_30", "high_32"
    ]]

# "Cold" stats (amount of days in a given year per criteria):
# avg - daily average hits of falls below 0
# low_0 - daily low hits or falls below 0
# low_10 - daily low at or below -10
# low_20 - daily low at or below -20
# low_30 - daily low at or below -30    
temp_low_values = [[
    "year", "avg", "low_0",
    "low_10", "low_20", "low_30"
    ]]

for year in range(2001, 2019):
    print("Processing year:", year)
    daily_low = 0
    daily_avg = 0
    daily_max_30 = 0
    daily_max_32 = 0
    daily_avg_0 = 0
    daily_low_0 = 0
    daily_low_10 = 0
    daily_low_20 = 0
    daily_low_30 = 0
    yearly_avg = 0.0
    temp_curr_year = [year]
    for month in range(1, 13):
        # Iterate through all pages for years 2001-2018, all months
        dest_url = (base_url
                    + urllib.parse.urlencode({"month": month, "year": year}))
        try:
            uh = urllib.request.urlopen(dest_url)
        except:
            print("Could not open", dest_url)
            print("Exiting")
            with open(logfile, "a+") as f:
                f.write(F"Could not open {dest_url}\n")
            quit()
        soup = BeautifulSoup(uh, "html.parser")
        
        # Get monthly average temperature direcrly from the page
        try:
            monthly_avg = re.findall("наблюдений: (\S+)°", soup.get_text())[0]
        except:
            # If there is no data, default to 0.0 and mark the error
            monthly_avg = 0.0
            print("Incorrect data for:", year, month)
            with open(logfile, "a+") as f:
                f.write(F"Incorrect monthly average for: {year} {month}\n")
        monthly_avg = float(monthly_avg)
        temp_curr_year.append(monthly_avg)
        # Sum up monthly averages, division is in the outer loop
        yearly_avg = yearly_avg + monthly_avg
        
        missing_data = 0
        # There is an extra table, and the one we need is nested within
        # another table
        table = soup.find_all("table")[2]
        # The first two rows contain column descriptions
        table_rows = table.find_all("tr")[2:]
        # tr for "table row" and td for "table data"
        for tr in table_rows:
            td = tr.find_all("td")
            # Get text values from "td" tags
            row = [item.text for item in td]
            # Sanity check, need to deal with missing data
            if len(row) == 5 and row[0] and row[1] and row[2]:
                # Checking daily mins
                if float(row[0]) >= 20.0:
                    daily_low += 1
                elif float(row[0]) <= -30.0:
                    daily_low_0 += 1
                    daily_low_10 += 1
                    daily_low_20 += 1
                    daily_low_30 += 1
                elif float(row[0]) <= -20.0:
                    daily_low_0 += 1
                    daily_low_10 += 1
                    daily_low_20 += 1
                elif float(row[0]) <= -10.0:
                    daily_low_0 += 1
                    daily_low_10 += 1
                elif float(row[0]) <= 0.0:
                    daily_low_0 += 1
                # Checking daily averages
                if float(row[1]) >= 20.0:
                    daily_avg += 1
                elif float(row[1]) <= 0.0:
                    daily_avg_0 += 1
                # Checking daily max temperatures
                if float(row[2]) >= 32.0:
                    daily_max_30 += 1
                    daily_max_32 += 1
                elif float(row[2]) >= 30.0:
                    daily_max_30 += 1
            else:
                missing_data += 1
        # Account for leap days (the table has 29 rows for February)
        if month == 2 and year%4 != 0:
            missing_data -= 1
        
        if missing_data > 0:
            print("Missing data for", missing_data, "days in:", year, month)
            with open(logfile, "a+") as f:
                f.write(F"Missing data for {missing_data} days in: "
                        F"{year} {month}\n")

    yearly_avg = yearly_avg / 12
    temp_curr_year.append(round(yearly_avg, 2))
    temp_by_years.append(temp_curr_year)
    
    temp_highs = [year, daily_low, daily_avg, daily_max_30, daily_max_32]
    temp_high_values.append(temp_highs)
    
    temp_lows = [
        year, daily_avg_0, daily_low_0,
        daily_low_10, daily_low_20, daily_low_30
        ]
    temp_low_values.append(temp_lows)

# All data collected and calculated, print the results into csv files

file_avg = city + "_avg.csv"
with open(file_avg, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(temp_by_years)
    
file_highs = city + "_highs.csv"
with open(file_highs, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(temp_high_values)
    
file_lows = city + "_lows.csv"
with open(file_lows, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(temp_low_values)

print("Done")
