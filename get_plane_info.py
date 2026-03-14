from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from opensky_api import OpenSkyApi

# searches nearby area to find nearby planes
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

import pandas as pd

class Plane:

    icao_df = pd.read_csv(("../data/aircraft-database-complete-2025-08.csv"))

    def __init__ (self, plane):
        # from opensky.api object
        self.icao = plane.icao24
        self.flight_num = plane.callsign
        self.longitude = plane.longitude
        self.latitude = plane.latitude
        self.altitude = plane.geo_altitude

        # take series from dataframe
        plane_row = Plane.icao_df[Plane.icao_df["'icao24'"] == self.icao]
        if plane_row.ndim == 2:
            plane_row = plane_row.iloc[0]

        # from database
        self.manufacturer = plane_row["'manufacturerName'"]
        self.model = plane_row["'model'"].replace("'", "")
        self.owner = plane_row["'owner'"]

    def __str__(self):
        return f"{self.flight_num}\n{self.manufacturer} {self.model}\n{self.owner}\n({self.longitude}, {self.latitude})\n{self.altitude} km\n"


# takes in an opensky_api state and uses geopy's geodesic module to determine if the
# plane is less than five miles from "home"
def is_within_radius(plane):
    distance = geodesic((HOME_LAT, HOME_LONG), (plane.latitude, plane.longitude)).mi
    return distance <= RADIUS

def main():
    plane_list = []

    # bbox = (min latitude, max latitude, min longitude, max longitude)
    states = api.get_states(bbox=(HOME_LAT - RADIUS, HOME_LAT + RADIUS, HOME_LONG - RADIUS, HOME_LONG + RADIUS))
    for plane in states.states:
        if is_within_radius(plane):
            plane_obj = Plane(plane)
            plane_list.append(plane_obj)

            print(plane_obj)

main()