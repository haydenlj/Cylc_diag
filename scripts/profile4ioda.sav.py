#!/usr/bin/env python3

import argparse
import netCDF4
import numpy
import pandas
import matplotlib.pyplot as plt


# TODO: remove it from here
def get_satelliteIdentifier():
    mydict = {
          4: {'name': 'MetOp-A'          , 'satid': 'metopa'   },
          3: {'name': 'MetOp-B'          , 'satid': 'metopb'   },
          5: {'name': 'MetOp-C'          , 'satid': 'metopc'   },
        267: {'name': 'PlanetIQ GNOMES-2', 'satid': 'planetiq' },
        750: {'name': 'COSMIC-2 E1'      , 'satid': 'cosmic2e1'},
        751: {'name': 'COSMIC-2 E2'      , 'satid': 'cosmic2e2'},
        752: {'name': 'COSMIC-2 E3'      , 'satid': 'cosmic2e3'},
        753: {'name': 'COSMIC-2 E4'      , 'satid': 'cosmic2e4'},
        754: {'name': 'COSMIC-2 E5'      , 'satid': 'cosmic2e5'},
        755: {'name': 'COSMIC-2 E6'      , 'satid': 'cosmic2e6'},
        803: {'name': 'GRACE C'          , 'satid': 'gracec'   },
        804: {'name': 'GRACE D'          , 'satid': 'graced'   },
        825: {'name': 'Kompsat-5'        , 'satid': 'kompsat5' },
         42: {'name': 'TerraSAR-X'       , 'satid': 'terrasarx'},
         43: {'name': 'TanDEM-X'         , 'satid': 'tandemx'  },
         44: {'name': 'PAZ'              , 'satid': 'paz'      },
    }

    return mydict


parser = argparse.ArgumentParser(description='profiles for ioda',formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-f','--filenames',help='ioda file name[s]',type=str,default=['ioda.nc4'],required=True,nargs='+')
parser.add_argument('--dtg_str',help='date time group string in the YYYYMMDDHH format',default='',required=False)
parser.add_argument('--printALL',help='print whole dataframes',action='store_true',default=False,required=False)
args = parser.parse_args()
fnames = args.filenames
dtg_str = args.dtg_str
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
    simulated_variables = input_dataset['hofx'].variables.keys()

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
                variables['channel_index'] = n
                variables[vertical_index] = chan
                variables['hofx'] = input_dataset['hofx'][simulated_variable][:,n]
                variables['ObsValue'] = input_dataset['ObsValue'][simulated_variable][:,n]
                variables['EffectiveQC'] = input_dataset['EffectiveQC'][simulated_variable][:,n]

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
            variables['hofx'] = input_dataset['hofx'][simulated_variable][:]
            variables['ObsValue'] = input_dataset['ObsValue'][simulated_variable][:]
            variables['EffectiveQC'] = input_dataset['EffectiveQC'][simulated_variable][:]
            variables['occulting_sat_id'] = input_dataset['MetaData']['occulting_sat_id'][:]

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
            variables[vertical_coordinate] = input_dataset['MetaData'][vertical_coordinate][:]
            variables['variable'] = simulated_variable
            variables['hofx'] = input_dataset['hofx'][simulated_variable][:]
            variables['ObsValue'] = input_dataset['ObsValue'][simulated_variable][:]
            variables['EffectiveQC'] = input_dataset['EffectiveQC'][simulated_variable][:]

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
            variables[vertical_coordinate] = input_dataset['MetaData'][vertical_coordinate][:]
            variables['variable'] = simulated_variable
            variables['hofx'] = input_dataset['hofx'][simulated_variable][:]
            variables['ObsValue'] = input_dataset['ObsValue'][simulated_variable][:]
            variables['EffectiveQC'] = input_dataset['EffectiveQC'][simulated_variable][:]

            df = pandas.DataFrame(variables)

            levels = [100000, 85000, 70000, 50000, 40000, 30000, 25000, 20000, 15000, 10000, 7000, 5000, 3000, 2000, 1000]

            for lindx, level in enumerate(levels):
                if lindx == 0:
                    l1 = 200000.0
                    l2 = numpy.exp(0.5 * (numpy.log(level) + numpy.log(levels[lindx+1])))
                elif lindx == len(levels)-1:
                    l1 = numpy.exp(0.5 * (numpy.log(level) + numpy.log(levels[lindx-1])))
                    l2 = 0.0
                else:
                    l1 = numpy.exp(0.5 * (numpy.log(level) + numpy.log(levels[lindx-1])))
                    l2 = numpy.exp(0.5 * (numpy.log(level) + numpy.log(levels[lindx+1])))
                df.loc[(df[vertical_coordinate] <= l1) & (df[vertical_coordinate] > l2), vertical_index] = level/100 # classify in Pa, but scale to hPa

            list_of_dataframes.append(df)

        else:
            raise NotImplementedError('option not available yet')

DF = pandas.concat(list_of_dataframes)
print(DF)

if normalize_omb:
    DF['jedi_omb'] = (DF['ObsValue'] - DF['hofx']) / DF['hofx'] * 100.0
else:
    DF['jedi_omb'] = DF['ObsValue'] - DF['hofx']

# set good obs as 1 to count later
DF['jedi_good'] = 0
indx = DF['EffectiveQC'] == 0
DF['jedi_good'].iloc[indx] = 1

# set good obs as 1 to count later
DF['obs'] = 0
indx = DF['ObsValue'].isna()
DF['obs'].iloc[~indx] = 1


if 'impact_height' in input_dataset['MetaData'].variables.keys():
    group = ['variable', 'occulting_sat_id', vertical_index]
else:
    group = ['variable', vertical_index]

# temporary addition to get plots...
table_all = DF.groupby(group).agg({'jedi_omb':['mean','std'], 'obs':'sum'})
table_all = table_all.reset_index()
#table_all = table_all.set_index(vertical_index)
print(table_all)

indx = DF['jedi_good'] == 1
table_good = DF[indx].groupby(group).agg({'jedi_omb':['mean','std'], 'jedi_good':'sum'})
table_good = table_good.reset_index()
#table_good = table_good.set_index(vertical_index)
print(table_good)

# TODO: remove it from here
labels_vcoord_dict = {}
labels_vcoord_dict['air_pressure'] = 'Air Pressure (hPa)'
labels_vcoord_dict['impact_height'] = 'Impact Height (km)'
labels_vcoord_dict['channels'] = 'Channels (index)'

# TODO: remove it from here
labels_var_dict = {}
labels_var_dict['air_temperature'] = 'Air Temperature (K)'
labels_var_dict['eastward_wind'] = 'Zonal Wind (m s$^{-1}$)'
labels_var_dict['northward_wind'] = 'Meridional Wind (m s$^{-1}$)'
labels_var_dict['specific_humidity'] = 'Specific Humidity (g kg$^{-1}$)'
labels_var_dict['surface_pressure'] = 'Surface Pressure (Pa))'
labels_var_dict['brightness_temperature'] = 'Brightness Temperature (K)'
labels_var_dict['bending_angle'] = 'Bending Angle (%)'

satelliteIdentifier = get_satelliteIdentifier()

for var in table_all['variable'].unique():
    for sat in table_all['occulting_sat_id'].unique():

        indx_all  = (table_all['variable'] == var) & (table_all['occulting_sat_id'] == sat)
        indx_good = (table_good['variable'] == var) & (table_good['occulting_sat_id'] == sat)

        fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(8,4.5), sharex=False, sharey=True, constrained_layout=False)

        axes[0].plot(table_all[indx_all]['jedi_omb']['std'],  table_all[indx_all]['layer'], '-', color='k', label='_no_legend_', linewidth=2.0, alpha=0.75)
        axes[0].plot(table_all[indx_all]['jedi_omb']['mean'], table_all[indx_all]['layer'], '--', color='k', label='_no_legend_', linewidth=2.0, alpha=0.75)

        axes[1].plot(table_good[indx_good]['jedi_omb']['std'],  table_good[indx_good]['layer'], '-', color='k', label='Std. Dev. OmB', linewidth=2.0, alpha=0.75)
        axes[1].plot(table_good[indx_good]['jedi_omb']['mean'], table_good[indx_good]['layer'], '--', color='k', label='Mean OmB', linewidth=2.0, alpha=0.75)

        if vertical_coordinate == 'air_pressure':
            axes[0].set_ylim([max(table_all[indx_all]['layer']), min(table_all[indx_all]['layer'])])
            axes[0].set_yscale('log')

        ax0up = axes[0].twiny()
        ax0up.plot(table_all[indx_all]['obs']['sum'], table_all[indx_all]['layer'], ':', color='k', label='Obs. Count', linewidth=1.0, alpha=0.75)
        ax0up.set_xlim([0,ax0up.get_xlim()[1]])

        ax1up = axes[1].twiny()
        ax1up.plot(table_good[indx_good]['jedi_good']['sum'], table_good[indx_good]['layer'], ':', color='k', label='Obs. Count', linewidth=1.0, alpha=0.75)
        ax1up.set_xlim(ax0up.get_xlim())

        axes[0].axvline(0.0,linestyle='-',linewidth=1.0,color='k',zorder=0)
        axes[1].axvline(0.0,linestyle='-',linewidth=1.0,color='k',zorder=0)

        axes[0].set_ylabel(labels_vcoord_dict[vertical_coordinate])
        axes[0].set_xlabel(labels_var_dict[var])
        axes[1].set_xlabel(labels_var_dict[var])
        ax0up.set_xlabel('Obs. Count (units)')
        ax1up.set_xlabel('Obs. Count (units)')

        axes[0].text(0, 1.15, r'(a) All Obs.', transform=axes[0].transAxes, weight='demi')
        axes[1].text(0, 1.15, r'(b) Obs. passing QC', transform=axes[1].transAxes, weight='demi')

        h1, l1 = axes[1].get_legend_handles_labels()
        h2, l2 = ax1up.get_legend_handles_labels()
        axes[1].legend(h1+h2, l1+l2, frameon=False, loc=0, ncol=1, columnspacing=1, handlelength=3, numpoints=1).get_frame().set_alpha(0.7)

        title = satelliteIdentifier[sat]['name']
        plt.suptitle(title,fontsize='large')

        plt.tight_layout()
        sat_string = satelliteIdentifier[sat]['satid']

        if dtg_str:
            ofname = f'gnssro.{sat_string}.{var}.omb.{dtg_str}.png'
        else:
            ofname = f'gnssro.{sat_string}.{var}.omb.png'
        plt.savefig(ofname, dpi=300, orientation='landscape', format='png')
        plt.close(fig)

