import urllib.request, urllib.parse, urllib.error
import re
import csv
from bs4 import BeautifulSoup

def win_safe_name(cityname) :
    """Edit the string so that it can be used as
    a file name in Windows"""
    ReservedChars = frozenset(["<", ">", ":", "/", "\\", "|", "?", "*", "\""])
    cityname = cityname.strip()
    for chr in cityname :
        if chr in ReservedChars :
            cityname = cityname.replace(chr, "_")
    return cityname

city = input("Enter the city name: ")
city = win_safe_name(city)
logfile = city + "_log.txt"
base_url = input("Link to the climate monitor: ")
if base_url.startswith("http://www.pogodaiklimat.ru/monitor") is False:
    print("Wrong URL format")
    quit()
base_url = base_url + "&"

temp_by_years = [[
    "year", "jan", "feb", "mar",
    "apr", "may", "jun", "jul",
    "aug", "sep", "oct", "nov",
    "dec", "avg"
    ]]
    
temp_high_values = [[
    "year", "low", "avg",
    "high_30", "high_32"
    ]]
    
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
        #print("Processing:", year, month)
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
        
        try:
            monthly_avg = re.findall("наблюдений: (\S+)°", soup.get_text())[0]
        except:
            monthly_avg = 0.0
            print("Incorrect data for:", year, month)
            with open(logfile, "a+") as f:
                f.write(F"Incorrect monthly average for: {year} {month}\n")
        monthly_avg = float(monthly_avg)
        temp_curr_year.append(monthly_avg)
        yearly_avg = yearly_avg + monthly_avg
        
        missing_data = 0        
        table = soup.find_all("table")[2]
        table_rows = table.find_all("tr")[2:]
        for tr in table_rows:
            td = tr.find_all("td")
            row = [i.text for i in td]
            if len(row) == 5 and row[0] and row[1] and row[2]:
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
                if float(row[1]) >= 20.0:
                    daily_avg += 1
                elif float(row[1]) <= 0.0:
                    daily_avg_0 += 1
                if float(row[2]) >= 32.0:
                    daily_max_30 += 1
                    daily_max_32 += 1
                elif float(row[2]) >= 30.0:
                    daily_max_30 += 1
            else:
                missing_data += 1
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