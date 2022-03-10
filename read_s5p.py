import json
from PIL import Image
from matplotlib import pyplot as plt
from osgeo import gdal
import os
import numpy as np
from skimage.morphology import convex_hull_image

from dir_config import all_dir, shape_file



def get_tif_lat_lons(ds):
    width = ds.RasterXSize
    height = ds.RasterYSize
    gt = ds.GetGeoTransform()
    top_left_lat = gt[3] + ((gt[5])/2)
    top_left_lon = gt[0] + ((gt[1])/2)
    lats = np.arange(0, height,1)
    lats = np.multiply(lats,(gt[5]))
    lats = np.add(lats, top_left_lat )
    lons = np.arange(0, width, 1)
    lons = np.multiply(lons,(gt[1]))
    lons = np.add(lons,top_left_lon)
    lons, lats = np.meshgrid(lons, lats)

    return lons, lats


def netcdf_to_png(file, naming_string):
    file = 'NETCDF:"'+ file + '":/PRODUCT/carbonmonoxide_total_column'
    png_image_dir = all_dir['s5p_png']+'/s5p_'+naming_string+'.png'

    ds = gdal.Open(file)
    warped_tif = gdal.Warp(all_dir['s5p_full_tif'] + '/s5p_full_'+naming_string+'.tiff', ds, geoloc=True, dstSRS="EPSG:4326", xRes=0.069, yRes=0.069, targetAlignedPixels=True, format='GTiff', srcNodata=9.96921e+36, dstNodata=9.96921e+36)
    crop_shape = gdal.Warp(all_dir['s5p_crop_tif']+ '/s5p_cropped_4326_'+naming_string+'.tiff', warped_tif, cutlineDSName=shape_file, cropToCutline=True)
    changed_proj = gdal.Warp(all_dir['s5p_crop_tif']+'/s5p_3857'+naming_string+'.tiff', crop_shape, srcSRS='EPSG:4326', dstSRS='EPSG:3857', dstNodata=0)

    myarray = np.array(changed_proj.GetRasterBand(1).ReadAsArray())
    ndv = np.array(changed_proj.GetRasterBand(1).GetNoDataValue())
    myarray = (myarray * 255 / np.max(myarray)).astype('uint8')
    myarray[myarray==ndv] = 255

    #make no data transparent
    img = Image.fromarray(myarray)
    img = img.convert("RGBA")
    datas = img.getdata()
    newData = []
    for item in datas:
        if item[0] == 255 and item[1] == 255 and item[2] == 255:
            newData.append((255, 255, 255, 0))
        else:
            newData.append(item)

    img.putdata(newData)
    img.save(png_image_dir, "PNG")

    #Find and save s5p data extent
    lons, lats = get_tif_lat_lons(crop_shape)
    array_4326 = np.array(crop_shape.GetRasterBand(1).ReadAsArray())
    img_4326 = Image.fromarray(array_4326)
    find_bounds(img_4326, lats, lons, naming_string)



def find_bounds(entire_image,lats, lons, naming_string):
    img = entire_image.convert('L') 
    np_img = np.array(img)
    np_img = ~np_img  # invert B&W
    np_img[np_img > 0] = 1

    data = convex_hull_image(np_img, tolerance=1e-10) 

    lons_mask = np.ma.masked_where(data==False, lons)
    lats_mask = np.ma.masked_where(data==False, lats)

    xmin,ymin,xmax,ymax = [lons_mask.min(), lats_mask.min(), lons_mask.max(), lats_mask.max()]

    bboxfile = all_dir['s5p_coord']+'/s5p_' + naming_string + ".js"
    print(bboxfile)

    with open(bboxfile, 'w') as file:
        json.dump({'xmin':xmin,'ymin':ymin,'xmax':xmax, 'ymax':ymax}, file)
