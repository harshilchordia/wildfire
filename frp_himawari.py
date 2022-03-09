import h5py
import numpy as np
import pandas as pd
import os

pd.set_option('display.max_columns', 500)


def extract_data_h5(file_path):

    msg_f = file_path
    # if they exist open them and extract the data, applying scalling and make panda
    if (os.path.exists(msg_f)):
        #print('Processing.....')
    
        with h5py.File(msg_f, 'r') as h5:
            msg_d ={'ACQTIME':h5['ACQTIME'][:].flatten(),                   #apply scaling factor
                        'LATITUDE':h5['LATITUDE'][:]                           /1000,
                        'LONGITUDE':h5['LONGITUDE'][:].flatten()               /1000,
                        'FRP':h5['FRP'][:].flatten()                           /10,
                        'FRP_UNCERTAINTY':h5['FRP_UNCERTAINTY'][:].flatten()   /100,
                        'PIXEL_SIZE':h5['PIXEL_SIZE'][:].flatten()             /100,
                        'PIXEL_VZA':h5['PIXEL_VZA'][:].flatten()               /100,
                        'ABS_LINE':h5['ABS_LINE'][:].flatten(),
                        'ABS_PIXEL':h5['ABS_PIXEL'][:].flatten()}
            msg_df = pd.DataFrame(data=msg_d,dtype=np.float32)
            msg_df['pixel_tag'] = msg_df.ABS_PIXEL*1000000

        msg_df = msg_df.reset_index(drop=True)
       
        return msg_df

    else:
        # print("ERROR when trying to open file, this file does not exist:", msg_datetime.strftime(DataDir + "%Y/HDF5_LSASAF_MSG-IODC_FRP-PIXEL-ListProduct_IODC-Disk_%Y%m%d%H%M.bz2")
        print("file not found: " + file_path)

    msg_df = pd.DataFrame()
    return msg_df





