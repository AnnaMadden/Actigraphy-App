# Copyright (c) 2020 brainlife.io
#
# This file is a template for a python-based brainlife.io App
# brainlife stages this git repo, writes `config.json` and execute this script.
# this script reads the `config.json` and execute pynets container through singularity
#
# you can run this script(main) without any parameter to test how this App will run outside brainlife
# you will need to copy config.json.brainlife-sample to config.json before running `main` as `main`
# will read all parameters from config.json
#
# Author: Franco Pestilli
# The University of Texas at Austin

# set up environment
import json
import nibabel as nib
import dipy

from dipy.align.reslice import reslice
from dipy.data import get_fnames

# load inputs from config.json
with open('config.json') as config_json:
	config = json.load(config_json)

# Load into variables predefined code inputs
data_file = str(config['t1'])
 
# set the output resolution
#out_res = [ int(v) for v in config['outres'].split(" ")]

# we load the input T1w that we would like to resample
#img = nib.load(data_file)

# we get the data from the nifti file
#input_data   = img.get_data()
#input_affine = img.affine
#input_zooms  = img.header.get_zooms()[:3]

# resample the data
#out_data, out_affine = reslice(input_data, input_affine, input_zooms, out_res)

# create the new NIFTI file for the output
#out_img = nib.Nifti1Image(out_data, out_affine)

# save the output file (with the new resolution) to disk
#nib.save(out_img, 'out_dir/t1.nii.gz')

###############Franco Code above#################

#!/usr/bin/env python
__doc__ = """ActiDocker :: This script takes actigraphy 
.xlsx files, parses and manipulates the movement data, and then 
outputs a new .csv and visuals. Script is specific for Tyler's project
and uses the docker image iamdamion/acti_docker:0.1 \n\n
USAGE:\n
1. cd to local working directory
2. copy .xlsx file to this directory, or place in subdirectory 
- IMPORTANT: .xlsx file must be within the directory you run this script 
  with the docker image, or in a sub directory such as "excel_files". 
  The script will fail if the path to the .xlsx file is in another directory
  because the docker image only has access to the pwd where docker is run. 
3. Run the script using the docker image. (see readme/wiki for detailed instructions)\n\n
- Out directory is created in your pwd (where you run the docker image from)
- Graphs based off code created by Nick Jackson \n
- Script and docker image originally created by Damion V. Demeter, 04.10.20'
"""
__references__ = """References
----------
[]
"""
__version__ = "0.1.0"
​
import argparse,datetime,logging,os,sys,time,xlrd
​
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
# from os import listdir
# from os.path import isfile, join
# import datetime, os, xlrd
# from datetime import date, timedelta
​
pwd = os.getcwd()
​
def main(argv=sys.argv):
    arg_parser = argparse.ArgumentParser(prog='ACTI_DOCKER.py',
                                         allow_abbrev=False,
                                         description=__doc__,
                                         formatter_class=argparse.RawDescriptionHelpFormatter,
                                         epilog=__references__,
                                         usage='%(prog)s xlsx_dir outdir_name [OPTIONS]')
    # Check for arguments. #
    if len(sys.argv[1:])==0:
        print('\nArguments required. Use -h option to print FULL usage.\n')
    arg_parser.add_argument('xlsx_dir', type=os.path.abspath,
                            help='Path to dir with all .xlsx files. This path must be within your pwd. '
                                 'All files within this directory will be included. Be sure '
                            )
    arg_parser.add_argument('outdir_name', type=str,
                            help='Name of output dir UNDER the pwd. If already created, the script '
                                 'will overwrite any files within this directory. If it does not exist, '
                                 'the script will create a directory with this name and write all outputs '
                                 'there.'
                            )
    arg_parser.add_argument('-plots', action='store_true', required=False,
                            help='Create plots in /PLOTS/ subdirectory. ',
                            dest='plots'
                            )
    arg_parser.add_argument('-sublist', action='store', type=os.path.abspath, 
                            required=False, default=os.path.join(pwd,'subject_list.txt'),
                            help='Path to subject list .txt file. Each line should contain '
                                 'FAMILYID <space> subject ID (C1, P1, etc). Each sub in the '
                                 'same family should have its own line.',
                            dest='sublist'
                            )
    arg_parser.add_argument('-quiet', action='store_true', required=False,
                            help='Quiet mode suppresses all QA/extra info '
                                 'printouts. (Errors always printed.)',
                            dest='quiet'
                            )
    arg_parser.add_argument('-v','--version', action='version', version='%(prog)s: ' + __version__)
    args = arg_parser.parse_args()
    # Setting up logger #
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')
    logger = logging.getLogger()
    if not args.quiet:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.ERROR)
​
    #################################################
    ## Script Argument Verification and Assignment ##
    #################################################
    logger.debug('\n--------------------- setup info ---------------------------------')
    # Verify excel dir
    if os.path.isdir(args.xlsx_dir):
        logger.debug(f'-Excel file directory verified: {os.path.abspath(args.xlsx_dir)}')
    else:
        sys.exit('\nERROR: Excel file directory provided does not exist. Please check. Exiting...\n')
    # Verify subject list file
    if os.path.isfile(args.sublist):
        logger.debug(f'-Subject list file verified: {os.path.abspath(args.sublist)}')
    else:
        sys.exit('\nERROR: Subject list file provided does not exist. Please check. Exiting...\n')
    # Verify output dir
    output_dir = os.path.join('outputs',args.outdir_name)
    if os.path.isdir(output_dir):
        logger.debug(f'-Output directory found: {output_dir}')
        logger.debug(' -WARNING: Files will be overwritten.')
    else:
        logger.debug(f'-CREATING output directory: {output_dir}')
        os.mkdir(output_dir)
    # Verify plotting true/false
    logger.debug(f'-Plotting: {args.plots}')
    logger.debug('--------------------------- end ---------------------------------\n')
​
    #################################################
    ##          Global Variable Assignment         ##
    #################################################
    start_time=time.time()
    time.sleep(1)
    today_date = datetime.datetime.now().strftime('%m%d%Y')
​
    # Creating empty "final output" dataframe with column names
    out_df = pd.DataFrame(columns=['SUBID',
                                'AVG_ALL_WAKE_DAY': AVG_ALL_WAKE_DAY, # <- numpy float64
                                'SD_ALL_WAKE_DAY': SD_ALL_WAKE_DAY, # <- numpy float64
                                'AVG_ALL_WAKE_END': AVG_ALL_WAKE_END, # <- numpy float64
                                'SD_ALL_WAKE_END': SD_ALL_WAKE_END, # <- numpy float64
                                'AVG_ALL_SLEEP_DAY': AVG_ALL_SLEEP_DAY, # <- numpy float64
                                'SD_ALL_SLEEP_DAY': SD_ALL_SLEEP_DAY, # <- numpy float64
                                'AVG_ALL_SLEEP_END': AVG_ALL_SLEEP_END, # <- numpy float64
                                'SD_ALL_SLEEP_END': SD_ALL_SLEEP_END, # <- numpy float64
                                'AVG_MAX_BIN_ACTIVE_DAY': AVG_MAX_BIN_ACTIVE_DAY, # <- numpy float64
                                'SD_MAX_BIN_ACTIVE_DAY': SD_MAX_BIN_ACTIVE_DAY, # <- numpy float64
                                'AVG_MAX_BIN_ACTIVE_END': AVG_MAX_BIN_ACTIVE_END, # <- numpy float64
                                'SD_MAX_BIN_ACTIVE_END': SD_MAX_BIN_ACTIVE_END, # <- numpy float64
                                'AVG_MAX_BIN_SLEEP_DAY': AVG_MAX_BIN_SLEEP_DAY, # <- numpy float64
                                'SD_MAX_BIN_SLEEP_DAY': SD_MAX_BIN_SLEEP_DAY, # <- numpy float64
                                'AVG_MAX_BIN_SLEEP_END': AVG_MAX_BIN_SLEEP_END, # <- numpy float64
                                'SD_MAX_BIN_SLEEP_END': SD_MAX_BIN_SLEEP_END, # <- numpy float64
                                'AVG_ALL_BINS_WAKE_DAY': AVG_ALL_BINS_WAKE_DAY, # <- numpy float64
                                'SD_ALL_BINS_WAKE_DAY': SD_ALL_BINS_WAKE_DAY, # <- numpy float64
                                'AVG_ALL_BINS_WAKE_END': AVG_ALL_BINS_WAKE_END, # <- numpy float64
                                'SD_ALL_BINS_WAKE_END': SD_ALL_BINS_WAKE_END, # <- numpy float64
                                'AVG_ALL_BINS_SLEEP_DAY': AVG_ALL_BINS_SLEEP_DAY, # <- numpy float64
                                'SD_ALL_BINS_SLEEP_DAY': SD_ALL_BINS_SLEEP_DAY, # <- numpy float64
                                'AVG_ALL_BINS_SLEEP_END': AVG_ALL_BINS_SLEEP_END, # <- numpy float64
                                'SD_ALL_BINS_SLEEP_END': SD_ALL_BINS_SLEEP_END, # <- numpy float64
                                'NUM_ACTIVE_WEEKDAY': weekdays_active, # <- int
                                'NUM_ACTIVE_WEEKEND': weekend_active, # <- int
                                'PERCENT_DAYS_WORN': percent_days_worn, # <- numpy float64
                                'PERCENT_END_WORN': percent_end_worn # <-numpy float64
                                  ])
​
    #################################################
    ##               DEFINE FUNCTIONS              ##
    #################################################
    def sub2db(famid,subid):
        excel_path = os.path.join(args.xlsx_dir,
                                  famid + '.xlsx')
        if os.path.exists(excel_path) == False:
            sys.exit('\nERROR: Excel file not found. Please check. Exiting...\n' + excel_path)
        else:
            pass
        tab_name = famid + subid
​
        ## Open excel as pandas df (crop A:I - this is stable)
        sub_df = pd.read_excel(excel_path,sheet_name=tab_name,usecols="A:I")
        # search for header line and real data start
        header_index = int(np.where(sub_df.values == 'Activity')[0])
        header = sub_df.iloc[header_index]
        data_start_index = header_index + 2
        # crop df and replace headers
        sub_df = sub_df[data_start_index:]
        sub_df.columns = header
        sub_df = sub_df.reset_index(drop=True)
        # add day of week for later (Monday = 0, Sunday = 6)
        sub_df['Weekday'] = sub_df['Date'].dt.weekday
        return sub_df
​
    def censor_contig(df,thresh):
        indices_to_del = []
        for i in range(len(df)):
            if (sum((df['Interval Status'][i:i+thresh]) == 'ACTIVE')==thresh) & ((df['Activity'][i:i+thresh].sum())==0):
                # print(df.iloc[i+thresh])
                # sys.exit()
                indices_to_del.append(list(range(i,i+thresh)))
​
        indices_to_del = [item for sublist in indices_to_del for item in sublist]
        # print(f'Dropping {len(set(indices_to_del))} rows calculated as "watch off"')
        ## drop rows in to-delete list
        censored_df = df.copy()
        delete_rows = censored_df.index[sorted(set(indices_to_del))] 
        censored_df.drop(delete_rows, inplace=True)
​
        return(censored_df)
​
    def get_avg_max_bin(the_df,bin_size):
        # make bins
        # all_bins = [activity_list[i:i + bin_size] for i in range(0, len(activity_list), bin_size)]
        # above is cleeeean but I need more logic. :(
        activity_list = the_df['Activity'].tolist()
        all_bins = []
        for i in range(0, len(activity_list), bin_size):
            the_bin = activity_list[i:i + bin_size]
            if len(the_bin) == bin_size:
                pass
            else:
                the_bin.extend([0] * (bin_size - len(the_bin)))
​
            all_bins.append(the_bin)
        # Now check for 70% non-zero, and find largest value list index
        high_val = 0
        top_bin = [0]
        for b in all_bins:
            if b.count(0) > 3:
                # print('skipped less than 70%)')
                pass
            else:
                if max(b) > high_val:
                    high_val = max(b)
                    top_bin = b
                else:
                    pass
        if sum(top_bin) == 0:
            avg_max_bin_val = 0
        else:
            avg_max_bin_val = np.mean(top_bin)
​
        return avg_max_bin_val
​
 def get_sd_max_bin(the_df,bin_size):
        # make bins
        # all_bins = [activity_list[i:i + bin_size] for i in range(0, len(activity_list), bin_size)]
        # above is cleeeean but I need more logic. :(
        activity_list = the_df['Activity'].tolist()
        all_bins = []
        for i in range(0, len(activity_list), bin_size):
            the_bin = activity_list[i:i + bin_size]
            if len(the_bin) == bin_size:
                pass
            else:
                the_bin.extend([0] * (bin_size - len(the_bin)))
​
            all_bins.append(the_bin)
        # Now check for 70% non-zero, and find largest value list index
        high_val = 0
        top_bin = [0]
        for b in all_bins:
            if b.count(0) > 3:
                # print('skipped less than 70%)')
                pass
            else:
                if max(b) > high_val:
                    high_val = max(b)
                    top_bin = b
                else:
                    pass
        if sum(top_bin) == 0:
            sd_max_bin_...
