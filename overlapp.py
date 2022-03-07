
import os
from random import randint, random
import subprocess
from osgeo import gdal
import json



# gdal_translate  -a_nodata 255 -a_ullr 142.105 -30.22 176.29 -5.35

#     warped_tif = gdal.Warp('extrafiles/chanhged123.tiff', ds, geoloc=True, dstSRS="EPSG:4326", xRes=0.069, yRes=0.069, targetAlignedPixels=True, format='GTiff' )



def georeference_png(pngfile, coordinates, naming_string, viirs_directory):
    saving_string = viirs_directory+"/georeferenced_tiffs/VIIRS_"+naming_string+'.tiff'
    # print(coordinates)
    # for file in os.listdir(directory+'/png'):
    #     js_data = ""
    #     for json_file in os.listdir(directory):
    #         if file[:-4]==json_file[:-3]:
    #             jsonfile=open(directory+"/"+json_file)
    #             data=json.load(jsonfile)
    #             print(data)
                # with open(directory+"/"+json_file) as data_file:
                #     data = dataFile.read()
                #     json_out = data[data.find('{'): data.rfind('}')+1]
                #     json_decode = demjson.decode(json_out)

                # print(json_decode)

                    # print(data_file)
                #     js_data = json.load(json_file)
                # print(js_data)

        # if file.startswith(filename_start):
        #     print(file[:-4])
    x1 = coordinates[0][1]
    y1 = coordinates[0][0]
    x2 = coordinates[1][1]
    y2 = coordinates[1][0]
    geo_tiff = gdal.Translate(saving_string, pngfile, format='GTiff', noData="255",outputSRS="EPSG:4326", outputBounds=[x1,y1,x2,y2])

# georeference_png()
def merge_viirs_tiff(current_directory, date):
    shape_file = 'new_aus_shape.shp'
    date_format = str(date.year)+'_'+str(date.strftime('%m'))+'_'+str(date.strftime('%d'))
    tiff_list = []
    for file in os.listdir(current_directory):
        filename_start = "VIIRS_"+ date_format
        if file.startswith(filename_start) and file.endswith('.tiff'):
            tiff_list.append(current_directory+"/"+file)


    merged_save_dir = current_directory+"/Merged_VIIRS_"+date_format+'.tiff'
    cropped_save_dir = current_directory+"/cropped_VIIRS_"+date_format+'.tiff'

    print(merged_save_dir)

    cmd = "gdal_merge.py -ot Float32 -o "+merged_save_dir+" -n 0.0 -a_nodata 255.0 -of GTiff"
    subprocess.call(cmd.split()+tiff_list)
    crop_shape = gdal.Warp(cropped_save_dir, merged_save_dir, cutlineDSName=shape_file, cropToCutline=True)
    pngimage = gdal.Translate('all_data/viirs/final_png/VIIRS_png_'+date_format+'.png', crop_shape, format='PNG', scaleParams=[[]])



    # vrt = gdal.BuildVRT("extrafiles/merged.vrt", tiff_list)
    # gdal.Translate('merged_t.tiff', vrt, format='GTiff')
    # vrt = None