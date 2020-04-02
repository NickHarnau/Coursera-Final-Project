import pandas as pd
from bs4 import BeautifulSoup
import requests
import numpy as np
from geopy.geocoders import Nominatim
import re


##
# PART 1 - Getting the data from Wikipedia with BS4
##

link = "https://de.wikipedia.org/wiki/Liste_der_Stadtteile_von_Darmstadt"

# get the html site of the Wikipedia page
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0"}
page = requests.get(link, headers=headers)
soup = BeautifulSoup(page.content, 'html.parser')
print(soup.prettify())

tables = soup.findChildren('table') # from the html site, we only need the data inside the table (select only data inside the "table" html tag)


Adresses = tables[0] # filter for the relevant table
rows = Adresses.find_all("tr")# in every html tag "tr" are all values of a row

""" the column order is : Number, Name, Areasize, inhabitats, inhabitants per area
for each relevant information create a list"""

Boroughs = []
Size_ha = []
Inhabitants = []
Inhabitants_per_ha = []
for row in rows:
    if len(row.find_all("td"))>0: # be sure to take row with values and not the "header row" (header row has no html tag "td")
        values = row.find_all("td")
        try:
            if int(values[0].text) < 550 and re.search("[0-9][0][0]", values[0].text) is None: # get only relevant boroughs 
                Boroughs.append(values[1].text)
                Size_ha.append(values[2].text)
                Inhabitants.append(values[3].text)
                Inhabitants_per_ha.append(values[4].text)
        except Exception:
            pass

# create a DF

df_Darmstadt_boroughs = pd.DataFrame({"Borough": Boroughs, "Size_Ha": Size_ha, "Inhabitants": Inhabitants, "Inhabitants_per_ha": Inhabitants_per_ha})

# get latitude and longitude for each borough and add to df
latitude = []
longitude = []
geolocator = Nominatim(user_agent="darmstadt_explorer", timeout=20)

for borough in df_Darmstadt_boroughs["Borough"]:
    address = '{},  Darmstadt'.format(borough)
    # get coordinates of Toronto
    location = geolocator.geocode(address)
    latitude.append(location.latitude)
    longitude.append(location.longitude)

df_Darmstadt_boroughs["latitude"]= latitude
df_Darmstadt_boroughs["longitude"]= longitude

#
# Part 2 - get nerby venues for each borough
#

# get neraby venues

CLIENT_ID = "1BGD4X1AQLSRCHH55KS1HTXN55EE2JD0MED41FABHHSH5ZF3"
CLIENT_SECRET = "ERSHWESPPOVFLM4MV2NDEWEFGOQ5RV303PADVLO4IQA4WRR1"
VERSION = "20180605"
food_category = "4d4b7105d754a06374d81259"
LIMIT = 1000 # have to set limit , becasue default it is 50
def getNearbyVenues(names, latitudes, longitudes, radius=500):
    venues_list = []
    for name, lat, lng in zip(names, latitudes, longitudes):
        print(name)

        # create the API request URL
        url = 'https://api.foursquare.com/v2/venues/explore?categoryId={}&client_id={}&client_secret={}&v={}&ll={},{}&radius={}&limit={}'.format(
            food_category,
            CLIENT_ID,
            CLIENT_SECRET,
            VERSION,
            lat,
            lng,
            radius,
            LIMIT)

        # make the GET request
        results = requests.get(url).json()["response"]['groups'][0]['items']

        # return only relevant information for each nearby venue
        venues_list.append([(
            name,
            lat,
            lng,
            v['venue']['name'],
            v['venue']['location']['lat'],
            v['venue']['location']['lng'],
            v['venue']['categories'][0]['name']) for v in results])

    nearby_venues = pd.DataFrame([item for venue_list in venues_list for item in venue_list])
    nearby_venues.columns = ['Borough',
                             'Borough Latitude',
                             'Borough Longitude',
                             'Venue',
                             'Venue Latitude',
                             'Venue Longitude',
                             'Venue Category']

    return (nearby_venues)

darmstadt_venues= getNearbyVenues(names=df_Darmstadt_boroughs['Borough'],
                                   latitudes=df_Darmstadt_boroughs['latitude'],
                                   longitudes=df_Darmstadt_boroughs['longitude'])



#
# Part 3 : count the total venues for each borough and count the different kinds for each borough
#

darmstadt_venues_grouped = darmstadt_venues.groupby(["Borough"])[["Venue"]].count().reset_index()
df_Darmstadt_merged = df_Darmstadt_boroughs.merge(darmstadt_venues_grouped, on="Borough", how="left")
# merge the two dfs
df_Darmstadt_merged.rename(columns={"Venue": "Total_Amount_Venues"}, inplace=True)


#
# First goal: get the neighborhood with lowest venue/restaurant rate per inhabitants
#


# cleaning data for further calculation
df_Darmstadt_merged.replace({',': '.'}, regex=True, inplace=True) # to replace , by . (30,0 -> 30.0 for further calculation)
df_Darmstadt_merged['Size_Ha'] = df_Darmstadt_merged['Size_Ha'].str.replace(r" ", "" ) # problem with a value ( 448, 5 -> 448,5)
# change type for further calculation
df_Darmstadt_merged= df_Darmstadt_merged.astype({'Size_Ha': 'float64', "Inhabitants": "float64", "Inhabitants_per_ha": "float64"})
# new column with Inhabitants per FoodPlace -> the higher the number the more people come on one FoodPlace
# e.g. Inhabitants per FoodPlace = 3000 -> 3000 inhabitants share one FoodPlace
df_Darmstadt_merged["Inhabitants per FoodPlace"] = df_Darmstadt_merged["Inhabitants"] / df_Darmstadt_merged["Total_Amount_Venues"]

# get the ID of min max and the names and number
most_venues_per_inhabitants= df_Darmstadt_merged["Inhabitants per FoodPlace"].idxmin()
name_most = df_Darmstadt_merged.loc[most_venues_per_inhabitants,"Borough"]
number_most = df_Darmstadt_merged.loc[most_venues_per_inhabitants,"Inhabitants per FoodPlace"]
least_venues_per_inhabitants = df_Darmstadt_merged["Inhabitants per FoodPlace"].idxmax()
name_least= df_Darmstadt_merged.loc[least_venues_per_inhabitants,"Borough"]
number_least = df_Darmstadt_merged.loc[least_venues_per_inhabitants,"Inhabitants per FoodPlace"]



print("The Borough with the most FoodPlaces is: {} where one FoodPlace comes on {} inhabitants". format(name_most, number_most))
print("We should open a restaurant in the Borough with least FoodPlaces per Inhabitants. "
      "This is {} where only one FoodPlace comes on {} inhabitants".format(name_least, number_least))

#
# Second Goal: for each Borough get the kind of FoodPlace, that is least represented there

darmstadt_dummies= pd.get_dummies(darmstadt_venues['Venue Category'])
darmstadt_dummies['Borough'] = darmstadt_venues['Borough']
darmstadt_dummies_grouped = darmstadt_dummies.groupby(["Borough"]).sum()

# print for each Borough, FoodPlaces, that do not exists.
kinds_FoodPlace = darmstadt_dummies.columns
for index, row in darmstadt_dummies.iterrows():
    print("\n\nIn the borough {} are no FoodPlaces of type:".format(row["Borough"]))
    for kind in kinds_FoodPlace:
        if row[kind]==0:
            print(kind)