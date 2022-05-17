#!/usr/bin/env python

"""
Parse and plot NEPTUNE DA IODA radiance stats files.

Original Author: Benjamin Ruston, NRL

"""

import datetime
import glob
import logging
import numpy as np
import optparse
import os.path
import sys
import time

from radiometer_define import sat_sen
from plot_rad_stats import plot_figures,    \
                           plot_rad_grams,  \
                           plot_ob_count,   \
                           plot_x_labels,   \
                           get_x_labels,    \
                           dtg_range,       \
                           spread_data
from read_ioda_netcdf import read_ioda
from IPython import embed as shell

try:
    parse_datetime = datetime.datetime.strptime
except AttributeError:
    parse_datetime = lambda str, fmt: datetime.datetime(*(time.strptime(str, fmt)[0:6]))

LOG        = logging.getLogger(__name__)
LOG_FORMAT = '%(message)s'

FMT_YYYYMMDDHHMN = '%Y%m%dT%H%MZ'
FMT_YYYYMMDDHH = '%Y%m%d%H'
FMT_YYYYMMDD   = '%Y%m%d'
FMT_YYYYMM     = '%Y%m'

DEFAULT_END_DATE  = datetime.datetime.today()
DEFAULT_LOOK_BACK = 30  # days

MISSING = -999.9


#----------------------------------------------------------------------
# Top-Level
#----------------------------------------------------------------------


def main(args, start_date, end_date):
    """
    Given a directory of IODA netCDF output files
    """
    LOG.debug('Starting DTG is: %s' % start_date.strftime(FMT_YYYYMMDDHH))
    LOG.debug('Ending DTG is:   %s' % end_date.strftime(FMT_YYYYMMDDHH))


    filenames = args.filenames
    image_dir = args.image_dir
    exp_name  = args.exp_name


    stat_data = process_sensor( filenames, start_date, end_date )

    # if not stat_data: continue
    # shell()
    # sys.exit()

    for k in stat_data:
        sensor = k.split('_')[-1]
        plot_figures(stat_data, sensor, start_date, end_date, image_dir, exp_name)


#----------------------------------------------------------------------
# Data Parsing 
#----------------------------------------------------------------------

def process_sensor( filenames, start_date, end_date ):
    # Generate the full date range
    delta      = datetime.timedelta(hours=6)
    date_range = dtg_range(start_date, end_date, delta)

    sensor_stats = None

    for filename in filenames:
        
        # cycle if no file
        if not os.path.isfile( filename ): continue
        
        print( 'processing: ', filename )
        i = 0
        # can get this number of channels from file but how a priori?
        for i in range(15):
            d, count = read_ioda(filename, i+1)

            # cycle if no data
            if not d:
                print('No data found in {} index {}, skipping...'.format(filename ,i))
                continue
            else:
                pass
                # print('Index {} has {} obs'.format(i, count))

            # shell()
            # sys.exit()

            sensor = d['sensor'].lower()
            ilimit = len(sat_sen[sensor]['freq'])
            try:
                platform = sat_sen[sensor]['sat'][sat_sen[sensor]['wmo_sat_ids'].index(d['wmo_sat_id'])]
            except:
                platform = sat_sen[sensor]['sat'][sat_sen[sensor]['short_sat_ids'].index(d['wmo_sat_id'])]
            dtg = d['dtg']

            # initialize sensor_stats
            key = '%s_%s' % (platform.upper(), d['sensor'].lower())
            if not sensor_stats:  
                sensor_stats = {}
            if key not in sensor_stats.keys():
                sensor_stats[key] = {}

            # load channel stats into dictionary
            chan = ( "%i" % (i+1) )
            innov_vals = np.ma.masked_outside( d['fg_depar'], MISSING, -MISSING ).compressed()
            bias_corr = np.ma.masked_outside( d['bias_corr'], MISSING, -MISSING ).compressed()
            nchan = len(innov_vals)
            if nchan == 0: continue
            stdv_innov = np.nanstd( innov_vals )
            innov = np.nanmean( innov_vals )
            raw_innov = np.nanmean( innov + bias_corr )
            status = 'assim'
            if chan not in sensor_stats[key].keys(): 
                sensor_stats[key][chan] = {}
            sensor_stats[key][chan][dtg] = (raw_innov, innov, stdv_innov, nchan, status)

    return sensor_stats

if __name__ == "__main__":

    from argparse import ArgumentParser

    parser = ArgumentParser(
        description=(
            'Read satwind IODA output and make a map plot')
    )


    required = parser.add_argument_group(title='required arguments')
    required.add_argument('-i', '--input-files', nargs='+', dest='filenames', 
                       action='store', default=None,
                       help='directory path to input, sensor summary files')

    optional = parser.add_argument_group(title='optional arguments')
    optional.add_argument('-d', '--end-date', dest='end_date', 
                       action='store', default=DEFAULT_END_DATE,
                       help='date time group for end of time window')
    optional.add_argument('-o', '--image-dir', dest='image_dir', 
                       action='store', default=os.getcwd(),
                       help='directory to output images')
    optional.add_argument('-n', '--ndays', dest='look_back', 
                       action='store', default=DEFAULT_LOOK_BACK,
                       help='size of time window in days')
    optional.add_argument('-r', '--exp-name', dest='exp_name', 
                       action='store', default=None,
                       help='experiment name to use in labeling')
    args = parser.parse_args()

    # create output directory if it does not exist
    if not os.path.exists(args.image_dir):
        os.makedirs(args.image_dir)

    # convert 10-digit datetime to date object, use default object (today) if none provided
    if args.end_date == DEFAULT_END_DATE:
        end_date = args.end_date
    else:
        try:
            end_date = parse_datetime(args.end_date, FMT_YYYYMMDDHH)
        except:
            parser.error("end date supplied with -d should be 10-digit yyyymmddhh provided: %s"% args.end_date)
 
    # make sure look back is an integer
    try:
        look_back = int(args.look_back)
    except:
        parser.error("number of days supplied with -n should be integer provided: %s"% args.look_back)
    start_date = end_date - datetime.timedelta(look_back)

    main(args, start_date, end_date)
