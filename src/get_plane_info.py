import requests
from geopy import distance
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from opensky_api import OpenSkyApi
import pandas as pd

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
            self.altitude = "[ALTITUDE]"

        # set up class values to be handled in call api
        self.type = "[TYPE]"
        self.owner = "[OWNER]"
        self.registration = "[REGISTRATION]"
        self.origin = "[ORIGIN]"
        self.destination = "[DESTINATION]"
        self.empty = False
        self.error = "[NO ERROR]"

        # set values from adsbdb.com
        self.call_api()

    def __str__(self):
        str = (f"{self.type}\n"
                f"{self.owner}\n"
                f"({self.longitude}, {self.latitude})\n"
                f"{self.altitude} km\n")
        if not self.empty:
            str += f"{self.origin["iata"]}-{self.destination["iata"]}\n"
        else:
            str += f"{self.error}\n"
        return str

    def call_api(self):
        url = f"https://api.adsbdb.com/v0/aircraft/{self.icao}?callsign={self.flight_num}"
        response = requests.get(url)

        if response.status_code == 200:
            aircraft_info = response.json()["response"]["aircraft"]
            self.type = aircraft_info["manufacturer"] + " " + aircraft_info["type"]
            self.owner = aircraft_info["registered_owner"]
            self.registration = aircraft_info["registration"]

            flight_info = response.json()["response"]["flightroute"]
            self.origin = self.get_airport_info(flight_info["origin"])
            self.destination = self.get_airport_info(flight_info["destination"])
        else:
            self.empty = True
            self.error = "ERROR: " + str.upper(response.text[13:-2])

    # parse airport information from adsbdb.com json
    # returns dict {iata, name, country, municipality}
    def get_airport_info(self, airport_info):
        iata = airport_info["iata_code"]
        country = airport_info["country_name"]
        municipality = airport_info["municipality"]
        name = airport_info["name"]
        return {"iata": iata, "name": name, "country": country, "municipality": municipality}

# takes in an opensky_api state and uses geopy's geodesic module to determine if the
# plane is less than RADIUS miles from "home"
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