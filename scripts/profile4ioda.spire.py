#!/usr/bin/env python3

import argparse
import netCDF4
import numpy
import pandas
import datetime

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt

from plot_global_scatter_map import plot_global


# TODO: remove it from here
def get_satelliteIdentifier():
    mydict = {
          3: {'name': 'MetOp-B'          , 'satid': 'metopb'   , 'gnssgroup': 'GRAS'},
          4: {'name': 'MetOp-A'          , 'satid': 'metopa'   , 'gnssgroup': 'GRAS'},
          5: {'name': 'MetOp-C'          , 'satid': 'metopc'   , 'gnssgroup': 'GRAS'},
        265: {'name': 'GeoOptics CICERO' , 'satid': 'cicero'   , 'gnssgroup': 'Commercial'},
        267: {'name': 'PlanetIQ GNOMES'  , 'satid': 'planetiq' , 'gnssgroup': 'Commercial'},
        269: {'name': 'Spire'            , 'satid': 'spire'    , 'gnssgroup': 'Commercial'},
        750: {'name': 'COSMIC-2 E1'      , 'satid': 'cosmic2e1', 'gnssgroup': 'COSMIC-2'},
        751: {'name': 'COSMIC-2 E2'      , 'satid': 'cosmic2e2', 'gnssgroup': 'COSMIC-2'},
        752: {'name': 'COSMIC-2 E3'      , 'satid': 'cosmic2e3', 'gnssgroup': 'COSMIC-2'},
        753: {'name': 'COSMIC-2 E4'      , 'satid': 'cosmic2e4', 'gnssgroup': 'COSMIC-2'},
        754: {'name': 'COSMIC-2 E5'      , 'satid': 'cosmic2e5', 'gnssgroup': 'COSMIC-2'},
        755: {'name': 'COSMIC-2 E6'      , 'satid': 'cosmic2e6', 'gnssgroup': 'COSMIC-2'},
        803: {'name': 'GRACE C'          , 'satid': 'gracec'   , 'gnssgroup': 'Other'},
        804: {'name': 'GRACE D'          , 'satid': 'graced'   , 'gnssgroup': 'Other'},
        825: {'name': 'Kompsat-5'        , 'satid': 'kompsat5' , 'gnssgroup': 'Other'},
         42: {'name': 'TerraSAR-X'       , 'satid': 'terrasarx', 'gnssgroup': 'Other'},
         43: {'name': 'TanDEM-X'         , 'satid': 'tandemx'  , 'gnssgroup': 'Other'},
         44: {'name': 'PAZ'              , 'satid': 'paz'      , 'gnssgroup': 'Other'},
    }
    return mydict


# TODO: remove it from here
def get_labels_vcoord():
    mydict = {
        'air_pressure' : 'Air Pressure (hPa)',
        'impact_height': 'Impact Height (km)',
        'channels'     : 'Channels (index)',
    }
    return mydict


# TODO: remove it from here
def get_labels_var():
    mydict = {
        'air_temperature'       : 'Air Temperature (K)',
        'eastward_wind'         : 'Zonal Wind (m s$^{-1}$)',
        'northward_wind'        : 'Meridional Wind (m s$^{-1}$)',
        'specific_humidity'     : 'Specific Humidity (g kg$^{-1}$)',
        'surface_pressure'      : 'Surface Pressure (Pa))',
        'brightness_temperature': 'Brightness Temperature (K)',
        'bending_angle'         : 'Bending Angle (%)',
    }
    return mydict


def get_plot_data(data, lat, lon, log=False):
            if log:
                locs = data > 0
                data = numpy.log10(data[locs])
            else:
                # locs = ~numpy.isnan(data)
                locs = data.notna()
                data = data[locs]
            alat = lat[locs]
            alon = lon[locs]
            return data, alat, alon


parser = argparse.ArgumentParser(description='profiles for ioda',formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-f','--filenames',help='ioda file name[s]',type=str,default=['ioda.nc4'],required=True,nargs='+')
parser.add_argument('--dtg_str',help='date time group string in the YYYYMMDDHH format',metavar='YYYYMMDDHH',required=True)
parser.add_argument('--printALL',help='print whole dataframes',action='store_true',default=False,required=False)
args = parser.parse_args()
fnames = args.filenames
dtg = datetime.datetime.strptime(args.dtg_str, '%Y%m%d%H')
printALL = args.printALL


if printALL:
    # printing whole dataframes
    max_rows = None
    max_cols = None
    pandas.set_option("display.max_rows", max_rows, "display.max_columns", max_cols)

print()
print('List of files to process:')
print()
for fname in fnames:
    print(' o %s' % (fname))
print()

list_of_dataframes = []

# loop over input files
for fname in fnames:

    print('processing ... %s' % (fname))

    # open dataset
    input_dataset = netCDF4.Dataset(fname)

    # skip file if no observations
    nlocs = input_dataset['nlocs'][:].count()
    if nlocs == 0: continue

    # get a list of simulated variables
    if 'hofx' in input_dataset.groups.keys():
        simulated_variables = input_dataset['hofx'].variables.keys()
    else:
        simulated_variables = input_dataset['ObsValue'].variables.keys()

    for simulated_variable in simulated_variables:

        # radiances case...
        if 'nchans' in input_dataset.variables.keys():

            chans = input_dataset['nchans'][:]
            vertical_coordinate = 'channels'
            vertical_index = 'channel_number'
            normalize_omb = False

            for n,chan in enumerate(chans):
                variables = {}
                variables['variable'] = simulated_variable
                variables['latitude'] = input_dataset['MetaData']['latitude'][:]
                variables['longitude'] = input_dataset['MetaData']['longitude'][:]
                variables[vertical_index] = chan
                variables['channel_index'] = n
                for k in ['hofx', 'ObsValue', 'EffectiveQC']:
                    if k in input_dataset.groups.keys():
                        variables[k] = input_dataset[k][simulated_variable][:,n]

                df = pandas.DataFrame(variables)

                list_of_dataframes.append(df)

        # radio occultation case...
        elif 'impact_height' in input_dataset['MetaData'].variables.keys():

            vertical_coordinate = 'impact_height'
            vertical_index = 'layer'
            normalize_omb = True

            variables = {}
            variables[vertical_coordinate] = input_dataset['MetaData'][vertical_coordinate][:]
            variables['variable'] = simulated_variable
            for k in ['hofx', 'ObsValue', 'EffectiveQC']:
                if k in input_dataset.groups.keys():
                    variables[k] = input_dataset[k][simulated_variable][:]
            variables['occulting_sat_id'] = input_dataset['MetaData']['occulting_sat_id'][:]
            variables['latitude'] = input_dataset['MetaData']['latitude'][:]
            variables['longitude'] = input_dataset['MetaData']['longitude'][:]

            df = pandas.DataFrame(variables)

            levels = range(0,80000+1,1000) # assuming 80000 m for the highest layer
            for lindx, level in enumerate(levels):
                if lindx == 0: # bottom case
                    l1 = 0.0
                    l2 = 0.5 * ( level + levels[lindx+1] )
                elif lindx == len(levels)-1: # top case
                    l1 = 0.5 * ( level + levels[lindx-1] )
                    l2 = levels[lindx]
                else: # middle case
                    l1 = 0.5 * ( level + levels[lindx-1] )
                    l2 = 0.5 * ( level + levels[lindx+1] )
                df.loc[(df[vertical_coordinate] >= l1) & (df[vertical_coordinate] < l2), vertical_index] = level/1000 # classify in m, but scale to km

            list_of_dataframes.append(df)

        # aircrafts case...
        elif 'height' in input_dataset['MetaData'].variables.keys():

            vertical_coordinate = 'height'
            vertical_index = 'layer'
            normalize_omb = False

            variables = {}
            variables['latitude'] = input_dataset['MetaData']['latitude'][:]
            variables['longitude'] = input_dataset['MetaData']['longitude'][:]
            variables[vertical_coordinate] = input_dataset['MetaData'][vertical_coordinate][:]
            variables['variable'] = simulated_variable
            for k in ['hofx', 'ObsValue', 'EffectiveQC']:
                if k in input_dataset.groups.keys():
                    variables[k] = input_dataset[k][simulated_variable][:]

            df = pandas.DataFrame(variables)

            levels = range(0,80000+1,1000) # assuming 80000 m for the highest layer
            for lindx, level in enumerate(levels):
                if lindx == 0: # bottom case
                    l1 = 0.0
                    l2 = 0.5 * ( level + levels[lindx+1] )
                elif lindx == len(levels)-1: # top case
                    l1 = 0.5 * ( level + levels[lindx-1] )
                    l2 = levels[lindx]
                else: # middle case
                    l1 = 0.5 * ( level + levels[lindx-1] )
                    l2 = 0.5 * ( level + levels[lindx+1] )
                df.loc[(df[vertical_coordinate] >= l1) & (df[vertical_coordinate] < l2), vertical_index] = level/1000 # classify in m, but scale to km

            list_of_dataframes.append(df)

        # sondes case...
        elif 'air_pressure' in input_dataset['MetaData'].variables.keys():

            vertical_coordinate = 'air_pressure'
            vertical_index = 'layer'
            normalize_omb = False

            variables = {}
            variables['latitude'] = input_dataset['MetaData']['latitude'][:]
            variables['longitude'] = input_dataset['MetaData']['longitude'][:]
            variables[vertical_coordinate] = input_dataset['MetaData'][vertical_coordinate][:]
            variables['variable'] = simulated_variable
            for k in ['hofx', 'ObsValue', 'EffectiveQC']:
                if k in input_dataset.groups.keys():
                    variables[k] = input_dataset[k][simulated_variable][:]

            df = pandas.DataFrame(variables)

            levels = [100000, 85000, 70000, 50000, 40000, 30000, 25000, 20000, 15000, 10000, 7000, 5000, 3000, 2000, 1000]
           #levels = [100000, 85000, 70000, 50000, 30000, 20000, 10000]

            for lindx, level in enumerate(levels):
                if lindx == 0: # bottom case
                    l1 = 200000.0
                    l2 = numpy.exp(0.5 * (numpy.log(level) + numpy.log(levels[lindx+1])))
                elif lindx == len(levels)-1: # top case
                    l1 = numpy.exp(0.5 * (numpy.log(level) + numpy.log(levels[lindx-1])))
                    l2 = 0.0
                else: # middle case
                    l1 = numpy.exp(0.5 * (numpy.log(level) + numpy.log(levels[lindx-1])))
                    l2 = numpy.exp(0.5 * (numpy.log(level) + numpy.log(levels[lindx+1])))
                df.loc[(df[vertical_coordinate] <= l1) & (df[vertical_coordinate] > l2), vertical_index] = level/100 # classify in Pa, but scale to hPa

           ## layers defined as +/- 10 hPa around levels
           #for lindx, level in enumerate(levels):
           #    df.loc[(df[vertical_coordinate] <= level+1000) & (df[vertical_coordinate] >= level-1000), vertical_index] = level/100 # classify in Pa, but scale to hPa

           #p_thresh = 0.015
           #for lindx, level in enumerate(levels):
           #    df.loc[(df[vertical_coordinate] > level*(1-p_thresh)) & (df[vertical_coordinate] < level*(1+p_thresh)), vertical_index] = level/100 # classify in Pa, but scale to hPa

            list_of_dataframes.append(df)

        else:
            raise NotImplementedError('option not available yet')

    input_dataset.close()

DF = pandas.concat(list_of_dataframes)

# set good obs as 1 to count later
DF['obs'] = 0
indx = DF['ObsValue'].isna()
DF['obs'].iloc[~indx] = 1

# hofx dependent diags
if 'hofx' in DF.columns:
    if normalize_omb:
        DF['jedi_omb'] = (DF['ObsValue'] - DF['hofx']) / DF['hofx'] * 100.0
    else:
        DF['jedi_omb'] = DF['ObsValue'] - DF['hofx']

if 'EffectiveQC' in DF.columns:
    # set good h(x) as 1 to count later
    DF['jedi_good'] = 0
    indx = DF['EffectiveQC'] == 0
    DF['jedi_good'].iloc[indx] = 1

if 'impact_height' in DF.columns:
    index_group = ['variable', 'occulting_sat_id', vertical_index]
else:
    index_group = ['variable', vertical_index]

# temporary addition to get summary of obs...
table_obs = DF.groupby(index_group).agg({'ObsValue':['min','max','mean','std','count']})
table = table_obs.copy()
table_sum = table.sum().values
#table_abssum = table.abs().sum().values
table.loc['sum', :] = table_sum
#table.loc['absolute sum', :] = table_abssum
with open('summary_obs.txt','w') as outfile:
    table.to_string(outfile)
table_obs = table_obs.reset_index()

# temporary addition to get plots...
table_all = DF.groupby(index_group).agg({'jedi_omb':['mean','std'], 'obs':'sum'})

table = table_all.copy()
table_sum = table.sum().values
#table_abssum = table.abs().sum().values
table.loc['sum', :] = table_sum
#table.loc['absolute sum', :] = table_abssum
with open('summary_obs_good.txt','w') as outfile:
    table.to_string(outfile)
table_all = table_all.reset_index()

indx = DF['jedi_good'] == 1
table_good = DF[indx].groupby(index_group).agg({'jedi_omb':['mean','std'], 'jedi_good':'sum'})
table_good = table_good.reset_index()

satelliteIdentifier = get_satelliteIdentifier()
labels_var = get_labels_var()
labels_vcoord = get_labels_vcoord()

# vertical profile plot
# ---------------------

if 'occulting_sat_id' in table_all.columns:

    variables = table_all['variable'].unique()
    groups = list(set( satelliteIdentifier[key]['gnssgroup'] for key in satelliteIdentifier.keys() ))
    sats = table_all['occulting_sat_id'].unique()
    colors = [ plt.cm.jet(x) for x in numpy.linspace(0,1,len(sats)) ]

    for var in variables:

        for group in groups:

            fig = plt.figure(figsize=(8,8))
            gs = gridspec.GridSpec(2,1,height_ratios=[95,5],hspace=0)
            ax = plt.subplot(gs[0])
            axup = ax.twiny()

            for s, sat in enumerate(sats):

                # skip satellite if not in group
                if satelliteIdentifier[sat]['gnssgroup'] != group: continue

                indx_good = (table_good['variable'] == var) & (table_good['occulting_sat_id'] == sat)
                if sum(indx_good) == 0: continue

                label = f"{satelliteIdentifier[sat]['name']} ({table_good[indx_good]['jedi_good']['sum'].sum()})"

                ax.plot(table_good[indx_good]['jedi_omb']['std'],
                        table_good[indx_good][vertical_index],
                        '--',  color=colors[s], linewidth=2.5, alpha=1.00, label=label)

                ax.plot(table_good[indx_good]['jedi_omb']['mean'],
                        table_good[indx_good][vertical_index],
                        '-', color=colors[s], linewidth=2.5, alpha=1.00, label='_no_legend')

                axup.plot(table_good[indx_good]['jedi_good']['sum'],
                          table_good[indx_good][vertical_index],
                          ':', color=colors[s], linewidth=1.5, alpha=1.00, label='_no_legend')

            # Dummy plot to get legend handles for line type
            # the following  needs to be in sync with what has been plotted above
            axdummy = ax.twinx()
            axdummy.plot(numpy.NaN, numpy.NaN,
                         '--',  color='k', linewidth=2.5, alpha=1.00, label='Std. Dev. OmB')
            axdummy.plot(numpy.NaN, numpy.NaN,
                         '-', color='k', linewidth=2.5, alpha=1.00, label='Mean OmB')
            axdummy.plot(numpy.NaN, numpy.NaN,
                         ':', color='k', linewidth=1.5, alpha=1.00, label='Obs. Count')
            axdummy.get_yaxis().set_visible(False)

            # Create legend for the line types
            h1, l1 = axdummy.get_legend_handles_labels()
            legend2 = axdummy.legend(h1, l1, labelspacing=1.2, handlelength=2.5,
                 ncol=1, loc=2, mode="expand", borderaxespad=0.0, frameon=False, numpoints=1)

           # Create legend for the line colors
            h1, l1 = ax.get_legend_handles_labels()
            h2, l2 = axup.get_legend_handles_labels()
            legend1 = ax.legend(h1+h2, l1+l2, labelspacing=1.2, handlelength=2.5,
                 bbox_to_anchor=(0., -0.20, 1.0, .102), ncol=3, mode="expand",
                 borderaxespad=0.0, frameon=False, numpoints=1)
            for line in legend1.get_lines():
                line.set_linewidth(10.0)

            # Set defaults
            axup.set_xlim([0,table_good[:]['jedi_good']['sum'].max()]) # axup.get_xlim()[1]])
            ax.set_xlim([-10.0, 10.0])
            ax.set_ylim([0,60]) # ax.get_ylim()[1]])

            # Add vertical reference line
            ax.axvline(0.0,linestyle='-',linewidth=1.0,color='k',zorder=0)

            # Add labels
            ax.set_ylabel(labels_vcoord[vertical_coordinate])
            ax.set_xlabel(labels_var[var])
            axup.set_xlabel('Obs. Count (units)')

             # Add title
            title = f"{group} platforms"
            plt.suptitle(title, fontsize='large', weight='demibold')

            ofname = f"gnssro.{group.lower()}.{var}.profile.{dtg.strftime('%Y%m%d%H')}.png"
            fig.savefig(ofname, format='png')
            plt.close(fig)


# spatial map plot
# ----------------

indx = DF['jedi_good'] == 1
df = DF.loc[indx][['variable','occulting_sat_id','latitude','longitude','ObsValue','hofx','jedi_omb']]

if 'occulting_sat_id' in df.columns:

    variables = df['variable'].unique()
    groups = list(set( satelliteIdentifier[key]['gnssgroup'] for key in satelliteIdentifier.keys() ))
    sats = df['occulting_sat_id'].unique()

    for var in variables:

        for group in groups:

            indx_group = (df['variable'] == '') & (df['occulting_sat_id'] == '')

            for s, sat in enumerate(sats):

                # skip satellite if not in group
                if satelliteIdentifier[sat]['gnssgroup'] != group: continue

                indx_group = indx_group | ((df['variable'] == var) & (df['occulting_sat_id'] == sat))
            if sum(indx_group) == 0: continue

            win_beg = dtg - datetime.timedelta(hours=6)

            # full geolocation set
            lat = df.loc[indx_group]['latitude']
            lon = df.loc[indx_group]['longitude']


            data, alat, alon = get_plot_data(df.loc[indx_group]['ObsValue'], lat, lon, log=True)
            xtitle = f"{group} platforms Bending Angle {win_beg.strftime('%Y%m%dT%HZ_PT48H')}"
            plot_global(data = data, lat  = alat, lon = alon,
                        title = xtitle, 
                        image_name=f"gnssro.{group.lower()}.{var}.ob.{dtg.strftime('%Y%m%d%H')}", 
                        units='log(radians)', dot_size=2.5)

            data, alat, alon = get_plot_data(df.loc[indx_group]['hofx'], lat, lon, log=True)
            xtitle = f"{group} platforms H(x) {win_beg.strftime('%Y%m%dT%HZ_PT48H')}"
            plot_global(data = data, lat  = alat, lon = alon,
                        title = xtitle,
                        image_name=f"gnssro.{group.lower()}.{var}.hofx.{dtg.strftime('%Y%m%d%H')}", 
                        units='log(radians)', dot_size=2.5)

            data, alat, alon = get_plot_data(df.loc[indx_group]['jedi_omb'], lat, lon)
            xtitle = f"{group} platforms Observation - H(x) {win_beg.strftime('%Y%m%dT%HZ_PT48H')}"
            plot_global(data = data, lat  = alat, lon = alon,
                        title = xtitle,
                        image_name=f"gnssro.{group.lower()}.{var}.omb.{dtg.strftime('%Y%m%d%H')}", 
                        units='%', dot_size=2.5)

