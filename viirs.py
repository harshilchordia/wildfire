import numpy as np
from pyhdf.SD import SD, SDC
from skimage import exposure
from scipy.interpolate import interp1d
import pyresample as pr
import pyproj
import json
import imageio

from dir_config import all_dir


lin = np.array([0, 30, 60, 120, 190, 255]) / 255.0
nonlin = np.array([0, 110, 160, 210, 240, 255]) / 255.0
scale = interp1d(lin, nonlin, kind='quadratic')
proj4param = {
    'merc' : {'proj': 'merc',
              'a': '6378137',
              'b': '6378137',
              'lat_ts': '0.0',
              'lon_0':'0.0',
              'x_0': '0.0',
              'y_0': '0.0',
              'k':'1.0',
              'units': 'm',
              'nadgrids': '@null'}
}

def read_viirs_swath_for_rgba(f):
    file = SD(f, SDC.READ)
    latlon = []
    mask = []
    for i, b in enumerate(['Latitude', 'Longitude']):
        sds_obj = file.select(b)
        data = sds_obj.get()
        mask.append(data <= -999)
        latlon.append(data)
    latitude, longitude = tuple(latlon)
    latlon_mask = np.any(mask, axis=0)
    rgb = []
    mask = []
    for i, b in enumerate([5, 4, 3]):
        band = 'Reflectance_M{}'.format(b)
        sds_obj = file.select(band)
        data = sds_obj.get()
        mask.append(data >= 65527)
        data = (data - sds_obj.Offset) * sds_obj.Scale
        data = np.clip(data, 0., 0.6)
        data = exposure.equalize_adapthist(scale(data), clip_limit=0.05)
        rgb.append(data)
    file.end()
    rgb = np.stack(rgb, axis=2)
    rgb_mask = np.any(mask, axis=0)
    mask = np.any([latlon_mask, rgb_mask], axis=0)
    latitude = np.ma.masked_array(data=latitude, mask=mask, fill_value=np.nan)
    longitude = np.ma.masked_array(data=longitude, mask=mask, fill_value=np.nan)
    rgb = np.ma.masked_array(data=rgb, mask=np.dstack([mask, mask, mask]), fill_value=np.nan)
    return (longitude, latitude, rgb)

def resample_swath_to_rgba(proj4, lons, lats, data, res, method='nearest'):
    lat_m = np.nanmean(lats)
    lon_m = np.nanmean(lons)
    swath_def = pr.geometry.SwathDefinition(lons=lons, lats=lats)
    prj = pyproj.Proj(**proj4)
    x, y = prj(lons, lats)
    x_ll, y_ll, x_ur, y_ur = (np.nanmin(x), np.nanmin(y), np.nanmax(x), np.nanmax(y))
    extent_proj = [x_ll, y_ll, x_ur, y_ur]
    _lon, _lat = prj([x_ll, x_ur], [y_ll, y_ur], inverse=True)
    leaflet_lonlat_bbox = [ [ _lon[0], _lat[0] ], [ _lon[1], _lat[1] ] ]
    ratio = (extent_proj[2]-extent_proj[0])/(extent_proj[3]-extent_proj[1])
    res = 3000
    if ratio > 1:
      ratio = 1./ratio
      x_size = res
      y_size = int(x_size*ratio)
    else:
      y_size = res
      x_size = int(y_size*ratio)
    area_def = pr.geometry.AreaDefinition(proj4['proj'], proj4['proj'], proj4['proj'],
                                          proj4, x_size, y_size, extent_proj )
    result = pr.kd_tree.resample_nearest(swath_def, data, area_def,
                                            radius_of_influence=20000,
                                            fill_value=None)
    prj_data = np.copy(result.data)
    if data.ndim == 2:
        prj_data[result.mask] = np.nan
        img = prj_data
    else:
        prj_data[result.mask] = 0.
        img = np.dstack([prj_data, 1.-np.any(result.mask, axis=2).astype(float)])
    crs = area_def.to_cartopy_crs()
    return (img, crs, leaflet_lonlat_bbox)


def save2png(pngfile, img):
    if img.ndim == 2:
        pass
    elif  img.ndim == 3:
        pass
    imageio.imwrite(pngfile, img)

def main(naming_string, f_viirs=None, prj=None, res=300):
    lons, lats, data = read_viirs_swath_for_rgba(f_viirs)
    rgba, crs, leaflet_lonlat_bbox = resample_swath_to_rgba(prj, lons, lats, data, res, method='bilinear')
    pngfile = all_dir['viirs_png']+"/VIIRS_" + naming_string + ".png"
    save2png(pngfile, rgba)
    bboxfile = all_dir['viirs_json']+"/VIIRS_" + naming_string + ".js"

    with open(bboxfile, 'w') as file:
        xmin = leaflet_lonlat_bbox[0][0]
        ymin = leaflet_lonlat_bbox[0][1]
        xmax = leaflet_lonlat_bbox[1][0]
        ymax = leaflet_lonlat_bbox[1][1]
        json.dump({'xmin':xmin,'ymin':ymin,'xmax':xmax, 'ymax':ymax}, file)
        
    return leaflet_lonlat_bbox


def process_viirs(file, naming_string):
    prj = proj4param['merc']
    coordinates_lonlat = main(naming_string, f_viirs=file, prj=prj, res=3000)
    return coordinates_lonlat
    
