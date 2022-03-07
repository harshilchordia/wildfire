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

def rgb_to_tiff(data, lon, lat):
    red = data[:,:,0]
    green = data[:,:,1]
    blue = data[:,:,2]

# Hannah code for converting to tiff
def make_tiff(tiff_file_name, img, coordinates, lat, lon):
    print('lat')
    print(lat.shape)
    print('lon')
    print(lon.shape)
    print('image')
    print(img.shape)

    # img = np.array(img)
    # img.resize((3232,3200,4))
    # print('resized image')
    # print(img[1250][200])

    xmin = coordinates[0][1]
    ymin = coordinates[0][0]
    xmax = coordinates[1][1]
    ymax = coordinates[1][0]
    print("\n \n \n ")
    print(img[:,:,0].shape)
    print("\n \n \n ")

    print(np.shape(img))
  
    nrows,ncols = np.shape(img[:,:,3])
    # ncols,nrows = row_column_tuple

    xres = (xmax-xmin)/float(3000)
    yres = (ymax-ymin)/float(2313)

    
    geotransform=(xmin,xres,0,ymax,0, -yres)

 
    output_raster = gdal.GetDriverByName('GTiff').Create(tiff_file_name,ncols, nrows, 4 ,gdal.GDT_Float32)  # Open the file
    output_raster.SetGeoTransform(geotransform)  
    srs = osr.SpatialReference()                 
    srs.ImportFromEPSG(4326)                     
                                            
    output_raster.SetProjection( srs.ExportToWkt() )   

    # Writes my array to the raster
    output_raster.GetRasterBand(1).WriteArray(img[:,:,0])
    output_raster.GetRasterBand(2).WriteArray(img[:,:,1])
    output_raster.GetRasterBand(3).WriteArray(img[:,:,2])
    output_raster.GetRasterBand(4).WriteArray(img[:,:,3])

    output_raster.GetRasterBand(1).SetNoDataValue(0)
    output_raster.GetRasterBand(2).SetNoDataValue(0)
    output_raster.GetRasterBand(3).SetNoDataValue(0)
    output_raster.GetRasterBand(4).SetNoDataValue(0)
    

    output_raster.FlushCache()

def make_tiff(tiff_file_name, img, coordinates):
    xmin = coordinates[1][1]
    ymin = coordinates[1][0]
    xmax = coordinates[0][1]
    ymax = coordinates[0][0]
  
    nrows,ncols = np.shape(img[0,:,:]) 
    xres = (xmax-xmin)/float(ncols)
    yres = (ymax-ymin)/float(nrows)
    geotransform=(xmin,xres,0,ymax,0, -yres)

    output_raster = gdal.GetDriverByName('GTiff').Create(tiff_file_name,ncols, nrows, 3 ,gdal.GDT_Float32)  # Open the file
    output_raster.SetGeoTransform(geotransform)  # Specify its coordinates
    srs = osr.SpatialReference()                 # Establish its coordinate encoding
    srs.ImportFromEPSG(4326)                     # This one specifies WGS84 lat long.
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


if __name__ == "__main__":
    f_viirs = '/Users/harshilchordia/Desktop/KCL Research/all_data/viirs/raw_files/NPP_VMAES_L1.A2019335.0442.001.2019335104525.hdf'
    lons, lats, data = read_viirs_swath_for_rgba(f_viirs)
    print(lons.shape)
    print(lats.shape)
    print(data[:,:,0].shape)
    rgb_to_tiff(data, lons, lats)




