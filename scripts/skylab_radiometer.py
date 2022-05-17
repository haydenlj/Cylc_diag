#!/usr/bin/python

"""
Python code to plot global averages of radiometer
first-guess and analysis departures

The innov_ar file is processed by module read_xiv.py

for usage see bottom of file
"""

from datetime import datetime, timedelta
import glob
import os.path
from os import getcwd
import sys

import h5py
import numpy as np
from define_wmo_platform import wmo_platform_names
from plot_global_scatter_map import plot_global

from IPython import embed as shell

def main(filename, channel, image_dir, cdtg=None, window_length=6, sat=None):

    if not os.path.isfile(filename):
        print (" ERROR: input file not found: ", filename)
        sys.exit()
    f = h5py.File(filename, 'r')

    dtg, cdtg = get_dtg(cdtg)
    sensor = get_sensor(f)
    sat = get_platform(f)
    ichan = channel - 1
    
    # this is the start of the window and window length
    str_date = dtg.strftime("%Y%m%dT%HZ")
    awindow = ("PT%dH" % window_length)
    str_date = '_'.join( [str_date, awindow] )

    str_chan = ("ch%d" % channel)

    lat = f['MetaData']['latitude']
    lon = f['MetaData']['longitude']

    print ( "len of lat and lon", len(lat), len(lon) )

    plots = { 'ob':  { 'value' : f['ObsValue']['brightness_temperature'][:,ichan],
                        'title' : ' '.join([sensor.upper(), 'Brightness', 'Temperature']),
                        'plot_range' : [None, None],
                        'units' : 'K',
                      },
              'hofx':  { 'value' : f['hofx0']['brightness_temperature'][:,ichan],
                        'title' : ' '.join([sensor.upper(), 'H(x)' ]),
                        'plot_range' : [None, None],
                        'units' : 'K',
                      },
              'omb':  { 'value' : f['ObsValue']['brightness_temperature'][:,ichan] - f['hofx0']['brightness_temperature'][:,ichan],
                        'title' : ' '.join([sensor.upper(), 'Observation', '-', 'H(x)']),
                        'plot_range' : [None, None],
                        'units' : 'K',
                      },
            }

    for k in plots:
        data = plots[k]['value']
        data_in = data[ data < 400 ]
        lat_in = lat[data < 400 ]
        lon_in = lon[data < 400 ]
        print ( "len of data", len(data) )
        if sat:
            xtitle = ' '.join([sat.upper(), plots[k]['title'], str_chan, str_date])
            image_name = '.'.join([sensor.lower(), sat.lower(), str_chan, k, str_date])
        else:
            xtitle = ' '.join([plots[k]['title'], str_chan, str_date])
            image_name = '.'.join([sensor.lower(), str_chan, k, str_date])

        image_name = os.path.join( image_dir, image_name )
        plot_range = plots[k]['plot_range']
        units = plots[k]['units']
        plot_global(data_in, lat_in, lon_in, xtitle, image_name, range=plot_range, units=units)

    f.close()


def get_dtg(cdtg):

    if not cdtg:
        try:
            str_dtg = f.attrs['date_time_string'].decode("utf-8")
            dtg = datetime.strptime(str_dtg, "%Y-%m-%dT%H:%M:%SZ")
            cdtg = dtg.strftime("%Y%m%d%H")
        except:
            print (" WARNING: no global attribute date_time_string found in data file")
            print (" ERROR: please provide 10-digit yyyymmddhh with -d option")
            sys.exit()
    else:
        dtg = datetime.strptime(cdtg, "%Y%m%d%H")

    return dtg, cdtg


def get_sensor(f):

    try:
        sensor = f.attrs['platformCommonName'].decode("utf-8")
    except:
        sensor = f['MetaData']['station_id'][0].decode("utf-8").split('_')[0]

    return sensor

def get_platform(f):

    try:
        wmo_sat_id = f['MetaData']['satelliteId'][0].item()
        platform = get_platform_name(wmo_sat_id)
    except:
        platform = f['MetaData']['station_id'][0].decode("utf-8").split('_')[1]

    return platform

def get_platform_name(wmo_sat_id):

    try:
        platform = wmo_platform_names[wmo_sat_id]
    except:
        print(" ERROR wmo_sat_id not found in wmo_platform_names")
        print(" ERROR wmo_sat_id provided: ",wmo_sat_id)
        sys.exit()

    return platform

if __name__ == "__main__":

    from optparse import OptionParser

    usage = 'usage: %prog -i input-file -c channel [-o image_dir -d date_time_group -w assimilation_window]'

    parser = OptionParser(usage)
    parser.add_option('-i', '--input-file', dest='filename',
                      action='store', type=str, default=None,
                      help='Location of input file')
    parser.add_option('-c', '--channel', dest='channel',
                      action='store', type=int, default=None,
                      help='channel of sensor to plot')
    parser.add_option('-d', '--cdtg', dest='cdtg',
                      action='store', type=str, default=None,
                      help='10-digit date time group yyyymmddhh')
    parser.add_option('-w', '--assimilation-window', dest='window_length',
                      action='store', type=int, default=6,
                      help='integer defining the hourly assimilation window length')
    parser.add_option('-o', '--image-dir', dest='image_dir',
                      action='store', type=str, default=os.getcwd(),
                      help='directory path in which to place images')
    (options, args) = parser.parse_args()


    # check for file
    if not options.filename:
        parser.error("please supply a file to plot with -i option")
    if not os.path.isfile( options.filename ):
        print('')
        parser.error("can not find file: %s" % options.filename)


    # check on channel
    if not options.channel:
        parser.error("please supply a channel with -c")

    # create output directory path if necessary
    if not os.path.exists(options.image_dir):
        os.mkdir( options.image_dir )

    main(options.filename, options.channel, options.image_dir, cdtg=options.cdtg, window_length=options.window_length)
