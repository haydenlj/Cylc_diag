#!/usr/bin/python

"""
Python code to read data from IODA netCDF

Usage:
python read_ioda_netcdf.py [filename]
"""

#import pdb
from IPython import embed as shell

import datetime
import numpy as np
from netCDF4 import Dataset  # http://code.google.com/p/netcdf4-python/
import os
import re
import sys
import numpy.ma as ma


def main(filename):

    d, data_count = read_ioda(filename, 9)

def read_ioda_raob(filename, d):

    nc_fid = open_ioda_file( filename )

    raob_ioda_vars = [     \
      'air_temperature',   \
      'specific_humidity', \
      'eastward_wind',     \
      'northward_wind' ]
    metaData_vars = [    \
      'air_pressure',    \
      'latitude',        \
      'longitude',       \
      'instrumentType',  \
      'station_id' ]
#     'stationIdWMOstation'  # ??

    for name in metaData_vars:
        if name not in d.keys():
            d[name] = nc_fid['MetaData'][name][:]
        else:
            d[name] = np.concatenate( (d[name], nc_fid['MetaData'][name][:] ), axis=None )
    for name in raob_ioda_vars:
        if name not in d.keys():
            d[name]               = nc_fid['ObsValue'][name][:]
            try:
                d[name + '_bk']       = nc_fid['hofx0'][name][:]
            except:
                d[name + '_bk']       = nc_fid['hofx'][name][:]
            try:
                d[name + '_an']       = nc_fid['hofx1'][name][:]
            except:
                d[name + '_an']       = nc_fid['hofx'][name][:]
            try:
                d[name + '_qc1']      = nc_fid['EffectiveQC1'][name][:]
            except:
                d[name + '_qc1']      = nc_fid['EffectiveQC'][name][:]
        else:
            d[name]               = np.concatenate( ( d[name],               nc_fid['ObsValue'][name][:] ), axis=None )
            try:
                d[name + '_bk']       = np.concatenate( ( d[name + '_bk'],       nc_fid['hofx0'][name][:] ), axis=None )
            except:
                d[name + '_bk']       = np.concatenate( ( d[name + '_bk'],       nc_fid['hofx'][name][:] ), axis=None )
            try:
                d[name + '_an']       = np.concatenate( ( d[name + '_an'],       nc_fid['hofx1'][name][:] ), axis=None )
            except:
                d[name + '_an']       = np.concatenate( ( d[name + '_an'],       nc_fid['hofx'][name][:] ), axis=None )
            try:
                d[name + '_qc1']      = np.concatenate( ( d[name + '_qc1'],      nc_fid['EffectiveQC1'][name][:] ), axis=None )
            except:
                d[name + '_qc1']      = np.concatenate( ( d[name + '_qc1'],      nc_fid['EffectiveQC'][name][:] ), axis=None )
    for name in raob_ioda_vars:
        d[name + '_fg_depar'] = d[name] - d[name + '_bk']
        d[name + '_an_depar'] = d[name] - d[name + '_an']
        if 'humidity' in name:
            d[name + '_fg_depar'] *= 1000.
            d[name + '_an_depar'] *= 1000.

    return d


def read_ioda(filename, channel, field=None):

    nc_fid = open_ioda_file( filename )

    name = ("brightness_temperature")
    # print ( name )

#   verbose -- return if channel is not present
    if channel not in nc_fid.variables['nchans'][:]:
       print ( "Channel %s not found in IODA file" % channel )
       nc_fid.close()
       return None, None

    ichannel=np.where(nc_fid.variables['nchans'][:]== channel)[0]

#   verbose -- what channels are present
#   for var in nc_vars:
#       if 'brightness_temperature' in var and 'depbg' in var:
#           print ( var )
#   verbose -- possible fields
#       if name in var:
#           print ( var )

#   GSI_HofX =  nc_fid.variables['brightness_temperature_11@GsiHofX'][:]

    d                = {}
#   just  missing values in first-guess departures
#   data_mask        = np.ma.masked_outside( nc_fid.variables[name + '@depbg'][:], -99999, 99999 )
#   QC1 appears to catch missing values and JEDI filters
    data_mask        = np.ma.masked_greater( nc_fid['EffectiveQC1'][name][:,ichannel], 1).mask
    d['lat']         = np.ma.array( nc_fid['MetaData']['latitude'][:], mask = data_mask ).compressed()
    d['lon']         = np.ma.array( nc_fid['MetaData']['longitude'][:], mask = data_mask ).compressed()
    d['ob']          = np.ma.array( nc_fid['ObsValue'][name][:,ichannel], mask = data_mask ).compressed()
    d['bk']          = np.ma.array( nc_fid['hofx0'][name][:,ichannel], mask = data_mask ).compressed()
    d['an']          = np.ma.array( nc_fid['hofx1'][name][:,ichannel], mask = data_mask ).compressed()
    d['an_depar']    = d['ob'] - d['an']
    d['fg_depar']    = d['ob'] - d['bk']
    d['bias_corr']   = np.ma.array( nc_fid['ObsBias0'][name][:,ichannel], mask = data_mask ).compressed()
    if field:
        d[field]     = np.ma.array( nc_fid[field][name][:,ichannel], mask = data_mask ).compressed()

    # parse a string dtg need to add epoch time generation
    try:
        str_dtg = nc_fid.date_time_string
        dtg = datetime.datetime.strptime(str_dtg, "%Y-%m-%dT%H:%M:%SZ") + datetime.timedelta(hours=3)
    except:
        str_dtg = re.search("\d{10}", os.path.basename(nc_fid.filepath())).group()
        if len(str_dtg) != 10:
            print("  ... Error: could not determine dateTime")
            sys.exit()
        dtg = datetime.datetime.strptime(str_dtg, "%Y%m%d%H")

    try:
        sensor = nc_fid.platformCommonName
    except:
        sensor = os.path.basename(nc_fid.filepath()).split('_')[0]

    try:
        wmo_sat_id = nc_fid['MetaData']['satelliteId'][0].item()
    except:
        wmo_sat_id = os.path.basename(nc_fid.filepath()).split('_')[1]

    d['dtg'] = dtg
    d['sensor'] = sensor
    d['wmo_sat_id'] = wmo_sat_id

#   print ( " number of %s points %i " % (name, len(d['ob']) ) )

    # Close original NetCDF file.
    nc_fid.close()

    return d, len(d['ob'])

def print_ncattr(nc_fid, key):
    """
    Prints the NetCDF file attributes for a given key

    Parameters
    ----------
    key : unicode
        a valid netCDF4.Dataset.variables key
    """
    try:
        print ('\tName:', key )
#       print ("\t\tdimensions:", nc_fid.variables[key].dimensions )
#       print ("\t\tsize:", nc_fid.variables[key].size )
#       print ("\t\ttype:", repr(nc_fid.variables[key].dtype) )
    except KeyError:
        print ("\t\tWARNING: %s does not contain variable attributes" % key )


def open_ioda_file( filename ):
    nc_fid = Dataset(filename, 'r')  # Dataset is the class behavior to open the file

    #nc_attrs = nc_fid.ncattrs()
    #nc_dims = [dim for dim in nc_fid.dimensions]  # list of nc dimensions
    #nc_vars = [var for var in nc_fid.variables]  # list of nc variables

    return nc_fid # , nc_attrs, nc_dims, nc_vars

 
if __name__ == "__main__":

    from optparse import OptionParser

    usage = 'usage: %prog -i input-file'

    parser = OptionParser(usage)
    parser.add_option('-i', '--input-file', dest='filename',
                      action='store', default=None,
                      help='Location of input file')
    (options, args) = parser.parse_args()


    # check for file
    if not options.filename:
        parser.error("please supply a file to plot with -i option")
    if not os.path.isfile( options.filename ):
        print('')
        parser.error("can not find file: %s" % options.filename)


    main(options.filename)
