#!/usr/bin/python

"""
Python code to plot locations of conventional data

Usage:
python conventional_quick_look.py input_file

"""

from datetime import datetime, timedelta
import os.path
from os import getcwd
import sys

import h5py
import numpy as np
from string import ascii_uppercase
from plot_global_scatter_map import plot_global

#from IPython import embed as shell

aircraft_keys = {  'eastward_wind' : {
                  'name' : 'U-Wind',
                  'units' : 'm/s',
                  'plot_range' : [None, None],
                   },
                'northward_wind' : {
                  'name' : 'V-Wind',
                  'units' : 'm/s',
                  'plot_range' : [None, None],
                   },
                'air_temperature' : {
                  'name' : 'Temperature',
                  'units' : 'K',
                  'plot_range' : [200., 300.],
                   },
                'height' : {
                  'name' : 'Altitude',
                  'units' : 'm',
                  'plot_range' : [None, None],
                   },
    }

def main(args):

    filename = args.filename
    image_dir = args.image_dir

    dtg = datetime.strptime(args.dtg, "%Y%m%d%H")

    # this is the start of the window and window length
    str_date  = dtg.strftime("%Y%m%dT%HZ")
    awindow = ("PT%dH" % args.window_length)
    str_date  = '_'.join( [str_date, awindow] )

    # this is the end of the window in 10-digit yyyymmddhh format
    dtg = dtg + timedelta(hours=args.window_length)
    cdtg = dtg.strftime("%Y%m%d%H")

    f = h5py.File(filename, 'r')

    sensor = 'Aircraft'

    height = np.array( f['MetaData']['height'] )
    lat = f['MetaData']['latitude']
    lon = f['MetaData']['longitude']

    # surface pressure, station elevation and geopotential height do not have H(x)
    k = 'air_temperature'
    ob   = np.array( f['ObsValue'][k] )
    hofx = np.array( f['hofx0'][k] )
    print ( '      ....   plotting: ', k )
    plots = { 'ob':  {
                'name' : 'Observation',
                'value' : ob,
                },
         'hofx':  {
                'name' : 'H(x)',
                'value' : hofx,
                },
          'omb':  {
                'name' : 'Ob - H(x)',
                'value' : ob - hofx,
                },
        }

    for k_plot in plots:
        data = plots[k_plot]['value']
        #print ("len of lat and lon", len(lat), len(lon))
        #print ("len of data", len(data))
        #shell()
        xtitle = ' '.join( [sensor, aircraft_keys[k]['name'], plots[k_plot]['name'], str_date] )
        image_name = '.'.join( [sensor.lower(), k, k_plot, cdtg] )
        image_name = os.path.join( image_dir, image_name )
        plot_range = aircraft_keys[k]['plot_range']
        if 'omb' in k_plot:
            plot_range = [-5, 5]
        units = aircraft_keys[k]['units']
        plot_global(data, lat, lon, xtitle, image_name, range=plot_range, units=units, dot_size=5.0)

if __name__ == "__main__":

    from optparse import OptionParser

    usage = 'usage: %prog -i input-file -d dtg -w window [-o image_dir]'

    parser = OptionParser(usage)
    parser.add_option('-i', '--input-file', dest='filename',
                      action='store', default=None,
                      help='Location of input file')
    parser.add_option('-d', '--dtg', dest='dtg',
                      action='store', type=str, default=None,
                      help='10-digit date time group yyyymmddhh')
    parser.add_option('-w', '--assimilation-window', dest='window_length',
                      action='store', type=int, default=6,
                      help='integer defining the hourly assimilation window length')
    parser.add_option('-o', '--image-dir', dest='image_dir',
                      action='store', default=os.getcwd(),
                      help='directory path in which to place images')
    (options, args) = parser.parse_args()


    # check for innovation file
    if not options.filename:
        parser.error("please supply an innovation file to plot with -i option")
    if not os.path.isfile( options.filename ):
        print('')
        parser.error("can not find innovation file: %s" % options.filename)


    # create output directory path if necessary
    if not os.path.exists(options.image_dir):
        try:
            os.mkdir( options.image_dir )
        except:
            print( 'making directories: ', options.image_dir )
            os.makedirs( options.image_dir )

    main(options)
