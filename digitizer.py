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

def run_digitizer(firepixels, rgb_image_path, s5p_emission_path, s5p_aus_crop_coord, rgb_coord):

    i = 0
    firepixels_geojson = {
        "type": "FeatureCollection",
        "features": firepixels
    }
    layers = {
        'htmlroot': all_dir['digitise_img'],
        'output': s5p_emission_path[:-3]+'.geojson',
        'baselayers': OrderedDict({
            "RGB {0}".format(i): {
                'filename': rgb_image_path,
                'bbox_lonlat':  [   [rgb_coord['xmin'], rgb_coord['ymin']]  ,   [rgb_coord['xmax'],rgb_coord['ymax']]   ]
            }
        }),
        'overlayers': OrderedDict({
            'emission': {
                'filename': s5p_emission_path,
                'bbox_lonlat': s5p_aus_crop_coord
            },
            'firepixels': firepixels_geojson
        }),
    }

    dgt = Digitizer(layers)
    dgt.open(html_file='digitizeIt.html')