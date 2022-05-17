#!/usr/bin/python

"""
Python code to plot radiosonde profiles

Usage:
see usage clause at bottom of routine

"""

# import pdb
# from IPython import embed as shell

import glob
import os.path
import sys
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.colors
import matplotlib.pyplot as plt

import numpy as np

from define_radiosonde import      raob_type, raob_station,                   \
                                   flatten,                                   \
                                   lx, ly, mandatory_levels,                  \
                                   known_raobs, raob_types, sorted_raob_keys, \
                                   var_coding, var_types, sorted_var_keys,    \
                                   sub_domains
from read_ioda_netcdf       import read_ioda_raob

#  globals -- globals everywhere
REAL_SIZE = 8
REAL_TYPE = 'float%d' % (8*REAL_SIZE)
MISSING = float(-999.99)


def main(filepath, cdtg, ndays, output_dir, image_dir):

    d, sorted_dic_keys = initialize_raob_dict( ly, lx, raob_types, var_types, REAL_TYPE)

    dtg_indx, cdtg_indx = time_window(ndays, cdtg)
    d['dtg_cnt'] = np.zeros((len(dtg_indx)),dtype=REAL_TYPE)
    dx = -1

    for dtg in cdtg_indx:
        data_count = 0
        dx += 1

        # initialize local - individual dtg mean & stdv
        local, _  = initialize_raob_dict( ly, lx, raob_types, var_types, REAL_TYPE)


        # NRL 
        # zfiles = glob.glob( os.path.join(filepath, dtg, 'da', 'obs', 'raob_all_out_*.nc4' ) )

        # z-suite
        zfiles = glob.glob( os.path.join(filepath, dtg, 'da', 'output', 'hofx', 'radiosonde_*.nc4' ) )

        # JCSDA demo
        # print ( os.path.join(filepath, dtg, 'Data', '*radiosonde_????.nc4' ) )
        # zfiles = glob.glob( os.path.join(filepath, dtg, 'Data', '*radiosonde_????.nc4' ) )
        data = {}
        for afile in zfiles:
            print ( "reading file: %s" % afile )
            # append data
            data = read_ioda_raob(afile, data)
        
        if not data: continue

        
        # print ( "len air_pressure: ", len(data['air_pressure']) )
        for i, pressure in enumerate(data['air_pressure']):
            # shell()
            # sys.exit()
            if pressure == 0.:
                print ( "unphysical pressure: ", i, pressure )
                continue
            data_count += 1
        
            # find vertical bin
            yidx = get_vertical_index( pressure/100., ly )
            if yidx < 0: continue
            xidx = get_latitude_index( data['latitude'][i], lx )

            # WMO has BUFR values > 100; AR does not support this
            raob_wmo_index = 79


            # define raob_index which is the raob 'groupings' not individual WMO index
            for raob_index, k in enumerate(sorted_raob_keys):
                v = flatten(list(raob_type[k].values()))
                # is this raob WMO index in v=list of raob grouping WMO indicies
                if raob_wmo_index in v:
                    break


            # now map ioda var names to names in define_radiosonde
            ioda_var_name = { 't': 'air_temperature',   \
                              'q': 'specific_humidity', \
                              'u': 'eastward_wind',     \
                              'v': 'northward_wind' }
                              # 'q': 'mixing_ratio',    \
        
            for k in ioda_var_name.keys():
                try:
                   var_index = sorted_var_keys.index(k)
                except ValueError:
                   print('Key {} not found in sorted_var_keys'.format(k))
                   continue
                fgname = ioda_var_name[k] + '_fg_depar'
                if fgname in data.keys():
                   xiv = data[fgname][i]
                   anname = ioda_var_name[k] + '_an_depar'
                   if anname in data.keys():
                      an_depar = data[anname][i]
                   else:
                      continue
                else:
                   continue
                # Sign convention is flipped between  NAVGEM (innov = y-Hxb) and JEDI (depbg = Hxb-y)
                # this is computed on the fly
                # xiv = -xiv
                # an_depar = -an_depar
                location_3d = ( yidx, raob_index, var_index )
                location_4d = ( yidx, xidx, raob_index, var_index )
                if xiv > 99999 or xiv < -99999: continue
                # if 't' in k:
                    # print ( "%s:  %f" % (ioda_var_name[k], xiv) )

                # https://en.wikipedia.org/wiki/Standard_deviation#Rapid_calculation_methods
                local['cnt'][location_3d]  +=  1.0
                local['zonal_cnt'][location_4d]  += 1.0

                mean_inc = (xiv - local['fg_depar'][location_3d]) / local['cnt'][location_3d]
                local['fg_depar'][location_3d] += mean_inc
                local['stdv_fg_depar'][location_3d] += (xiv - local['fg_depar'][location_3d]) * (xiv - local['fg_depar'][location_3d] + mean_inc)

                mean_inc = (xiv - local['zonal_fg_depar'][location_4d]) / local['zonal_cnt'][location_4d]
                local['zonal_fg_depar'][location_4d] += mean_inc
                local['zonal_stdv_fg_depar'][location_4d] += (xiv - local['zonal_fg_depar'][location_4d]) * (xiv - local['zonal_fg_depar'][location_4d] + mean_inc)

                mean_inc = (an_depar - local['an_depar'][location_3d]) / local['cnt'][location_3d]
                local['an_depar'][location_3d] += mean_inc
                local['stdv_an_depar'][location_3d] += (an_depar - local['an_depar'][location_3d]) * (an_depar - local['an_depar'][location_3d] + mean_inc)

                mean_inc = (an_depar - local['zonal_an_depar'][location_4d]) / local['zonal_cnt'][location_4d]
                local['zonal_an_depar'][location_4d] += mean_inc
                local['zonal_stdv_an_depar'][location_4d] += (an_depar - local['zonal_an_depar'][location_4d]) * (an_depar - local['zonal_an_depar'][location_4d] + mean_inc)

            # shell()
            # sys.exit()

        print('found ',  data_count, '  raob obs ')
            
        # compute the individual dtg fg_depars and standard deviations
        # https://en.wikipedia.org/wiki/Standard_deviation#Rapid_calculation_methods
        print('now computing the fg_depar and standard deviation')

        local = compute_mean_stdv_statistics(local)

        #   we now have data for a dtg (either read or wrote)
        # ===   use individual dtg mean/stdv to compute  ======
        # ===    a mean/stdv for the entire time series  ======

        # count overall for this date time group
        d['dtg_cnt'][dx] = local['cnt'].sum()

        # weight fg_depar from date time group by its count
        d['cnt']            +=  local['cnt']
        d['zonal_cnt']      +=  local['zonal_cnt']

        mean_inc = (local['fg_depar'] - d['fg_depar']) / d['cnt']
        d['fg_depar']       +=  mean_inc
        d['stdv_fg_depar']  +=  (local['fg_depar'] - d['fg_depar']) * (local['fg_depar'] - d['fg_depar'] + mean_inc)

        mean_inc = (local['an_depar'] - d['an_depar']) / d['cnt']
        d['an_depar']       +=  mean_inc
        d['stdv_an_depar']  +=  (local['an_depar'] - d['an_depar']) * (local['an_depar'] - d['an_depar'] + mean_inc)

        mean_inc = (local['zonal_fg_depar'] - d['zonal_fg_depar']) / d['zonal_cnt']
        d['zonal_fg_depar'] += mean_inc
        d['zonal_stdv_fg_depar']  +=  (local['zonal_fg_depar'] - d['zonal_fg_depar']) * (local['zonal_fg_depar'] - d['zonal_fg_depar'] + mean_inc)

        mean_inc = (local['zonal_an_depar'] - d['zonal_an_depar']) / d['zonal_cnt']
        d['zonal_an_depar'] += mean_inc
        d['zonal_stdv_an_depar']  +=  (local['zonal_an_depar'] - d['zonal_an_depar']) * (local['zonal_an_depar'] - d['zonal_an_depar'] + mean_inc)

    #####################################################
    #     we have finished looping over time series     #
    #      final computation of series mean/stdv        #
    #####################################################

    d = compute_mean_stdv_statistics(d)

# ===========================================================
# ===   finished computing stats  --> BEGIN plotting    =====
# ===========================================================

    print('  ')
    print('  ')
    if len(raob_type['other (Unknown)']['unknown']) > 0:
        print('   ##### unknown raobs found WMO index :  ', raob_type['other (Unknown)']['unknown'])
        print('  ')
        print('  ')
    print("Plotting...")        


    for var in sorted_var_keys:

        str_field = var_coding[var]['name'] 
        str_index = var_coding[var]['index'] 
        str_units = var_coding[var]['unit']

        # height observations are for surface stations only -- skip for now
        if var == 'Z':
            continue

        # JEDI separates radiosonde from profilers
        # for include in ['normal', 'other', 'profiler']:
        for include in ['normal']:

            tot_global = 0
            rnd = float(0)
            # compute zonal fg_depar for groups of raob classifications
            # and determine if valid data exists
            count = np.zeros( (ly['num'], lx['num']), dtype=REAL_TYPE )
            fg_depar = np.zeros( (ly['num'], lx['num']), dtype=REAL_TYPE )
            an_depar = np.zeros( (ly['num'], lx['num']), dtype=REAL_TYPE )
            stdv_fg_depar = np.zeros( (ly['num'], lx['num']), dtype=REAL_TYPE )
            stdv_an_depar = np.zeros( (ly['num'], lx['num']), dtype=REAL_TYPE )

            regional = { 'count': {},
                         'fg_depar' : {},
                         'an_depar' : {},
                    'stdv_fg_depar' :  {}, 
                    'stdv_an_depar' :  {} }
            for key in regional:
                for domain in sub_domains:
                    regional[key][domain] = np.zeros( ly['num'], dtype=REAL_TYPE )
                

            glb_count = np.zeros( ly['num'], dtype=REAL_TYPE )
            glb_fg_depar = np.zeros( ly['num'], dtype=REAL_TYPE )
            glb_an_depar = np.zeros( ly['num'], dtype=REAL_TYPE )
            glb_stdv_fg_depar = np.zeros( ly['num'], dtype=REAL_TYPE )
            glb_stdv_an_depar = np.zeros( ly['num'], dtype=REAL_TYPE )
            for l, k in enumerate(sorted_raob_keys):
                if include == 'normal':
                    if 'profiler' in k:
                    #if 'other' in k or 'profiler' in k:
                        continue
                elif include not in k:
                        continue

                if not d['cnt'][ :, l, str_index ].sum():
                    continue  # np.sum will reset tot_global to mask if all values are masked
                tot_global += np.sum( d['cnt'][ :, l, str_index ] )

                tmp_cnt = d['cnt'][ :, l, str_index ]
                tmp_fg_depar = d['fg_depar'][ :, l, str_index ]
                tmp_an_depar = d['an_depar'][ :, l, str_index ]
                good =  tmp_cnt > 0 
                glb_count[good] += tmp_cnt[good]
                glb_fg_depar[good] += tmp_cnt[good] * tmp_fg_depar[good]
                glb_an_depar[good] += tmp_cnt[good] * tmp_an_depar[good]

                tmp_cnt = d['zonal_cnt'][ :, :, l, str_index ]
                tmp_fg_depar = d['zonal_fg_depar'][ :, :, l, str_index ]
                tmp_an_depar = d['zonal_an_depar'][ :, :, l, str_index ]
                good =  tmp_cnt > 0 
                count[good] += tmp_cnt[good]
                fg_depar[good] += tmp_cnt[good] * tmp_fg_depar[good]
                an_depar[good] += tmp_cnt[good] * tmp_an_depar[good]

                for domain in sub_domains:
                    regional['count'][domain] = np.sum(count[:,sub_domains[domain]['lx_index'][0]:sub_domains[domain]['lx_index'][1]], axis=1)
                    regional['fg_depar'][domain] = np.sum(fg_depar[:,sub_domains[domain]['lx_index'][0]:sub_domains[domain]['lx_index'][1]], axis=1)
                    regional['an_depar'][domain] = np.sum(an_depar[:,sub_domains[domain]['lx_index'][0]:sub_domains[domain]['lx_index'][1]], axis=1)


            glb_count = np.ma.masked_less_equal( glb_count, 1 )
            glb_fg_depar = np.ma.array( glb_fg_depar, mask = glb_count.mask, fill_value = MISSING ) / glb_count
            glb_an_depar = np.ma.array( glb_an_depar, mask = glb_count.mask, fill_value = MISSING ) / glb_count

            count = np.ma.masked_less_equal( count, 1 )
            fg_depar = np.ma.array( fg_depar, mask = count.mask, fill_value = MISSING ) / count
            an_depar = np.ma.array( an_depar, mask = count.mask, fill_value = MISSING ) / count

            for domain in sub_domains:
                regional['count'][domain] = np.ma.masked_less_equal( regional['count'][domain], 1 )
                regional['fg_depar'][domain] = np.ma.array( regional['fg_depar'][domain], 
                                                            mask = regional['count'][domain].mask, 
                                                      fill_value = MISSING ) / regional['count'][domain]
                regional['an_depar'][domain] = np.ma.array( regional['fg_depar'][domain], 
                                                            mask = regional['count'][domain].mask, 
                                                      fill_value = MISSING ) / regional['count'][domain]

            # use group zonal fg_depar for raob classifications to compute group stdv
            for l, k in enumerate(sorted_raob_keys):
                if include == 'normal':
                    if 'profile' in k:
                    #if 'other' in k or 'profile' in k:
                        continue
                elif include not in k:
                        continue

                tmp_cnt = d['cnt'][ :, l, str_index ]
                tmp_fg_depar = d['fg_depar'][ :, l, str_index ]
                tmp_an_depar = d['an_depar'][ :, l, str_index ]
                tmp_stdv_fg_depar = d['stdv_fg_depar'][ :, l, str_index ]
                tmp_stdv_an_depar = d['stdv_an_depar'][ :, l, str_index ]
                good =  tmp_cnt > 1 
                glb_stdv_fg_depar[good] += tmp_cnt[good] * ( tmp_stdv_fg_depar[good]**2 + ( glb_fg_depar[good] - tmp_fg_depar[good])**2 )
                glb_stdv_an_depar[good] += tmp_cnt[good] * ( tmp_stdv_an_depar[good]**2 + ( glb_an_depar[good] - tmp_an_depar[good])**2 )

                tmp_cnt = d['zonal_cnt'][ :, :, l, str_index ]
                tmp_fg_depar = d['zonal_fg_depar'][ :, :, l, str_index ]
                tmp_an_depar = d['zonal_an_depar'][ :, :, l, str_index ]
                tmp_stdv_fg_depar = d['zonal_stdv_fg_depar'][ :, :, l, str_index ]
                tmp_stdv_an_depar = d['zonal_stdv_an_depar'][ :, :, l, str_index ]
                good =  tmp_cnt > 1 
                stdv_fg_depar[good] += tmp_cnt[good] * ( tmp_stdv_fg_depar[good]**2 + ( fg_depar[good] - tmp_fg_depar[good])**2 )
                stdv_an_depar[good] += tmp_cnt[good] * ( tmp_stdv_an_depar[good]**2 + ( an_depar[good] - tmp_an_depar[good])**2 )

                for domain in sub_domains:
                    regional['stdv_fg_depar'][domain] = np.sum(stdv_fg_depar[:,sub_domains[domain]['lx_index'][0]:sub_domains[domain]['lx_index'][1]], axis=1)
                    regional['stdv_an_depar'][domain] = np.sum(stdv_an_depar[:,sub_domains[domain]['lx_index'][0]:sub_domains[domain]['lx_index'][1]], axis=1)

            glb_stdv_fg_depar = np.sqrt( np.ma.array( glb_stdv_fg_depar, mask=glb_count.mask, fill_value=MISSING ) / glb_count )
            glb_stdv_an_depar = np.sqrt( np.ma.array( glb_stdv_an_depar, mask=glb_count.mask, fill_value=MISSING ) / glb_count )

            stdv_fg_depar = np.sqrt( np.ma.array( stdv_fg_depar, mask=count.mask, fill_value=MISSING ) / count )
            stdv_an_depar = np.sqrt( np.ma.array( stdv_an_depar, mask=count.mask, fill_value=MISSING ) / count )

            for domain in sub_domains:
                regional['stdv_fg_depar'][domain] = np.sqrt( np.ma.array( regional['stdv_fg_depar'][domain], 
                                                            mask = regional['count'][domain].mask, 
                                                      fill_value = MISSING ) / regional['count'][domain] )
                regional['stdv_an_depar'][domain] = np.sqrt( np.ma.array( regional['stdv_an_depar'][domain], 
                                                            mask = regional['count'][domain].mask, 
                                                      fill_value = MISSING ) / regional['count'][domain] )

            ########################################################
            ###      plot global mean and stdv of innovation     ###
            ########################################################
            for fld in ['bias', 'stdv']:
                if include == 'normal' :
                    ttl = ' '.join( [cdtg, 'raob', str_field, fld, 'global', 'innov', '(', str_units, ')'] )
                    image_name =  '_'.join( [ 'raob', 'global', fld, var, cdtg] )
                else :
                    #continue
                    ttl = ' '.join( [cdtg, 'raob', str_field, fld, 'global', 'innov', '(', str_units, ')'] )
                    image_name =  '_'.join( [ 'raob', 'global', fld, var, include, cdtg] )
                image_name = os.path.join( image_dir, image_name )
 
                if fld == 'bias':
                    glb_fg_data = glb_fg_depar
                    glb_an_data = glb_an_depar
                    zmin = var_coding[var]['min']/5.0
                    zmax = var_coding[var]['max']/5.0
                elif fld == 'stdv':
                    glb_fg_data = glb_stdv_fg_depar
                    glb_an_data = glb_stdv_an_depar
                    zmin = 0.0
                    zmax = var_coding[var]['max']
                else:
                    print('unknown global field to plot')
                    continue

                data_range = { 'min'  :  zmin,
                               'max'  :  zmax,
                              'unit'  :  var_coding[var]['unit']  }

                if tot_global > 0:
                    print('   .... : ', image_name)
                    plot_global_mean_stdv(glb_count, glb_fg_data, glb_an_data, data_range, str_index, ttl, image_name, include)
                else:
                    print('   .... no data for: ', image_name)            

            #########################################################
            ###      plot  mean and stdv of innovation            ###
            #########################################################

            # these are by radiosonde types (vendors) 
            # not being plotted as JEDI convention needs to be checked

#           ttl = ' '.join( [cdtg, 'raob', str_field] )
#           if include == 'normal' :
#               image_name =  '_'.join( [ 'raob', 'mean', var, cdtg] )
#           else:
#               image_name =  '_'.join( [ 'raob', 'mean', var, include, cdtg] )
#           image_name = os.path.join( image_dir, image_name )
#           data_range = { 'min'  :  var_coding[var]['min'], 
#                          'max'  :  var_coding[var]['max'],
#                          'unit'  :  var_coding[var]['unit']  }

#           if tot_global > 0:
#               print('   .... : ', image_name)
#               plot_mean_stdv_raob_type(d, data_range, str_index, ttl, image_name, include)
#           else:
#               print('   .... no data for: ', image_name)


            ########################################################
            ###       plot zonal innovation mean and stdv        ###
            ########################################################
            for fld in ['mean', 'stdv']:
                if include == 'normal' :
                    ttl = ' '.join( ['zonal', fld, 'raob', str_field, 'innov', '(', str_units, ')'] )
                    image_name =  '_'.join( [ 'raob', 'zonal', fld, var, cdtg] )
                else :
                    #continue
                    ttl = ' '.join( ['zonal', fld, 'raob', include, str_field, 'innov', '(', str_units, ')'] )
                    image_name =  '_'.join( [ 'raob', 'zonal', fld, var, include, cdtg] )
                image_name = os.path.join( image_dir, image_name )
 
                if fld == 'mean':
                    data = fg_depar
                    zmin = var_coding[var]['min']
                elif fld == 'stdv':
                    data = stdv_fg_depar
                    zmin = 0.0
                else:
                    print('unknown zonal field to plot')
                    continue

                data_range = { 'min'  :  zmin,
                               'max'  :  var_coding[var]['max'],
                              'unit'  :  var_coding[var]['unit'],
                               'bin'  :  var_coding[var]['bin']   }

                if count.sum() > 0:
                    print('   .... : ', image_name)
                    plot_zonal(data, data_range, ttl, image_name)
                else:
                    print('   .... no data for : ', image_name)


def plot_global_mean_stdv(count, fg_depar, an_depar, data_range, var_indx, ttl, image_name, include):

    # plot the data
    font_base = 12

    fig = plt.figure(figsize=(7.5,7.5))

    # define plotting axis 
    ax = fig.add_subplot(111)

    yrange=np.array( [ 0.0, len(mandatory_levels)-1 ] )

    # make a vertical dotted line along x=0
    plt.plot( [0.0,0.0], yrange,':',linewidth=3.0,color='#b1b1b1')

    colors = ['r','k','b','c','g','#996433','m','#bbe0e3','#ffd700','y']
    fg_lines = {}
    an_lines = {}

    # set the labels for the y-axis (mandatory pressure levels)
    yticks = list(range( ly['num']))
    ylabs = mandatory_levels
    ax.yaxis.set_ticks(yticks)
    ax.yaxis.set_ticklabels( ylabs, fontsize=font_base,
                            fontweight='demibold',color='k')

    line_color = 0
    k = 'Background DEPAR'
    xses_fg = fg_depar[:]
    yses_fg = np.ma.array( yticks, mask=xses_fg.mask )
    fg_lines[1] = plt.plot( xses_fg, yses_fg, '-', linewidth=3.5, 
                             color=colors[line_color%len(colors)], label=k )
    line_color += 1
    k = 'Analysis DEPAR'
    xses_an = an_depar[:]
    if np.min(an_depar) == np.max(an_depar):
        print(' no analysis departure to plot only plotting first-guess departure ')
    else:
        yses_an = np.ma.array( yticks, mask=xses_an.mask )
        an_lines[1] = plt.plot( xses_an, yses_an, '--', linewidth=3.5,
                             color=colors[line_color%len(colors)], label=k )

    ax.legend(loc='best',labelspacing=0.02)

    plt.xlim( data_range['min'], data_range['max'] )
    for line in ax.get_xticklabels():
        line.set_color('k')
        line.set_fontsize(font_base)
        line.set_fontweight('demibold')

    plt.xlabel(data_range['unit'],fontsize=font_base,fontweight='demibold')
    plt.ylabel('Pressure (hPa)',fontsize=font_base,fontweight='demibold')

    # print the number of assimilated observations as a column on the right of the plot
    xses_cnt = np.int_(count[:])
    
    # Routine was displaying '--' text on the x axis where there were no values,
    #  which created a problem in SVG image format because XML/SVG comments
    #  include those characters <!-- -->.  This fixes the problem:
    for i in range(len(xses_cnt)):
        if not xses_cnt[i] > 0:
            xses_cnt[i] = 0

    axright = ax.twinx()
    axright.yaxis.set_ticks(yticks)
    axright.yaxis.set_ticklabels( xses_cnt.tolist(), weight='demibold', fontsize=font_base)

        
    if ttl.find('bias') > 0:
        ax.text(0.1, 0.6, 'BIAS', transform=ax.transAxes, fontsize=2.*font_base, fontweight='bold')
    else:
        ax.text(0.1, 0.6, 'STDV', transform=ax.transAxes, fontsize=2.*font_base, fontweight='bold')
    ax.text(1, 1, ' CNT\n\n', transform=ax.transAxes, ha='left', fontweight='bold', va='baseline')

    #final label on top of figure
    plt.suptitle(ttl,fontweight='demibold',fontsize=font_base)

    fig.subplots_adjust(left=0.125, right=0.875, top=0.925, bottom=0.075)

    fig.savefig('%s.png' % image_name, format='png') 
    plt.close(fig)  

def plot_mean_stdv_raob_type(data, data_range, var_indx, ttl, image_name, include):

    # plot the data
    font_base = 12

    fig = plt.figure(figsize=(7.5,7.5))

    pion = (0.10, 0.075, 0.85, 0.80)

    # define plotting axis 
    ax = fig.add_axes(pion)

    yrange=np.array( [ 0.0, len(mandatory_levels)-1 ] )

    # make a vertical dotted line along x=0
    plt.plot( [0.0,0.0], yrange,':',linewidth=3.0,color='#b1b1b1')

    colors = ['r','m','b','c','g','#996433','k','#bbe0e3','#ffd700','y']
    fg_lines = {}
    halos = {}

    # set the labels for the y-axis (mandatory pressure levels)
    yticks = list(range( ly['num']))
    ylabs = mandatory_levels
    ax.yaxis.set_ticks(yticks)
    ax.yaxis.set_ticklabels( ylabs, fontsize=font_base,
                            fontweight='demibold',color='k')

    line_color = -1
    for l, k in enumerate(sorted_raob_keys):
        if include == 'normal':
            if 'other' in k or 'profiler' in k:
                continue
        elif include not in k:
                continue
        xses = data['fg_depar'][:,l,var_indx]
        yses = np.ma.array( yticks, mask=xses.mask )
        halo = data['stdv_fg_depar'][:,l,var_indx]
        if not np.sum(data['cnt'][:,l,var_indx]):
                continue
        line_color += 1
        fg_lines[l] = plt.plot( xses, yses, '-', linewidth=3.5, 
                             color=colors[line_color%len(colors)], label=k )
        halos[l] = plt.fill_betweenx( yses, xses-halo, xses+halo, alpha=0.1, edgecolors='none',
                                      facecolor=colors[line_color%len(colors)] )
    ax.legend(loc='best',labelspacing=0.02)

    plt.xlim( data_range['min'], data_range['max'] )
    for line in ax.get_xticklabels():
        line.set_color('k')
        line.set_fontsize(font_base)
        line.set_fontweight('demibold')

    plt.xlabel(data_range['unit'],fontsize=font_base,fontweight='demibold')
    plt.ylabel('Pressure (hPa)',fontsize=font_base,fontweight='demibold')

    # plot the number of assimilated observations as a dotted line
    ax2 = ax.twiny()
    line_color = -1
    max_count = 0
    for l, k in enumerate(sorted_raob_keys):
        if include == 'normal':
            if 'other' in k or 'profiler' in k:
                continue
        elif include not in k:
                continue
        xses = data['cnt'][:,l,var_indx]
        yses = np.ma.array( yticks, mask=xses.mask )
        if not xses.sum():
                continue
        line_color += 1
        plt.plot(xses,yses,':', linewidth=1.5, color=colors[line_color%len(colors)] )
    plt.xlabel('ob count',fontsize=font_base,fontweight='demibold')
    plt.ylim( yrange[0], yrange[1] )
    ax2.yaxis.set_ticks(yticks)
    ax2.yaxis.set_ticklabels( ylabs, fontsize=font_base,
                            fontweight='demibold',color='k')
    for line in ax2.get_xticklabels():
        line.set_color('k')
        line.set_fontsize(font_base)
        line.set_fontweight('demibold')

    #final label on top of figure
    plt.suptitle(ttl,fontweight='demibold',fontsize=1.5*font_base)

    fig.savefig('%s.png' % image_name, format='png') 
    plt.close(fig)

def plot_zonal(data, data_range, ttl, image_name):

    # plot the data
    font_base = 12
    color_map = cmap=matplotlib.cm.nipy_spectral

    fig = plt.figure(figsize=(10,7.5))

    pion = (0.10, 0.15, 0.85, 0.80)
    cb_pion = (0.10, 0.05, 0.825, 0.05)

    # define plotting axis
    ax = fig.add_axes(pion)

    #  define colorbar ticks and normalize colors
    aticks = np.arange( np.round(data_range['min'], decimals=4),
                    np.round(data_range['max']+data_range['bin'], decimals=4),
                    data_range['bin'] )
    ticks = aticks[::-1]

    # set the labels for the y-axis (mandatory pressure levels)
    yticks = np.arange( ly['num'] ) + 0.5
    ylabs = mandatory_levels
    ax.yaxis.set_ticks(yticks)
    ax.yaxis.set_ticklabels( ylabs, fontsize=font_base,
                            fontweight='demibold',color='k')

    # set the x-axis and labels (latitude)
    xticks=[]
    xlabs=[]
    xstep = int(int(30)/int(lx['bin']))  # 30-degree labels x-axis
    for atick in range(0,lx['num'],xstep):
        xticks.append(float(atick) + 0.5)
        xlabs.append(np.round(lx['bins'][atick]))
    ax.xaxis.set_ticks(xticks)
    ax.xaxis.set_ticklabels(np.array(xlabs,dtype='int32'),fontsize=font_base,
                            fontweight='demibold',color='k')

    ####  main plot using 'pcolor'  ####
    norm = matplotlib.colors.Normalize(vmin=ticks.min(), vmax=ticks.max())
    c = plt.pcolor(data, edgecolors='none', norm=norm, cmap=color_map )

    # set min/max of x&y axes[xmin,xmax,ymin,ymax]
    plt.axis([ 0, lx['num'], 0, ly['num'] ])

    plt.ylabel('Pressure (hPa)',fontsize=font_base,fontweight='demibold')
    plt.title(ttl,fontweight='demibold',fontsize=1.5*font_base)


    #   add a colorbar
    cax = fig.add_axes(cb_pion)
    cb = matplotlib.colorbar.ColorbarBase(ax=cax,orientation='horizontal',
                                      cmap=color_map, ticks=ticks, norm=norm)


    for line in cax.get_xticklabels():
        line.set_color('k')
        line.set_fontsize(font_base)
        line.set_fontweight('demibold')

    fig.savefig('%s.png' % image_name, format='png')
    plt.close(fig)
    

def time_window(ndays, dtg):
#############################################################################
#   create a list of date-time groups going back ndays at 6-hr intervals
#############################################################################


# please replace with datetime ( if needed at all )


    ncycles = 4*int(ndays) + 1

    dom = np.array([31,28,31,30,31,30,31,31,30,31,30,31])


    print('Last ',ndays,' Days of Data Assimilation cycles')

    iyyyy=int(dtg[0:4])
    imm=int(dtg[4:6])
    idd=int(dtg[6:8])
    ihh=int(dtg[8:10])

    if ((iyyyy % 4) == 0):
        dom[1] = 29

    if ((ihh % 6) != 0):
        print('only set for 6-hr intervals')

    dtg_indx = [] # strarr(ncycles)
    cdtg_indx = [] # strarr(ncycles)

    for i in range(ncycles):
        if (ihh < 0):
            ihh = 24 + ihh
            idd = idd - 1
            if (idd <= 0):
                imm = imm - 1
                if (imm <= 0):
                    iyyyy = iyyyy - 1
                    imm = 12
                    idd = 31
                else:
                    idd = dom[imm-1]

        dtg_indx.append("%.4i%.2i%.2iT%.2i00Z" % (iyyyy,imm,idd,ihh))
        cdtg_indx.append("%.4i%.2i%.2i%.2i" % (iyyyy,imm,idd,ihh))

        ihh = ihh - 6

    dtg_indx.reverse()
    return dtg_indx, cdtg_indx
                
def initialize_raob_dict( ly, lx, raob_types, var_types, REAL_TYPE):

    # initialize summary data structure
    d = {}
    d['fg_depar'] = np.zeros((ly['num'], raob_types, var_types),dtype=REAL_TYPE)
    d['stdv_fg_depar'] = np.zeros((ly['num'], raob_types, var_types),dtype=REAL_TYPE)
    d['cnt'] = np.zeros((ly['num'], raob_types, var_types),dtype=REAL_TYPE)
    d['an_depar'] = np.zeros((ly['num'], raob_types, var_types),dtype=REAL_TYPE)
    d['stdv_an_depar'] = np.zeros((ly['num'], raob_types, var_types),dtype=REAL_TYPE)

    #  will reduce this to three groupings before plotting
    d['zonal_fg_depar'] = np.zeros((ly['num'], lx['num'], raob_types, var_types),dtype=REAL_TYPE)
    d['zonal_stdv_fg_depar'] = np.zeros((ly['num'], lx['num'], raob_types, var_types),dtype=REAL_TYPE)
    d['zonal_cnt'] = np.zeros((ly['num'], lx['num'], raob_types, var_types),dtype=REAL_TYPE)
    d['zonal_an_depar'] = np.zeros((ly['num'], lx['num'], raob_types, var_types),dtype=REAL_TYPE)
    d['zonal_stdv_an_depar'] = np.zeros((ly['num'], lx['num'], raob_types, var_types),dtype=REAL_TYPE)
    sorted_dic_keys = sorted( d.keys() )

    return d, sorted_dic_keys

def compute_mean_stdv_statistics(dstats):

    good = np.where( dstats['cnt'] > 0 )
    good_zonal = np.where( dstats['zonal_cnt'] > 0 )

    no_good = np.where( dstats['cnt'] == 0 )
    no_good_zonal = np.where( dstats['zonal_cnt'] == 0 )

    dstats['stdv_fg_depar'][good] = np.sqrt(dstats['stdv_fg_depar'][good]/dstats['cnt'][good])
    dstats['stdv_an_depar'][good] = np.sqrt(dstats['stdv_an_depar'][good]/dstats['cnt'][good])
    dstats['zonal_stdv_fg_depar'][good_zonal] = np.sqrt(dstats['zonal_stdv_fg_depar'][good_zonal] / dstats['zonal_cnt'][good_zonal])
    dstats['zonal_stdv_an_depar'][good_zonal] = np.sqrt(dstats['zonal_stdv_an_depar'][good_zonal] / dstats['zonal_cnt'][good_zonal])

    dstats['fg_depar'][no_good] = MISSING
    dstats['an_depar'][no_good] = MISSING
    dstats['stdv_fg_depar'][no_good] = MISSING
    dstats['stdv_an_depar'][no_good] = MISSING
    dstats['zonal_fg_depar'][no_good_zonal] = MISSING
    dstats['zonal_an_depar'][no_good_zonal] = MISSING
    dstats['zonal_stdv_fg_depar'][no_good_zonal] = MISSING
    dstats['zonal_stdv_an_depar'][no_good_zonal] = MISSING

    return dstats
    

def determine_range(rnd):
    for pwr in np.arange(-5,5):
        for val in [1.0, 2.0, 5.0]:
            base = val*(10.0**pwr)
            if base < rnd:
                continue
            return base
    return rnd

def get_vertical_index( pressure, ly ):

    yidx = -1
    for j in range(len(mandatory_levels)):
        if ly['mid_points'][j] >= pressure and pressure > ly['mid_points'][j+1]:
            yidx = j
            break
    if yidx == -1:
        print(' ... pressure value outside range ? (val,min,max): ', \
             pressure, ly['mid_points'].min(), ly['mid_points'].max())
        print(' ...  could not determine vertical index')

    return yidx

def get_latitude_index( lat, lx ):

    # find latitude index
    rnd_x = float(np.round( (lat - lx['min']) / lx['bin']) ) * lx['bin'] + lx['min']
    xidx = int(round((rnd_x - lx['min'])/lx['bin']))

    return xidx

if __name__ == "__main__":

    from optparse import OptionParser

    usage = 'usage: %prog -d date-time -i input-loc -o image-dir [-s save-dir] [-n ndays]'

    parser = OptionParser(usage)
    parser.add_option('-o', '--image-dir', dest='image_dir',
                      action='store', default=None,
                      help='Output location for image')
    parser.add_option('-i', '--input-loc', dest='filepath',
                      action='store', default=None,
                      help='Location of input files')
    parser.add_option('-d', '--date-time', dest='cdtg',
                      action='store', default=None,
                      help='10-digit date time group')
    parser.add_option('-n', '--ndays', dest='ndays',
                      action='store', default=30,
                      help='size of time window days backwards')
    parser.add_option('-s', '--save-dir', dest='output_dir',
                      action='store', default=None,
                      help='path where intermediary binary files will be written')

    (options, args) = parser.parse_args()

    # chk date
    if (options.cdtg):
        if len(options.cdtg) != 10:
            parser.error("expecting date in 10 character (yyyymmddhh) format \n \
                        received date: %s" % options.cdtg)
    else:
        parser.error("provide date in 10 character (yyyymmddhh) format, specify with -d option")

    if not options.filepath:
        parser.error("no path to monitoring directories given, specify with -i option")
    if not os.path.isdir(options.filepath):    
        parser.error("Missing monitoring directory: %s"% options.filepath)

    if not options.image_dir:
        parser.error("no path for outputting images given, specify with -o option")
    image_dir = os.path.join( options.image_dir, 'raob' )
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)

    if not options.output_dir:
        output_dir = options.filepath
    else:
        output_dir = options.output_dir

    main(options.filepath, options.cdtg, options.ndays, output_dir, image_dir)
