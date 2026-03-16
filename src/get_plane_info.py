from enum import Enum
from geopy import distance
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from opensky_api import OpenSkyApi
import pandas as pd

# searches nearby area to find planes within radius
# only has information about the physical plane, not the flight route

# ICAO aircraft designators provided by opensky
# https://opensky-network.org/datasets/#metadata/
# last downloaded 03/11/2026

api = OpenSkyApi()

geolocator = Nominatim(user_agent="Planes+Trains")
ADDRESS = "1415 Duckens St Odenton, MD"
LOCATION = geolocator.geocode(ADDRESS)
HOME_LAT, HOME_LONG = LOCATION.latitude, LOCATION.longitude
RADIUS = 15 ## mi

class Categories(Enum):
    NO_INFO = 0
    NO_ADS_B_INFO = 1
    LIGHT = 2
    SMALL = 3
    LARGE = 4
    HIGH_VORTEX_LARGE = 5
    HEAVY = 6
    HIGH_PERFORMANCE = 7
    ROTORCRAFT = 8
    GLIDER = 9
    LIGHTER_THAN_AIR = 10
    PARACHUTIST = 11
    ULTRALIGHT = 12
    RESERVED = 13
    UNMANNED = 14
    TRANS_ATOSPHERIC = 15
    SURFACE_VEHICLE_EMERGENCY = 16
    SURFACE_VEHICLE_SERVICE = 17
    POINT_OBSTACLE = 18
    CLUSTER_OBSTACLE = 19
    LINE_OBSTACLE = 20

class Plane:

    icao_df = pd.read_csv(("../data/aircraft-database-complete-2025-08.csv"))

    def __init__ (self, plane):
        # from opensky.api object
        self.icao = plane.icao24
        self.flight_num = plane.callsign
        self.longitude = plane.longitude
        self.latitude = plane.latitude
        self.category = Categories(plane.category)

        # altitudes are often empty, handle
        if plane.geo_altitude is not None:
            self.altitude = plane.geo_altitude
        else:
            self.altitude = "[Altitude]"
        self.is_empty = False

        # take series from dataframe
        plane_row = Plane.icao_df[Plane.icao_df["'icao24'"] == self.icao]

        if plane_row.empty:
            self.is_empty = True

        if plane_row.ndim == 2 and not self.is_empty:
            plane_row = plane_row.iloc[0]

        if not self.is_empty:
            # from database
            self.manufacturer = plane_row["'manufacturerName'"]
            self.model = plane_row["'model'"].replace("'", "")
            self.owner = plane_row["'owner'"]
        else:
            # fill empty values
            self.manufacturer = "[Manufacturer]"
            self.model = "[Model]"
            self.owner = "[Owner]"
        # handle null values --> model doesn't get turned to '' and I don't know why
        if not self.manufacturer or self.manufacturer == "''":
            self.manufacturer = "[Manufacturer]"
        if not self.model:
            self.model = "[Model]"
        if not self.owner or self.owner == "''":
            self.owner = "[Owner]"

        # handle category exceptions because there are a lot of really common plane types without categories
        if self.category == Categories.NO_INFO:
            if "737" in self.model and (self.manufacturer == "Boeing" or "Boeing" in self.model):
                self.category = Categories.LARGE

    def __str__(self):
        return (f"{self.flight_num}\n{self.manufacturer} {self.model}\n{self.owner}\n"
                f"({self.longitude}, {self.latitude})\n{self.altitude} km\n{self.category.name}\n")


# takes in an opensky_api state and uses geopy's geodesic module to determine if the
# plane is less than five miles from "home"
def is_within_radius(plane):
    distance = geodesic((HOME_LAT, HOME_LONG), (plane.latitude, plane.longitude)).mi
    return distance <= RADIUS

# determines bbox parameters
# returns tuple in format (min latitude, max latitude, min longitude, max longitude)
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

    return min_lat, min_lon, max_lat, max_lon

def main():
    plane_list = []

    # bbox = (min latitude, max latitude, min longitude, max longitude)
    min_lat, min_lon, max_lat, max_lon = get_bbox_params()
    states = api.get_states(bbox=(min_lat, max_lat, min_lon, max_lon))
    for plane in states.states:
        if is_within_radius(plane):
            plane_obj = Plane(plane)
            plane_list.append(plane_obj)

            print(plane_obj)

main()