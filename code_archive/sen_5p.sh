#!/bin/bash


SenDir=/home/hann/dataDisk/validation_data/Sentinal_5P/original_data/


cd ${SenDir}
ls S5P_OFFL_L2* > co_files.txt

while read -r CO_file; do
	echo "${CO_file:20:8}"
	python3 /home/hann/gnu_WRF-CMAQ/scripts/wrf-cmaq/cmaq_analysis/sen_5p_co_timestamp.py ${CO_file}
	time_stamp=`cat ./time_stamp.txt`
	echo $time_stamp
	harpconvert -a 'CO_column_number_density_validity>50;bin_spatial(351,-35,0.1,351,10,0.1)' ${CO_file} SA_Sentinal_5P_CO_${time_stamp}.nc
	rm ./time_stamp.txt
done < co_files.txt
#harpconvert -a 'bin_spatial(350,-35,0.1,350,10,0.1)'