import json
from PIL import Image
from matplotlib import pyplot as plt
from osgeo import gdal
import os
import numpy as np
from skimage.morphology import convex_hull_image
import imageio

# file = "/Users/harshilchordia/Downloads/sentinel5p/S5P_OFFL_L2__CO_____20191220T025930_20191220T044100_11318_01_010302_20191221T164720.nc"
# # file = "/Users/harshilchordia/Desktop/KCL Research/all_data/s5p/S5P_OFFL_L2__CO_____20191201T021534_20191201T035703_11048_01_010302_20191207T014034.nc"
# coordinates = [111.739531274, -9.093294054, 159.612371748, -44.839754231] #cooridnates for australia
 #cooridantes for the data

crop_coordinates = [112.9530000000000030,-43.6770000000000067, 159.0450000000000159,-9.1770000000000067]

#cropped_s5p_CO_date-time.tiff

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
    if not os.path.exists('all_data/s5p/tiff'):
        os.makedirs('all_data/s5p/tiff')

    if not os.path.exists('all_data/s5p/tiff/full_tiff'):
        os.makedirs('all_data/s5p/tiff/full_tiff')

    if not os.path.exists('all_data/s5p/tiff/cropped_tiff'):
        os.makedirs('all_data/s5p/tiff/cropped_tiff')

    if not os.path.exists('all_data/s5p/png'):
        os.makedirs('all_data/s5p/png')

    if not os.path.exists('all_data/s5p/cropped_mask_coord'):
        os.makedirs('all_data/s5p/cropped_mask_coord')

    saving_tiff = 'all_data/s5p/tiff/'
    ds = gdal.Open(file)

    warped_tif = gdal.Warp(saving_tiff+'full_tiff/s5p_full_'+naming_string+'.tiff', ds, geoloc=True, dstSRS="EPSG:4326", xRes=0.069, yRes=0.069, targetAlignedPixels=True, format='GTiff', srcNodata=9.96921e+36, dstNodata=9.96921e+36)

    shape_file = 'new_aus_shape.shp'
    # adfasdf
    
    crop_shape = gdal.Warp(saving_tiff+'cropped_tiff/s5p_cropped_4326'+naming_string+'.tiff', warped_tif, cutlineDSName=shape_file, cropToCutline=True)
    # crop_shape = gdal.Translate(saving_tiff+'cropped_tiff/s5p_cropped_'+naming_string+'.tiff', warped_tif, projWinSRS="EPSG:4326",projWin=crop_coordinates)

    # crop_tif = gdal.Translate('extrafiles/croppjned.tiff', warped_tif,format='GTiff', projWin=crop_coordinates)

    changed_proj = gdal.Warp('all_data/s5p/png/s5p_3857'+naming_string+'.tiff', crop_shape, srcSRS='EPSG:4326', dstSRS='EPSG:3857', dstNodata=0)


    png_image_dir = 'all_data/s5p/png/s5p_'+naming_string+'.png'

   



    myarray = np.array(changed_proj.GetRasterBand(1).ReadAsArray())
    ndv = np.array(changed_proj.GetRasterBand(1).GetNoDataValue())
   

    myarray = (myarray * 255 / np.max(myarray)).astype('uint8')
    myarray[myarray==ndv] = 255


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
 

    # formatted[formatted==0.0] = 255

    # print(formatted)
    # img = Image.fromarray(formatted)

   


    # imageio.imwrite(png_image_dir, myarray)

    geoTransform = crop_shape.GetGeoTransform()
    minx = geoTransform[0]
    maxy = geoTransform[3]
    maxx = minx + geoTransform[1] * crop_shape.RasterXSize
    miny = maxy + geoTransform[5] * crop_shape.RasterYSize
    print ([minx, miny, maxx, maxy])


    # pngimage = gdal.Translate(png_image_dir, changed_proj, format='PNG')

    lons, lats = get_tif_lat_lons(changed_proj)
    find_bounds(img, lats, lons, naming_string)
    

    

    # img = image.fromarray(pngimage, 'RGB')
# img.save('my.png')
    # img.show()
    # print(get_tif_lat_lons(crop_shape))
    # return pngimage


# netcdf_to_png(file, coordinates)



def find_bounds(entire_image,lats, lons, naming_string):
    img = entire_image.convert('L') 

    np_img = np.array(img)
    np_img = ~np_img  # invert B&W
    np_img[np_img > 0] = 1

    # myarray = np.array(crop_shape.GetRasterBand(1).ReadAsArray())
    # print(np.shape(myarray))

    data = convex_hull_image(np_img, tolerance=1e-10) 


    lons_mask = np.ma.masked_where(data==False, lons)
    lats_mask = np.ma.masked_where(data==False, lats)

    xmin,ymin,xmax,ymax = [lons_mask.min(), lats_mask.min(), lons_mask.max(), lats_mask.max()]

    bboxfile = 'all_data/s5p/cropped_mask_coord/s5p_' + naming_string + ".js"

    with open(bboxfile, 'w') as file:
        json.dump({'xmin':xmin,'ymin':ymin,'xmax':xmax, 'ymax':ymax}, file)
        # file.write('s5p_bbox_lonlat = {};'.format(json.dumps(corners)))

    # print(lons_mask)

    # plt.imshow(lats)

    # plt.show()

    # plt.imshow(lats_mask)

    # plt.show()

  



   
# find_bounds()