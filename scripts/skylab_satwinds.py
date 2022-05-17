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

from IPython import embed as shell

satwind_keys = {  
                'eastward_wind' : {
                  'name' : 'U-Wind',
                  'units' : 'm/s',
                  'plot_range' : [None, None],
                   },
                'northward_wind' : {
                  'name' : 'V-Wind',
                  'units' : 'm/s',
                  'plot_range' : [None, None],
                   },
                'air_pressure' : {
                  'name' : 'Pressure',
                  'units' : 'hPa',
                  'plot_range' : [None, None],
                   },
    }

mandatory_levels = [ 850, 700, 500, 300, 200, 100]

class obData:
    def __init__(self):
        self.init = False

def main(filenames, image_dir, cdtg=None, window_length=None):

    sensor = "GeoSatelliteWinds"

    # set a time tag for the image
    dtg = datetime.strptime(cdtg, "%Y%m%d%H")

    # this is the start of the window and window length
    str_date = dtg.strftime("%Y%m%dT%HZ")
    awindow = ("PT%dH" % window_length)
    str_date = '_'.join( [str_date, awindow] )

    # this is the end of the window in 10-digit yyyymmddhh format
    dtg = dtg + timedelta(hours=window_length)
    cdtg = dtg.strftime("%Y%m%d%H")

    objData = obData()

    for afile in filenames:

        latitude, longitude, air_pressure, observation, hofx, fg_depar = read_data(afile)
        if not objData.init:
            objData.init = True
            objData.lat = latitude
            objData.lon = longitude
            objData.pressure = air_pressure
            objData.ob = observation
            objData.hofx = hofx
            objData.fg_depar = fg_depar
        else:
            shell()
            sys.exit()
            objData.lat = latitude
            objData.lon = longitude
            objData.pressure = air_pressure
            objData.ob = observation
            objData.hofx = hofx
            objData.fg_depar = fg_depar

    for plvl in mandatory_levels:
    #for plvl in [500]:
        str_plvl = ( "%ihPa" % plvl )

        air_pressure = np.array(objData.pressure)
        lat_full = np.array(objData.lat)
        lon_full = np.array(objData.lon)

        p_thresh = 0.1
        print ( '  ....   plotting Pressure range: ', plvl*(1-p_thresh), plvl*(1+p_thresh) )
        locs_01 = np.where( air_pressure > plvl*100.*(1-p_thresh) )
        lat_full = lat_full[ locs_01 ]
        lon_full = lon_full[ locs_01 ]
        air_pressure = air_pressure[ locs_01 ]

        locs_02 = np.where( air_pressure < plvl*100.*(1+p_thresh) )
        lat_full = lat_full[ locs_02 ]
        lon_full = lon_full[ locs_02 ]
        air_pressure = air_pressure[ locs_02 ]

        for k, v in satwind_keys.items():
            # surface pressure, station elevation and geopotential height do not have H(x)
            if 'pressure' in k: continue
            print ( '      ....   plotting: ', k )
            plots = { 'ob':  {
                        'value' : np.array(objData.ob[k]),
                        'name' : 'Observation',
                        },
                 'hofx':  {
                        'value' : np.array(objData.hofx[k]),
                        'name' : 'H(x)',
                        },
                  'omb':  {
                        'value' : objData.fg_depar[k],
                        'name' : 'Ob - H(x)',
                        },
                }

            for k_plot in plots:
                #print (" restrict ", k, " for pressure range ")
                data = plots[k_plot]['value']
                data = data[ locs_01 ]
                data = data[ locs_02 ]
                #print (" restrict ", k, " for physical reality ")
                gpos = np.where(np.array(data) < 1.e11)
                lat = lat_full[gpos]
                lon = lon_full[gpos]
                data = data[gpos]
                gpos = np.where(np.array(data) > -1.e11)
                lat = lat_full[gpos]
                lon = lon_full[gpos]
                data = data[gpos]
                #print ("len of lat and lon", len(lat), len(lon))
                #print ("len of data", len(data))
                # shell()
                xtitle = ' '.join( [sensor, satwind_keys[k]['name'], plots[k_plot]['name'], str_plvl, str_date] )
                image_name = '.'.join( [sensor.lower(), k, k_plot, str_plvl, cdtg] )
                image_name = os.path.join( image_dir, image_name )
                plot_range = satwind_keys[k]['plot_range']
                units = satwind_keys[k]['units']
                print ( len(data), len(lat), len(lon) )
                try:
                    plot_global(data, lat, lon, xtitle, image_name, range=plot_range, units=units, dot_size=5.)
                except:
                    print("could not make image: ", image_name)


def read_data(afile):

    f = h5py.File(afile, 'r')
    #shell()
    #sys.exit()
    latitude = f['MetaData']['latitude']
    longitude = f['MetaData']['longitude']
    air_pressure = f['MetaData']['air_pressure']
    observation = {}
    hofx = {}
    fg_depar = {}
    for k, v in satwind_keys.items():
        if 'pressure' in k: continue
        observation[k] = f['ObsValue'][k]
        hofx[k] = f['hofx'][k]
        fg_depar[k] = np.array(f['ObsValue'][k]) - np.array(f['hofx'][k])


    return latitude, longitude, air_pressure, observation, hofx, fg_depar


if __name__ == "__main__":

    from argparse import ArgumentParser

    parser = ArgumentParser(
        description=(
            'Read satwind IODA output and make a map plot')
    )

    required = parser.add_argument_group(title='required arguments')
    required.add_argument('-i', '--input-files', nargs='+', dest='filenames',
                          action='store', default=None, required=True,
                          help='input files')
    required.add_argument('-d', '--dtg', dest='dtg',
                      action='store', type=str, default=None, required=True,
                      help='10-digit date time group yyyymmddhh')

    optional = parser.add_argument_group(title='optional arguments')

    optional.add_argument('-o', '--image-dir', dest='image_dir',
                      action='store', type=str, default=os.getcwd(),
                      help='directory path in which to place images')
    optional.add_argument('-w', '--assimilation-window', dest='window_length',
                      action='store', type=int, default=6,
                      help='integer defining the hourly assimilation window length')
    args = parser.parse_args()


    # check for file
    if not args.filenames:
        parser.error("please supply file(s) to plot with -i option")

    # create output directory path if necessary
    if not os.path.exists(args.image_dir):
        try:
            os.mkdir( args.image_dir )
        except:
            print( 'making directories: ', args.image_dir )
            os.makedirs( args.image_dir )

    main(args.filenames, args.image_dir, cdtg=args.dtg, window_length=args.window_length)
