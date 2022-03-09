import numpy as np
from pyhdf.SD import SD, SDC
from skimage import exposure
from scipy.interpolate import interp1d
import pyresample as pr
import pyproj
import json
import imageio
import overlapp
from osgeo import gdal
from osgeo import osr

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
        # print('read {}'.format(b))
        sds_obj = file.select(b)
        data = sds_obj.get()
        mask.append(data <= -999)
        # print('{} error: {}'.format(b, np.sum(mask[i])))
        latlon.append(data)
    latitude, longitude = tuple(latlon)
    latlon_mask = np.any(mask, axis=0)
    rgb = []
    mask = []
    for i, b in enumerate([5, 4, 3]):
        band = 'Reflectance_M{}'.format(b)
        # print('read {}'.format(band))
        sds_obj = file.select(band)
        data = sds_obj.get()
        mask.append(data >= 65527)
        data = (data - sds_obj.Offset) * sds_obj.Scale
        data = np.clip(data, 0., 0.6)
        data = exposure.equalize_adapthist(scale(data), clip_limit=0.05)
        # print('data type after equalize: ', data.dtype)
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
    # print('leaflet latLngBounds: [[{}, {}], [{}, {}]]'.format(_lat[0], _lon[0], _lat[1], _lon[1]))
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
    # print(area_def)
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

#TIFF CODE
def make_tiff(tiff_file_name, img, coordinates):
    xmin = coordinates[0][0]
    ymin = coordinates[0][1]
    xmax = coordinates[1][0]
    ymax = coordinates[1][1]
  
    nrows,ncols = np.shape(img[:,:,3]) 
    xres = (xmax-xmin)/float(ncols)
    yres = (ymax-ymin)/float(nrows)
    geotransform=(xmin,xres,0,ymax,0, -yres)

    output_raster = gdal.GetDriverByName('GTiff').Create(tiff_file_name,ncols, nrows, 3 ,gdal.GDT_Float32)  # Open the file
    output_raster.SetGeoTransform(geotransform)  # Specify its coordinates
    srs = osr.SpatialReference()                 # Establish its coordinate encoding
    srs.ImportFromEPSG(3857)                     # This one specifies WGS84 lat long.
                                                 # Anyone know how to specify the
                                                 # IAU2000:49900 Mars encoding?
    output_raster.SetProjection( srs.ExportToWkt() )   # Exports the coordinate system
                                                       # to the file
    # Writes my array to the raster
    output_raster.GetRasterBand(1).WriteArray(img[:,:,0])
    output_raster.GetRasterBand(2).WriteArray(img[:,:,1])
    output_raster.GetRasterBand(3).WriteArray(img[:,:,2])
    output_raster.GetRasterBand(1).SetNoDataValue(-9999)
    output_raster.FlushCache()


def save2png(pngfile, img, viirs_directory, naming_string, lonlat):

    if img.ndim == 2:
        pass
        # print(np.nanmax(img), np.nanmin(img), np.isnan(img).any())
    elif  img.ndim == 3:
        pass
        # print(np.nanmax(img[:,:,:-1]), np.nanmin(img[:,:,:-1]), np.isnan(img[:,:,:-1]).any())
    # scipy.misc.imsave(pngfile, img)
    # img = np.flip(img, 1)
    saving_string = viirs_directory+"/tiffs/full/VIIRS_"+naming_string+'.tiff'
    make_tiff(saving_string, img,lonlat)

 
    imageio.imwrite(pngfile, img)





def main(naming_string, f_viirs=None, prj=None, res=300):
    viirs_directory = 'all_data/viirs'
    lons, lats, data = read_viirs_swath_for_rgba(f_viirs)
    rgba, crs, leaflet_lonlat_bbox = resample_swath_to_rgba(prj, lons, lats, data, res, method='bilinear')
    pngfile = viirs_directory+"/png_and_json/png/VIIRS_" + naming_string + ".png"
    
    save2png(pngfile, rgba, viirs_directory, naming_string, leaflet_lonlat_bbox)
    bboxfile = viirs_directory+"/png_and_json/json/VIIRS_" + naming_string + ".js"

    # overlapp.georeference_png(pngfile, leaflet_lonlat_bbox, naming_string, viirs_directory)
    with open(bboxfile, 'w') as file:
        xmin = leaflet_lonlat_bbox[0][0]
        ymin = leaflet_lonlat_bbox[0][1]
        xmax = leaflet_lonlat_bbox[1][0]
        ymax = leaflet_lonlat_bbox[1][1]
        json.dump({'xmin':xmin,'ymin':ymin,'xmax':xmax, 'ymax':ymax}, file)
        
        # file.write('{viirs_bbox_lonlat = {};'.format(json.dumps(leaflet_lonlat_bbox)))

    return leaflet_lonlat_bbox



def process_viirs(file, naming_string):
    prj = proj4param['merc']
    coordinates_lonlat = main(naming_string, f_viirs=file, prj=prj, res=3000)
    return coordinates_lonlat
    


# if __name__ == " __main__":
# #     # file = '/Users/harshilchordia/Downloads/sentinel5p/VIIRS/NPP_VMAES_L1.A2019342.0224.001.2019342115422.hdf'
# #     file = '/Users/harshilchordia/Desktop/KCL Research/all_data/viirs/NPP_VMAES_L1.A2019335.0442.001.2019335104525.hdf'
    
# #     # file = '/Users/harshilchordia/Downloads/sentinel5p/VIIRS/test.netcdf'
# #     # file = '/Users/harshilchordia/Downloads/NP.hdf.dap'
# #     # f='NPP_VMAES_L1.A2018276.1230.001.2018276233743.hdf'
# #     f = '/Users/harshilchordia/Desktop/KCL Research/all_data/viirs/raw_files/NPP_VMAES_L1.A2019335.0442.001.2019335104525.hdf'

# # #     f = file 
# #     prj = proj4param['merc']
#     # main(f_viirs=f, prj=prj, res=3000)