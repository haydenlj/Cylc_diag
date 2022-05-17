#!/usr/bin/python

"""
Python code to plot global averages of radiometer innovations
innovation as a function of impact height

The innov_ar file is processed by module read_xiv.py

Usage:
python innovar_radiance.py [data_time_group] [ndays]

"""

from datetime import datetime, timedelta
import glob
import os.path
from os import getcwd
import sys

import h5py
import numpy as np
from plot_global_scatter_map import plot_global

# from IPython import embed as shell

sensor = 'TROPICS01'

def main(filename, channel, image_dir, dtg=None, window_length=6, sat=None):


    f = h5py.File(filename, 'r')

    if not dtg:
        str_dtg = f.attrs['date_time_string'].decode("utf-8")
        dtg = datetime.strptime(str_dtg, "%Y-%m-%dT%H:%M:%SZ")
        cdtg = dtg.strftime("%Y%m%d%H")
    else:
        cdtg = str(dtg)
        dtg = datetime.strptime(cdtg, "%Y%m%d%H")

    
    # this is the start of the window and window length
    str_date = dtg.strftime("%Y%m%dT%HZ")
    awindow = ("PT%dH" % window_length)
    str_date = '_'.join( [str_date, awindow] )

    # this is the end of the window in 10-digit yyyymmddhh format
    dtg = dtg + timedelta(hours=window_length)
    cdtg = dtg.strftime("%Y%m%d%H")

    print ( "the time: ", cdtg )

    lat = f['MetaData']['latitude']
    lon = f['MetaData']['longitude']
    lat2, lon2 = 90.0, 0.0
    # dist = [check_distance(lat1=i, lon1=j, lat2=lat2, lon2=lon2) for i, j in zip(lat,lon)]
    # dist = np.array(dist)


    ichan = channel - 1
    str_chan = ("ch%d" % channel)
    ob = f['ObsValue']['brightness_temperature'][:,ichan]
    bk = f['hofx']['brightness_temperature'][:,ichan]
    xiv = ob - bk
    print ( "len of lat and lon", len(lat), len(lon) )

#   plots = { 'ob':  { 'value' : dist,
    plots = { 'ob':  { 'value' : f['ObsValue']['brightness_temperature'][:,ichan],
                        'title' : ' '.join([sensor, 'Brightness', 'Temperature']),
                        'plot_range' : [None, None],
                        'units' : 'K',
                      },
              'hofx':  { 'value' : f['hofx']['brightness_temperature'][:,ichan],
                        'title' : ' '.join([sensor, 'H(x)' ]),
                        'plot_range' : [None, None],
                        'units' : 'K',
                      },
              'omb':  { 'value' : f['ObsValue']['brightness_temperature'][:,ichan] - f['hofx']['brightness_temperature'][:,ichan],
                        'title' : ' '.join([sensor, 'Observation', '-', 'H(x)']),
                        'plot_range' : [None, None],
                        'units' : 'K',
                      },
            }

    for k in plots:
        data = plots[k]['value']
        chk = (ob < 400) & (bk < 400) & (ob > 135) & (bk > 135) # & (dist > 1100)
        data_in = data[ chk ]
        lat_in = lat[ chk ]
        lon_in = lon[ chk ]
        if np.isnan(np.min(data_in)) or np.isnan(np.max(data_in)):
            print ( " suspect data for field " , k, " channel " + str_chan )
            continue
        print ( "len of data", len(data) )
        if sat:
            xtitle = ' '.join([sat, plots[k]['title'], str_chan, str_date])
            image_name = '.'.join([sensor.lower(), sat, str_chan, k, cdtg])
        else:
            xtitle = ' '.join([plots[k]['title'], str_chan, str_date])
            image_name = '.'.join([sensor.lower(), str_chan, k, cdtg])

        image_name = os.path.join( image_dir, image_name )
        plot_range = plots[k]['plot_range']
        units = plots[k]['units']
        plot_global(data_in, lat_in, lon_in, xtitle, image_name, range=plot_range, units=units)

    f.close()


def check_distance(lat1=0.0, lon1=0.0, lat2=0.0, lon2=0.0):

    # ensure longitude is between -180 and 180
    lon1 = ((lon1 + 180.0) % 360.0) - 180.0
    lon2 = ((lon2 + 180.0) % 360.0) - 180.0

    # calculate deltas
    dlon = lon1 - lon2
    dlat = lat1 - lat2

    # convert to radians
    lon1_in_rad = np.deg2rad( lon1 )
    lat1_in_rad = np.deg2rad( lat1 )

    lon2_in_rad = np.deg2rad( lon2 )
    lat2_in_rad = np.deg2rad( lat2 )

    # calculate deltas in radians
    dlon_in_rad = lon1_in_rad - lon2_in_rad
    dlat_in_rad = lat1_in_rad - lat2_in_rad

    earth_radius = 6378.137
    # calculate distance (Euclidean)
    dlon = dlon * np.cos( lat2_in_rad )
    dist = np.sqrt( dlon*dlon + dlat*dlat )

    #rth_radius method haversine
    # a = np.sin(dlat_in_rad/2)**2 + np.cos(lat2_in_rad) * np.cos(lat1_in_rad) * np.sin(dlon_in_rad/2)**2
    # c = 2 * np.arctan2( np.sqrt( a ), np.sqrt( 1 - a ) )
    # dist = np.rad2deg( c )

    # convert to km
    dist = np.deg2rad(dist) * earth_radius

    return dist


if __name__ == "__main__":

    from optparse import OptionParser

    usage = 'usage: %prog -i input-file -c channel [-f field  -p satellite -o image_dir]'

    parser = OptionParser(usage)
    parser.add_option('-i', '--input-file', dest='filename',
                      action='store', type=str, default=None,
                      help='Location of input file')
    parser.add_option('-c', '--channel', dest='channel',
                      action='store', type=int, default=None,
                      help='channel of sensor to plot')
    parser.add_option('-d', '--dtg', dest='dtg',
                      action='store', type=int, default=None,
                      help='10-digit date time group yyyymmddhh')
    parser.add_option('-w', '--assimilation-window', dest='window_length',
                      action='store', type=int, default=6,
                      help='integer defining the hourly assimilation window length')
    parser.add_option('-o', '--image-dir', dest='image_dir',
                      action='store', type=str, default=os.getcwd(),
                      help='directory path in which to place images')
    parser.add_option('-p', '--platform', dest='platform',
                      action='store', type=str, default=None,
                      help='platform or satellite name')
    (options, args) = parser.parse_args()


    # check for innovation file
    if not options.filename:
        parser.error("please supply an innovation file to plot with -i option")
    if not os.path.isfile( options.filename ):
        print('')
        parser.error("can not find innovation file: %s" % options.filename)


    # check on channel
    if not options.channel:
        parser.error("please supply a channel with -c")

    # create output directory path if necessary
    if not os.path.exists(options.image_dir):
        os.mkdir( options.image_dir )

    main(options.filename, options.channel, options.image_dir, dtg=options.dtg, window_length=options.window_length, sat=options.platform)
