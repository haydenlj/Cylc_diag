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

synop_keys = dict(stationElevation='Station Elevation',
                  stationIdWMOblock='WMO Block ID',
                  stationIdWMOstation='WMO Station ID')
metar_keys = dict(station_elevation='Station Elevation',
#                 station_id='WMO Block and Station ID',
                  unixtime='Unix Time offset',
                  height='Station height')

raob_keys = {  'station_elevation' : {
                  'name' : 'Station Elevation',
                  'units' : 'm',
                  'plot_range' : [None, None],
                   },
                'surface_pressure' : {
                  'name' : 'Surface Pressure',
                  'units' : 'hPa',
                  'plot_range' : [None, None],
                   },
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
                'air_temperature' : {
                  'name' : 'Temperature',
                  'units' : 'K',
                  'plot_range' : [None, None],
                   },
                'specific_humidity' : {
                  'name' : 'Specific Humidity',
                  'units' : 'kg/kg',
                  'plot_range' : [None, None],
                   },
                'geopotential_height' : {
                  'name' : 'Geopotential Height',
                  'units' : 'm',
                  'plot_range' : [None, None],
                   },
    }

#mandatory_levels = [ 1000, 925, 850, 700, 500, 400, 300,
#                    250, 200, 150, 100, 70, 50, 30, 20, 10, 5]
#mandatory_levels = [ 1000, 850, 700, 500, 300, 200, 50, 10]
mandatory_levels = [ 1000, 850, 700, 500, 300, 200, 100]


def main(filename, image_dir, dtg=None, window_length=None, field=None):

    if 'synop' in filename:
        go_synop(filename, image_dir)
    elif 'metar' in filename:
        go_metar(filename, image_dir)
    elif 'raob' in filename or 'radiosonde' in filename:
        go_raob(filename, image_dir, cdtg=dtg, field=field)

def go_raob(filename, image_dir, cdtg=None, window_length=6, field=None):
    f = h5py.File(filename, 'r')
    #shell()
    #sys.exit()
    if not cdtg:
        str_dtg = f.attrs['date_time_string'].decode("utf-8")
        dtg = datetime.strptime(str_dtg, "%Y-%m-%dT%H:%M:%SZ")
        cdtg = dtg.strftime("%Y%m%d%H")
    else:
        dtg = datetime.strptime(cdtg, "%Y%m%d%H")

    # this is the start of the window and window length
    str_date = dtg.strftime("%Y%m%dT%HZ")
    awindow = ("PT%dH" % window_length)
    str_date = '_'.join( [str_date, awindow] )

    # this is the end of the window in 10-digit yyyymmddhh format
    dtg = dtg + timedelta(hours=window_length)
    cdtg = dtg.strftime("%Y%m%d%H")

    sensor = 'Radiosonde'
    #plvl = 500
    for plvl in mandatory_levels:
    #for plvl in [500]:
        str_plvl = ( "%ihPa" % plvl )

        air_pressure = np.array( f['MetaData']['air_pressure'] )
        sfc_pressure = np.array( f['ObsValue']['surface_pressure'] )
        lat_full = f['MetaData']['latitude']
        lon_full = f['MetaData']['longitude']

        p_thresh = 0.015
        print ( '  ....   plotting Pressure range: ', plvl*(1-p_thresh), plvl*(1+p_thresh) )
        locs_01 = np.where( air_pressure > plvl*100.*(1-p_thresh) )
        lat_full = lat_full[ locs_01 ]
        lon_full = lon_full[ locs_01 ]
        air_pressure = air_pressure[ locs_01 ]
        sfc_pressure = sfc_pressure[ locs_01 ]

        locs_02 = np.where( air_pressure < plvl*100.*(1+p_thresh) )
        lat_full = lat_full[ locs_02 ]
        lon_full = lon_full[ locs_02 ]
        air_pressure = air_pressure[ locs_02 ]
        sfc_pressure = sfc_pressure[ locs_02 ]

        locs_03 = np.where( air_pressure < sfc_pressure )
        lat_full = lat_full[ locs_03 ]
        lon_full = lon_full[ locs_03 ]
        air_pressure = air_pressure[ locs_03 ]
        sfc_pressure = sfc_pressure[ locs_03 ]

        for k, v in raob_keys.items():
            # surface pressure, station elevation and geopotential height do not have H(x)
            if 'pressure' in k or 'station' in k or 'height' in k: continue
            print ( '      ....   plotting: ', k )
            plots = { 'ob':  {
                        'value' : f['ObsValue'][k],
                        'name' : 'Observation',
                        },
                 'hofx':  {
                        'value' : f['hofx'][k],
                        'name' : 'H(x)',
                        },
                  'omb':  {
                        'value' : np.array(f['ObsValue'][k]) - np.array(f['hofx'][k]),
                        'name' : 'Ob - H(x)',
                        },
                }

            for k_plot in plots:
                data = plots[k_plot]['value']
                data = data[ locs_01 ]
                data = data[ locs_02 ]
                data = data[ locs_03 ]
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
                xtitle = ' '.join( [sensor, raob_keys[k]['name'], plots[k_plot]['name'], str_plvl, str_date] )
                image_name = '.'.join( [sensor.lower(), k, k_plot, str_plvl, cdtg] )
                image_name = os.path.join( image_dir, image_name )
                plot_range = raob_keys[k]['plot_range']
                units = raob_keys[k]['units']
                try:
                    plot_global(data, lat, lon, xtitle, image_name, range=plot_range, units=units, dot_size=12.5)
                except:
                    print("could not make image: ", image_name)


def go_metar(filename, image_dir):
    f = h5py.File(filename, 'r')

    lat_full = f['MetaData']['latitude']
    lon_full = f['MetaData']['longitude']
    stnID_full = f['MetaData']['station_id']

#   sampled_locs = []
#   for char in ascii_uppercase:
#   #for char in ['C', 'K', 'N']:
#       #print ( "searching letter: ", char)
#       matches = 0
#       for i, station in enumerate(stnID_full):
#           if station.decode("utf-8")[0] == char:
#               matches += 1
#               if char == 'C' or char == 'E' or char == 'K' or char == 'L':
#                   lim = 750
#               else:
#                   lim = 100
#               if (matches % lim) == 1:
#                   sampled_locs.append( i )
#                   print( station.decode("utf-8") )
#               #shell()
#               #sys.exit()
#       #print ( char, " matches: ", matches)

#   sampled_locs = sorted(sampled_locs)

    for k, v in metar_keys.items():
#   if True:
#       k = 'unixtime'
#       v = 'Unix Time offset'
        data = f['MetaData'][k]
        gpos = np.where(np.array(data) < 1.e11)
#       gpos = sampled_locs
        lat = lat_full[gpos]
        lon = lon_full[gpos]
        data = data[gpos]
        #print ("len of lat and lon", len(lat), len(lon))
        #print ("len of data", len(data))
        # shell()

        xtitle = 'sampled METAR ' + v
        image_name = 'metar_'+k+'_2021080100_sampled'
        range = None
        units = v
        plot_global(data, lat, lon, xtitle, image_name, range = range, units = units, dot_size=15)

def go_synop(filename, image_dir):
    f = h5py.File(filename, 'r')

    #['MetaData', 'ObsValue', 'nlocs']
    #['datetime', 'latitude', 'longitude', 'stationElevation', 'stationIdWMOblock', 'stationIdWMOstation']
    #f['MetaData']['datetime'][0]
    # b'2021-08-01T00:00:1e+11Z'
    lat_full = f['MetaData']['latitude']
    lon_full = f['MetaData']['longitude']
    block_full = f['MetaData']['stationIdWMOblock']

    sampled_locs = []
    for jb in np.arange(120):
        locs = np.where( np.array(block_full) == jb )
        if len(locs[0]) > 0:
            mid_point = int(np.floor((len(locs[0]) - 1) / 2))
            #shell()
            #sys.exit()
            sampled_locs.append( locs[0][mid_point] )
    sampled_locs = sorted(sampled_locs)

    #for k, v in synop_keys.items():
    if True:
        k = 'stationIdWMOblock'
        v = 'WMO Block ID'
        data = f['MetaData'][k]
        #gpos = np.where(np.array(data) < 1.e11)
        gpos = sampled_locs
        lat = lat_full[gpos]
        lon = lon_full[gpos]
        data = data[gpos]
        #print ("len of lat and lon", len(lat), len(lon))
        #print ("len of data", len(data))
        # shell()

        xtitle = 'sampled - Synop ' + v
        image_name = 'synop_'+k+'_2021080100_sampled'
        range = None
        units = v
        plot_global(data, lat, lon, xtitle, image_name, range = range, units = units, dot_size=15)

if __name__ == "__main__":

    from optparse import OptionParser

    usage = 'usage: %prog -i input-file [-f field  -o image_dir]'

    parser = OptionParser(usage)
    parser.add_option('-i', '--input-file', dest='filename',
                      action='store', type=str, default=None,
                      help='Location of input file')
    parser.add_option('-f', '--field', dest='field',
                      action='store', type=str, default=None,
                      help='field in input data to plot')
    parser.add_option('-d', '--dtg', dest='dtg',
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


    # create output directory path if necessary
    if not os.path.exists(options.image_dir):
        try:
            os.mkdir( options.image_dir )
        except:
            print( 'making directories: ', options.image_dir )
            os.makedirs( options.image_dir )

    main(options.filename, options.image_dir, dtg=options.dtg, window_length=options.window_length, field=options.field)
