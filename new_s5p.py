from matplotlib import pyplot as plt
import numpy as np
from pyhdf.SD import SD, SDC
from skimage import exposure
from scipy.interpolate import interp1d
import scipy.misc
import pyresample as pr
import pyproj
import json
import h5py
import imageio
from PIL import Image
from matplotlib import cm

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
        print('read {}'.format(b))
        sds_obj = file.select(b)
        data = sds_obj.get()
        mask.append(data <= -999)
        print('{} error: {}'.format(b, np.sum(mask[i])))
        latlon.append(data)
    latitude, longitude = tuple(latlon)
    latlon_mask = np.any(mask, axis=0)
    rgb = []
    mask = []
    for i, b in enumerate([5, 4, 3]):
        band = 'Reflectance_M{}'.format(b)
        print('read {}'.format(band))
        sds_obj = file.select(band)
        data = sds_obj.get()
        mask.append(data >= 65527)
        data = (data - sds_obj.Offset) * sds_obj.Scale
        data = np.clip(data, 0., 0.6)
        data = exposure.equalize_adapthist(scale(data), clip_limit=0.05)
        print('data type after equalize: ', data.dtype)
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
    leaflet_latlon_bbox = [ [ _lat[0], _lon[0] ], [ _lat[1], _lon[1] ] ]
    print('leaflet latLngBounds: [[{}, {}], [{}, {}]]'.format(_lat[0], _lon[0], _lat[1], _lon[1]))
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
    print(area_def)
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
    return (img, crs, leaflet_latlon_bbox)

def save2png(pngfile, img):

    if img.ndim == 2:
        print(np.nanmax(img), np.nanmin(img), np.isnan(img).any())
    elif  img.ndim == 3:
        print(np.nanmax(img[:,:,:-1]), np.nanmin(img[:,:,:-1]), np.isnan(img[:,:,:-1]).any())
    # scipy.misc.imsave(pngfile, img)

    img = np.clip(img, 0, 0.1)
    # im = img.astype(np.uint8)
    # im = Image.fromarray(im)
    # # im = im.convert('L')
    # im.save(pngfile)

    img=np.nan_to_num(img, nan=0)
    # img[img==0]
    # img = img*10000
    # print(img)
    # plt.imshow(img)
    # plt.savefig(pngfile)
    plt.imsave(pngfile, img, cmap=cm.gray)
    # print(img.shape)
    # imageio.imwrite(pngfile, img)


def read_s5p_swath_for_tcco(f):
    file = h5py.File(f,'r')
    # lat lon
    latlon = []
    mask = []
    for i, b in enumerate(['latitude', 'longitude']):
        band = '/PRODUCT/' + b
        print('read {}'.format(band))
        dset = file[band]
        vmin = dset.attrs['valid_min'][0]
        vmax = dset.attrs['valid_max'][0]
        vfill = dset.attrs['_FillValue'][0]
        data = dset[:][0,:,:]
        m = (data < vmin) | (data > vmax) | (data == vfill)
        mask.append(m)
        latlon.append(data)
    latitude, longitude = tuple(latlon)
    latlon_mask = np.any(mask, axis=0)
    # TCCO
    tcco_name = 'PRODUCT/carbonmonoxide_total_column'
    dset = file[tcco_name]
    units = dset.attrs['units'].decode('UTF-8')
    vfill = dset.attrs['_FillValue'][0]
    print('read TCCO [{}]: {}'.format(units, tcco_name))
    tcco = dset[:][0,:,:]
    tcco_mask = (tcco >= vfill-0.01e36)
    file.close()
    #
    mask = np.any([latlon_mask, tcco_mask], axis=0)
    latitude = np.ma.masked_array(data=latitude, mask=mask, fill_value=np.nan)
    longitude = np.ma.masked_array(data=longitude, mask=mask, fill_value=np.nan)
    gray = np.ma.masked_array(data=tcco, mask=mask, fill_value=np.nan)
    return (longitude, latitude, gray)

def main(f_s5p=None, prj=None, res=300):
    lons, lats, tcco = read_s5p_swath_for_tcco(f_s5p)
    rgba, crs, leaflet_latlon_bbox = resample_swath_to_rgba(prj, lons, lats, tcco, res, method='bilinear')
    pngfile = "{0}.png".format(f_s5p)
    save2png(pngfile, rgba)
    bboxfile = "{0}.js".format(f_s5p)
    with open(bboxfile, 'w') as file:
        file.write('viirs_bbox = {};'.format(json.dumps(leaflet_latlon_bbox)))
    
    print(lons.shape)
    print(rgba.shape)


if __name__ == "__main__":
    f='NPP_VMAES_L1.A2018276.1230.001.2018276233743.hdf'
    f='/Users/harshilchordia/Desktop/KCL_Research/all_data/s5p/raw_data/S5P_OFFL_L2__CO_____20191220T025930_20191220T044100_11318_01_010302_20191221T164720.nc'

    prj = proj4param['merc']
    main(f_s5p=f, prj=prj, res=3000)