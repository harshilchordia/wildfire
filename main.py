import datetime
import json
import os
import shutil

#Project files
import frp_himawari
import read_s5p
import viirs
import digitizer
from dir_config import full_path, all_dir, Australia_Shape_Coord



def createdirs():
    
    for dir in all_dir.values():
        print(dir)
        if not os.path.exists(dir):
            os.makedirs(dir)


def pause():
    programPause = input('Press the <ENTER> key to continue...')

def convertDate(date_entry):
    day, month, year = map(int, date_entry.split('-'))
    date = datetime.date(year, month, day)
    return date

def fetch_VIIRS(date):
    viirs_list = []
    day_number = date.strftime('%-j')
    for file in os.listdir(all_dir['viirs_raw']):
        filename_start = 'NPP_VMAES_L1.A'+str(date.year)+str(day_number)
        if file.startswith(filename_start):
            t = file[22:26]
            time = datetime.datetime.strptime(t,'%H%M').time()
            viirs_list.append({'file':file, 'time':time})
   
    return viirs_list

def fetch_S5P(date):
    s5p_list = []
    for file in os.listdir(all_dir['s5p_raw']):
        filename_start = 'S5P_OFFL_L2__CO_____'+str(date.year)+str(date.strftime('%m'))+str(date.strftime('%d'))
        if file.startswith(filename_start):
            t = file[29:33]
            time = datetime.datetime.strptime(t,'%H%M').time()
            s5p_list.append({'file':file, 'time':time})
    
    return s5p_list


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
    himawari_dir = all_dir['himawari_raw'] + '/' + str(date.year) + '/' + str(date.strftime('%m')) + '/' + str(date.strftime('%d'))
    frp_list = []
    for file in os.listdir(himawari_dir):
        filename_start = 'CAMS__HMWR_FRP-PIXEL-ListProduct_HMWR-FD_'+str(date.year)+str(date.strftime('%m'))+str(date.strftime('%d'))
        if file.startswith(filename_start):
            t = file[-7:-3]
            time = datetime.datetime.strptime(t,'%H%M').time()
            if time<=latest_time:
                frp_list.append({'file':file, 'time':time})
    
    return frp_list, himawari_dir
            
def fetch_day_frp(frp_list,frp_path):
    firepixels = []
    for i in frp_list:
        himawari_data = frp_himawari.extract_data_h5(frp_path+'/'+i['file'])
        lon = himawari_data['LONGITUDE']
        lat = himawari_data['LATITUDE']

        for x,y in zip(lon.items(), lat.items()):
            lon_point=x[1]
            lat_point=y[1]
            firepixels.append({'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [lon_point, lat_point] }})
    return firepixels

def save_frp(firepixels, date, latest_time):

    naming_string = date.strftime('%Y_%m_%d')+'_till_'+ latest_time.strftime('%H%M')
    bboxfile = all_dir['frp_json']+'/frp_' + naming_string + '.js'

    with open(bboxfile, 'w') as file:
        json.dump(firepixels, file)


def read_frp(date):
    for file in os.listdir(all_dir['frp_json']):
        if file.startswith('frp_'+date.strftime('%Y_%m_%d')):
            with open(all_dir['frp_json']+'/'+file) as data_file:
                data = json.loads(data_file.read())
                return data


def read_s5p_coord(date):
    s5p_coord_list = []
    for file in os.listdir(all_dir['s5p_coord']):
        if file.startswith('s5p_'+ date.strftime('%Y_%m_%d')):
           with open(all_dir['s5p_coord']+'/'+file) as data_file:
                data = json.loads(data_file.read())
                file = file[:-2]+'png'
                s5p_coord_list.append({'file':file, 'coord':data})
    return s5p_coord_list

def read_viirs_coord(date):
    viirs_coord_list =[]
    for file in os.listdir(all_dir['viirs_json']):
        if file.startswith('VIIRS_'+ date.strftime('%Y_%m_%d')):
            with open(all_dir['viirs_json']+'/'+file) as data_file:
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
   

def viirs_day_loop(date_string, viirs_list):
    for i in viirs_list:
        file_path = all_dir['viirs_raw'] + '/' + i['file']
        naming_string = date_string + '_T_' + i['time'].strftime('%H%M')
        viirs.process_viirs(file_path, naming_string)

def s5p_day_loop(date_string, s5p_list):
    for i in s5p_list:
        file_path = all_dir['s5p_raw']+'/'+i['file']
        naming_string = date_string + '_T_' + i['time'].strftime('%H%M')
        read_s5p.netcdf_to_png(file_path, naming_string)



def run_loop_for_day(frp_list, frp_path, viirs_list, s5p_list, date, latest_time):
    date_string = date.strftime('%Y_%m_%d')

    firepixels = fetch_day_frp(frp_list, frp_path)
    save_frp(firepixels, date, latest_time)
    print('\n\n Firepixels Saved :) \n\n')

    viirs_day_loop(date_string, viirs_list)
    print('\n\n VIIRS saved :) \n\n')


    s5p_day_loop(date_string, s5p_list)
    print('\n\n S5P CO saved :) \n\n')

   
    print('\n\n All conversion done :) \n\n')

def run_digitizer(s5p_data, viirs_data, firepixels):        
    for s in s5p_data:
        run = False
        shutil.copyfile(full_path+'/'+all_dir['s5p_png']+'/'+s['file'], full_path+'/'+all_dir['digitise_img']+'/'+s['file'])
        for v in viirs_data:
            if check_overlap_rectangles(s['coord'], v['coord']):
                run = True
                shutil.copyfile(full_path+'/'+all_dir['viirs_png']+'/'+v['file'], full_path+'/'+all_dir['digitise_img']+'/'+v['file'])
                digitizer.run_digitizer(firepixels, v['file'], s['file'], Australia_Shape_Coord, v['coord'])
                pause()
        if run==False:
            digitizer.run_digitizer(firepixels, '', s['file'], Australia_Shape_Coord, s['coord'])
            pause()


if __name__ == '__main__':
    createdirs()
    date = convertDate('20-12-2019') #DD-MM-YYYY
    
    #fetch raw data
    viirs_list = fetch_VIIRS(date)
    s5p_list = fetch_S5P(date)
    latest_time = find_latest_time(viirs_list, s5p_list)
    frp_list, frp_path = fetch_FRP(date, latest_time)

    #run loop and save files
    run_loop_for_day(frp_list, frp_path,  viirs_list, s5p_list, date, latest_time)
  
    #run digitizer after all processing
    s5_data = read_s5p_coord(date)
    viirs_data = read_viirs_coord(date)
    firepixels = read_frp(date)
    run_digitizer(s5_data, viirs_data, firepixels)
   


    
    

   
  
    
    
