#------------------------------------------------------------------------------------------------
# digitized tool created by Jiangping He
#
# All coods in [lon, lat] format
# firepixel points in geojson format, geopandas (https://geopandas.org) can manipulate it.
# image path relative to path `layers['htmlroot']`, bbox should be rectangle shape in lon,lat
# only valid at the folder with same level of this file
#------------------------------------------------------------------------------------------------
from libs.ui import Digitizer
from main import all_dir


def run_digitizer(firepixels, rgb_image_path, s5p_emission_path,s5p_aus_crop_coord, rgb_coord):
    print('\nS5P CO Product:')
    print(s5p_emission_path)
    print('\n')
    
    firepixels_geojson = {
        "type": "FeatureCollection",
        "features": firepixels
    }
    layers = {
        'htmlroot': all_dir['digitise_img'],
        'rgb': {
            'filename': rgb_image_path,
            'bbox_lonlat':  [   [rgb_coord['xmin'], rgb_coord['ymin']]  ,   [rgb_coord['xmax'],rgb_coord['ymax']]   ]
        },
        'emission': {
            'filename': s5p_emission_path,
            'bbox_lonlat': s5p_aus_crop_coord

        },
        'firepixels': firepixels_geojson
    }

    dgt = Digitizer(layers)
    dgt.open(html_file='digitizeIt.html')