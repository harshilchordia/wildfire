directory = "/Users/harshilchordia/Desktop/KCL_Research/all_data"


import datetime
import json
import os
import shutil
import frp_himawari
import read_s5p
import viirs
import digitizer
import overlapp

def pause():
    programPause = input("Press the <ENTER> key to continue...")

def convertDate(date_entry):
    day, month, year = map(int, date_entry.split('-'))
    date = datetime.date(year, month, day)
    return date

def fetch_VIIRS(date):
    current_directory = directory + "/viirs/raw_files"
    viirs_list = []
    day_number = date.strftime('%-j')

    for file in os.listdir(current_directory):
        filename_start = "NPP_VMAES_L1.A"+str(date.year)+str(day_number)
        if file.startswith(filename_start):
            t = file[22:26]
            time = datetime.datetime.strptime(t,'%H%M').time()
            viirs_list.append({'file':file, 'time':time})
   
    return viirs_list, current_directory

def fetch_S5P(date):
    current_directory = directory + "/s5p/raw_data"
    s5p_list = []

    for file in os.listdir(current_directory):
        filename_start = "S5P_OFFL_L2__CO_____"+str(date.year)+str(date.strftime('%m'))+str(date.strftime('%d'))
        if file.startswith(filename_start):
            t = file[29:33]
            time = datetime.datetime.strptime(t,'%H%M').time()
            s5p_list.append({'file':file, 'time':time})
    
    return s5p_list, current_directory


def find_latest_time(viirs_list, s5p_list):
    last_time = datetime.time(hour=00, minute=1)
    for i in viirs_list:
        if last_time<i['time']:
            last_time = i['time']

    for i in s5p_list:
        if last_time<i['time']:
            last_time = i['time']
    return last_time


def fetch_FRP(date, latest_time):
    current_directory = directory + "/Himawari-8/" + str(date.year) + "/" + str(date.strftime('%m')) + "/" + str(date.strftime('%d'))
    frp_list = []
    for file in os.listdir(current_directory):
        filename_start = "CAMS__HMWR_FRP-PIXEL-ListProduct_HMWR-FD_"+str(date.year)+str(date.strftime('%m'))+str(date.strftime('%d'))
        if file.startswith(filename_start):
            t = file[-7:-3]
            time = datetime.datetime.strptime(t,'%H%M').time()
            if time<=latest_time:
                frp_list.append({'file':file, 'time':time})
    
    return frp_list, current_directory
            
def run_loop_frp(frp_list,frp_path):
    firepixels = []
    for i in frp_list:
        himawari_data = frp_himawari.extract_data_h5(frp_path+"/"+i['file'])
        lon = himawari_data["LONGITUDE"]
        lat = himawari_data["LATITUDE"]

        for x,y in zip(lon.items(), lat.items()):
            lon_point=x[1]
            lat_point=y[1]
            firepixels.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [lon_point, lat_point] }})
    return firepixels

def save_frp(firepixels, date, latest_time):
    if not os.path.exists('all_data/Himawari-8/json_dumps'):
        os.makedirs('all_data/Himawari-8/json_dumps')

    naming_string = date.strftime("%Y_%m_%d")+'_till_'+ latest_time.strftime("%H%M")
    bboxfile = "all_data/Himawari-8/json_dumps/frp_" + naming_string + ".js"

    with open(bboxfile, 'w') as file:
        # file.write('{};'.format(json.dumps(firepixels)))
        json.dump(firepixels, file)


def read_frp(date):
    dir= 'all_data/Himawari-8/json_dumps'
    for file in os.listdir(dir):
        if file.startswith('frp_'+date.strftime("%Y_%m_%d")):
            with open(dir+"/"+file) as data_file:
                data = json.loads(data_file.read())
                return data


def read_s5p_coord(date):
    dir = 'all_data/s5p/cropped_mask_coord'
    s5p_coord_list = []
    for file in os.listdir(dir):
        if file.startswith('s5p_'+ date.strftime("%Y_%m_%d")):
           with open(dir+"/"+file) as data_file:
                data = json.loads(data_file.read())
                file = file[:-2]+'png'
                s5p_coord_list.append({'file':file, 'coord':data})
    return s5p_coord_list

def read_viirs_coord(date):
    dir = 'all_data/viirs/png_and_json/json'
    viirs_coord_list =[]
    for file in os.listdir(dir):
        if file.startswith('VIIRS_'+ date.strftime("%Y_%m_%d")):
            with open(dir+"/"+file) as data_file:
                data = json.loads(data_file.read())
                file = file[:-2]+'png'
                viirs_coord_list.append({'file':file, 'coord':data})
    return viirs_coord_list
              
def check_overlap_rectangles(rec1, rec2):
    # check if either rectangle is actually a line
        if (rec1['xmin'] == rec1['xmax'] or rec1['ymin'] == rec1['ymax'] or \
            rec2['xmin'] == rec2['xmax'] or rec2['ymin'] == rec2['ymax']):
            # the line cannot have positive overlap
            return False

        return not (rec1['xmax'] <= rec2['xmin'] or  # left
                    rec1['ymax'] <= rec2['ymin'] or  # bottom
                    rec1['xmin'] >= rec2['xmax'] or  # right
                    rec1['ymin'] >= rec2['ymax'])    # top

def run_digitizer(s5p_data, viirs_data, firepixels):
    viirs_png_path = 'all_data/viirs/png_and_json/png/'
    s5p_png_path = 'all_data/s5p/png/'
    full_path = '/Users/harshilchordia/Desktop/KCL_Research/'
    digitizer_img_folder = 'current_digitizer_folder/'
    Australia_Crop_coordinates = [[112.953,-43.67700000000001], [159.04500000000002,-9.177000000000007]]
    # Australia_Crop_coordinates = [[-73.0020000000000095, -85.1460000000000150], [287.0400000000000205,81.1440000000000055]]
    
    
    for s in s5p_data:
        shutil.copyfile(full_path+s5p_png_path+s['file'], full_path+digitizer_img_folder+s['file'])
        for v in viirs_data:
            if check_overlap_rectangles(s['coord'], v['coord']):
            # if (True):
                shutil.copyfile(full_path+viirs_png_path+v['file'], full_path+digitizer_img_folder+v['file'])
                digitizer.run_digitizer(firepixels, v['file'], s['file'], Australia_Crop_coordinates, v['coord'])
                pause()

   

        

def run_loop_for_day(viirs_list, viirs_path, s5p_list, s5p_path, frp_list, frp_path, date, latest_time):
    # firepixels = run_loop_frp(frp_list, frp_path)
    # save_frp(firepixels, date, latest_time)
    # viirs_coordinates = []
    # for i in viirs_list:
    #     file_path = viirs_path+"/"+i['file']
    #     naming_string = date.strftime("%Y_%m_%d") + "_T_"+i['time'].strftime("%H%M")
 
    #     temp = viirs.process_viirs(file_path, naming_string)
    #     temp = [[temp[0][1], temp[0][0]],[temp[1][1], temp[1][0]]]
    #     viirs_coordinates.append(temp)

    overlapp.merge_viirs_tiff(directory+'/viirs/tiffs', date)
    # s5p data processing
    for i in s5p_list:
        file_path = s5p_path+"/"+i['file']
        naming_string = date.strftime("%Y_%m_%d") + "_T_"+i['time'].strftime("%H%M")
        read_s5p.netcdf_to_png(file_path, naming_string)

    print('\n\n\n\n All conversion to png done :) \n\n\n\n\n')


if __name__ == '__main__':
    date = convertDate("01-12-2019") #DD-MM-YYYY
    viirs_list, viirs_path = fetch_VIIRS(date)
    s5p_list, s5p_path = fetch_S5P(date)
    latest_time = find_latest_time(viirs_list, s5p_list)
    frp_list, frp_path = fetch_FRP(date, latest_time)
    firepixels = run_loop_for_day(viirs_list, viirs_path, s5p_list, s5p_path, frp_list, frp_path, date, latest_time)
  
    #run digitizer after all processing
    s5_data = read_s5p_coord(date)
    viirs_data = read_viirs_coord(date)
    firepixels = read_frp(date)
    run_digitizer(s5_data, viirs_data, firepixels)
   


    
    

   
  
    
    
