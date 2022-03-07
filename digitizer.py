#------------------------------------------------------------------------------------------------
# digitized tool created by Jiangping He
#
# All coods in [lon, lat] format
# firepixel points in geojson format, geopandas (https://geopandas.org) can manipulate it.
# image path relative to path `layers['htmlroot']`, bbox should be rectangle shape in lon,lat
# only valid at the folder with same level of this file
#------------------------------------------------------------------------------------------------
from libs.ui import Digitizer
# Australia_Crop_coordinates = [[112.9225824584963220,-43.7372956269755235], [159.0987229003908965,-9.1473609336361505]]
# x = [[-49.207832336425774, 119.56679534912111], [-23.75498199462891, 160.94941711425778]]
# Australia_Crop_coordinates = [[x[0][1],x[0][0]],[x[1][1],x[1][0]]]

def run_digitizer(firepixels, rgb_image_path,rgb_coord, s5p_emission_path,s5p_aus_crop_coord):
    firepixels_geojson = {
        "type": "FeatureCollection",
        "features": firepixels
    }
    print(s5p_emission_path)

    layers = {
        'htmlroot': 'current_digitizer_folder',
        'rgb': {
            'filename': rgb_image_path,
            'bbox_lonlat':  [   [rgb_coord['xmin'], rgb_coord['ymin']]  ,   [rgb_coord['xmax'],rgb_coord['ymax']]   ]
        },
        'emission': {
            'filename': s5p_emission_path,
            # 'bbox_lonlat': [   [s5p_coord['xmin'], s5p_coord['ymin']]  ,   [s5p_coord['xmax'],s5p_coord['ymax']]   ]
            'bbox_lonlat': s5p_aus_crop_coord

        },
        'firepixels': firepixels_geojson
    }

    dgt = Digitizer(layers)
    dgt.open(html_file='digitizeIt.html')