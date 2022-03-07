#------------------------------------------------------------------------------------------------
# digitized tool created by Jiangping He
#
# All coods in [lon, lat] format
# firepixel points in geojson format, geopandas (https://geopandas.org) can manipulate it.
# image path relative to path `layers['htmlroot']`, bbox should be rectangle shape in lon,lat
# only valid at the folder with same level of this file
#------------------------------------------------------------------------------------------------
from libs.ui import Digitizer

firepixels_geojson = {
    "type": "FeatureCollection",
    "features": [
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [176.838, -12.404] }},
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [180, -21] }},
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [192.92, -25.150] }},
    ]
}
layers = {
    'htmlroot': 'demo',
    'rgb': {
        'filename': 'tonga_goes.png',
        'bbox_lonlat':  [[176.838, -12.404], [192.92, -25.150]]
    },
    'emission': {
        'filename': 'MODIS_AOD-fake.png',
        'bbox_lonlat': [[169.55, -7.93], [190.86, -33.93]]
    },
    'firepixels': firepixels_geojson
}

dgt = Digitizer(layers)
dgt.open(html_file='digitizeIt.html')