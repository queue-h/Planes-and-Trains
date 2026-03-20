import re
import requests
from geopy import distance
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from opensky_api import OpenSkyApi
import pandas as pd
from selenium import webdriver
from selenium.webdriver import chrome
from bs4 import BeautifulSoup


# searches nearby area to find planes within radius
# gets flight info from adsb.lol

# ICAO aircraft designators provided by opensky
# https://opensky-network.org/datasets/#metadata/
# last downloaded 03/11/2026

api = OpenSkyApi()

geolocator = Nominatim(user_agent="Planes+Trains")
ADDRESS = "1415 Duckens St Odenton, MD"
LOCATION = geolocator.geocode(ADDRESS)
HOME_LAT, HOME_LONG = LOCATION.latitude, LOCATION.longitude
RADIUS = 10 ## mi

class Plane:

    icao_df = pd.read_csv(("../data/aircraft-database-complete-2025-08.csv"))

    def __init__ (self, plane):
        # from opensky.api object
        self.icao = plane.icao24
        self.flight_num = plane.callsign.strip()  # flight number and callsign seem to be interchangeable
        self.longitude = plane.longitude
        self.latitude = plane.latitude

        # altitudes are often empty, handle
        if plane.geo_altitude is not None:
            self.altitude = plane.geo_altitude
        else:
            self.altitude = "[Altitude]"
        self.is_empty = False

        # get values from html (adsb.lol)
        aircraft_info = self.get_aircraft()
        self.year, self.company, self.model = aircraft_info["type_tuple"]
        self.owner = aircraft_info["owner"]
        self.registration = aircraft_info["registration"]

        # get values from api (adsbdb.com)
        self.origin, self.destination = self.get_flight()

    def __str__(self):
        return (f"{self.year} {self.company} {self.model}\n"
                f"{self.owner}\n"
                f"({self.longitude}, {self.latitude})\n"
                f"{self.altitude} km\n"
                f"{self.origin["iata"]}-{self.destination["iata"]}\n")

    # scrape data from https://adsb.lol/
    # only provides aircraft info
    # returns dict {type_tuple, owner, registration}
    def get_aircraft(self):
        url = "https://adsb.lol/" + "?icao=" + self.icao

        chrome_options = chrome.options.Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")

        # create driver and get page
        driver = webdriver.Chrome(options=chrome_options)

        # get and parse html
        driver.get(url)
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        # get info from website
        type_tuple = self.get_type(soup)
        owner = self.get_owner(soup)
        registration = self.get_registration(soup)

        driver.quit()
        return {"type_tuple": type_tuple, "owner": owner, "registration": registration}

    # given a beautiful soup object, returns a tuple in the form of (year, make, model)
    def get_type(self, soup):
        # find type
        type_str = soup.find(id="selected_typelong").text

        # check for year
        year_pattern = re.compile(r"^\d{4}")
        if year_pattern.search(type_str) is not None:
            year = year_pattern.search(type_str).group()
        else:
            year = "[Year]"

        # get make
        make_pattern = re.compile(r"[A-Z]{2,} ")
        if make_pattern.search(type_str) is not None:
            make = make_pattern.search(type_str).group().strip()
        else:
            make = "[Company]"

        # get model
        if make_pattern.search(type_str) is not None:
            model_index = make_pattern.search(type_str).end()
            model = type_str[model_index:]
        else:
            model = "[Model]"

        # return type
        return (year, make, model)

    # find owner from adsb.lol
    def get_owner(self, soup):
        owner = soup.find(id="selected_ownop").text
        if owner is None:
            owner = "[Owner]"
        return owner

    # find registration num from adsb.lol
    def get_registration(self, soup):
        registration = soup.find(id="selected_registration").text
        if registration is None:
            registration = "[Registration]"
        return registration

    # get flight information from https://adsbdb.com api
    # returns tuple (origin, destination)
    def get_flight(self):
        url = "https://api.adsbdb.com/v0/callsign/" + self.flight_num

        response = requests.get(url)
        if response.status_code == 200:
            flight = response.json()["response"]["flightroute"]

            # find origin
            origin = self.get_airport_info(flight["origin"])
            destination = self.get_airport_info(flight["destination"])

        else:
            return f"{response.status_code}: {response.text}"

        return origin, destination

    # parse airport information from adsbdb.com json
    # returns dict {iata, name, country, municipality}
    def get_airport_info(self, airport_info):
        iata = airport_info["iata_code"]
        country = airport_info["country_name"]
        municipality = airport_info["municipality"]
        name = airport_info["name"]
        return {"iata": iata, "name": name, "country": country, "municipality": municipality}

# takes in an opensky_api state and uses geopy's geodesic module to determine if the
# plane is less than five miles from "home"
def is_within_radius(plane):
    distance = geodesic((HOME_LAT, HOME_LONG), (plane.latitude, plane.longitude)).mi
    return distance <= RADIUS

# determines bbox parameters
# returns dict {min latitude, max latitude, min longitude, max longitude}
def get_bbox_params():

    # get values
    east = distance.distance(miles=RADIUS).destination((HOME_LAT, HOME_LONG), bearing=90).latitude # 90 for east (lat)
    west = distance.distance(miles=RADIUS).destination((HOME_LAT, HOME_LONG), bearing=270).latitude # 270 for west (lat)
    south = distance.distance(miles=RADIUS).destination((HOME_LAT, HOME_LONG), bearing=180).longitude # 180 for south (lon)
    north = distance.distance(miles=RADIUS).destination((HOME_LAT, HOME_LONG), bearing=0).longitude # 0 for north (lon)

    # determines relative values
    min_lat = min(east, west)
    max_lat = max(east, west)
    min_lon = min(north, south)
    max_lon = max(north, south)

    return {"min_lat": min_lat, "min_lon": min_lon, "max_lat": max_lat, "max_lon": max_lon}

def main():
    plane_list = []

    # bbox = (min latitude, max latitude, min longitude, max longitude)
    bbox = get_bbox_params()
    states = api.get_states(bbox=(bbox["min_lat"], bbox["max_lat"], bbox["min_lon"], bbox["max_lon"]))
    for plane in states.states:
        if is_within_radius(plane):
            plane_obj = Plane(plane)
            plane_list.append(plane_obj)

            print(plane_obj)

main()