#------------------------------------------------------------------------------------------------
# digitized tool created by Jiangping He
#
# All coods in [lon, lat] format
# firepixel points in geojson format, geopandas (https://geopandas.org) can manipulate it.
# image path relative to path `layers['htmlroot']`, bbox should be rectangle shape in lon,lat
# only access the folder at the same level of this file
#------------------------------------------------------------------------------------------------
from libs.ui import Digitizer
from collections import OrderedDict
from dir_config import all_dir

def run_digitizer(firepixels, rgb_image_path, s5p_emission_path,s5p_aus_crop_coord, rgb_coord):


    firepixels_geojson = {
        "type": "FeatureCollection",
        "features": firepixels
    }
    layers = {
        'htmlroot': 'demo',
        'output': 'MODIS_AOD-fake.plume.geojson',
        'baselayers': OrderedDict({
            'rgb': {
                'filename': 'tonga_goes.png',
                'bbox_lonlat':  [[176.838, -12.404], [192.92, -25.150]]
            }
        }),
        'overlayers': OrderedDict({
            'emission': {
                'filename': 'MODIS_AOD-fake.png',
                'bbox_lonlat': [[169.55, -7.93], [190.86, -33.93]]
            },
            'firepixels': firepixels_geojson
        }),
    }

    dgt = Digitizer(layers)
    dgt.open(html_file='digitizeIt.html')