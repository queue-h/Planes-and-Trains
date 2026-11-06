// get root
let rootDiv = document.querySelector('#root');

// get the coordinates of an address
let address = "AMERICAN UNIVERSITY";
let radius = 10;

// get coordinates of an address
async function callGeoApi(address) {
    let user_agent = "Planes+Trains";

    // nominatim base url
    const url = new URL("https://nominatim.openstreetmap.org/search");
    url.searchParams.set("q", address);
    url.searchParams.set("format", "json");
    url.searchParams.set("limit", 1);

    let result = await fetch(url, {
        headers: {"User-Agent": user_agent}
    });
    return await result.json();
}

// returns [minLat, minLon, maxLat, maxLon]
function getBoundingBox(lat, lon) {
    const NORTH = 0;
    const EAST = 90;
    const SOUTH = 180;
    const WEST = 270;

    let latlng = {latitude: lat, longitude: lon};

    let north = geolib.computeDestinationPoint(latlng, radius * 1000, NORTH).latitude;
    let east = geolib.computeDestinationPoint(latlng, radius * 1000, EAST).longitude;
    let south = geolib.computeDestinationPoint(latlng, radius * 1000, SOUTH).latitude;
    let west = geolib.computeDestinationPoint(latlng, radius * 1000, WEST).longitude;

    // determine relative values
    let maxLon = Math.max(east, west);
    let minLon = Math.min(east, west);
    let maxLat = Math.max(north, south);
    let minLat = Math.min(north, south);

    return [minLat, minLon, maxLat, maxLon];
}

async function callOpenSky(address) {
    // get location
    let location = await callGeoApi(address);
    location = location[0]; // returns as an array

    let latitude = Number(location.lat);
    let longitude = Number(location.lon);
    let bbox = getBoundingBox(latitude, longitude);

    // set url with bbox params to filter results
    const url = new URL(`https://opensky-network.org/api/states/all?lamin=${bbox[0]}&lomin=${bbox[1]}&lamax=${bbox[2]}&lomax=${bbox[3]}`);

    let response = await fetch(url, {
        headers: {
            "Accept": "application/json",
            "Access-Control-Allow-Origin": "https://opensky-network.org"
        }
    });

    console.log(response);


}
callOpenSky(address);