#!/usr/bin/env python

# Plot JEDI Minimization 
#
# usage clause at bottom of file
#
#


import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os.path
import sys
import numpy as np
from datetime import date, timedelta
import datetime

from IPython import embed as shell


# globals -- globals everywhere
zcolors = [ 'g', 'r', 'c', 'm', 'y', 'k', 'g', 'r', 'c' ]
zlines  = [ '-', ':', '-', ':', '-', ':', ':', '-', ':' ]

minimizer_values = { 
                    'rho'                 : 'DRIPCGMinimizer rho',
                    'alpha'               : 'DRIPCGMinimizer rho',
                    'gradient reduction'  : 'Gradient reduction (',
                    'norm reduction'      : 'Norm reduction (',
                    'J'                   : 'Quadratic cost function: J ',
                    'Jb'                  : 'Quadratic cost function: Jb',
                    'JoJc'                : 'Quadratic cost function: JoJc',
}

try:
    parse_datetime = datetime.datetime.strptime
except AttributeError:
    # datetime does not contain strptime prior to python v2.5
    import time
    parse_datetime = lambda str, fmt: datetime.datetime(*(time.strptime(str, fmt)[0:6]))


def main(files, image_dir, end):

    print ( "files: ", files)

    # calculate start DTG
    end_date = date(int(end[0:4]), int(end[4:6]), int(end[6:8]))
    start_date = end_date # - timedelta(int(look_back))

    start = '%4i%.2i%.2i00' % (start_date.year, start_date.month, start_date.day)

    # read {run}_sweepar_1_DTG files
    sweep = read_files(files, start, end)

    # plot figures
    plot_figures(sweep, image_dir, start, end)


def read_files(files, start, end):

    # global data structure
    sweep = {}


    zfiles = [ files ]
    dtg = end
    # loop through files
    for file in sorted(zfiles):
            
        # read file
        print('Reading file: ' + file)
        f = open(file, 'r')
        for line in f:
            # DRIPCGMinimizer rho = 1672606197459798.50000000, alpha = 0.00001359
            # DRIPCG end of iteration 1
            # Gradient reduction ( 1) = 4113490580.143638
            # Norm reduction ( 1) = 1.174093451745387

            # Quadratic cost function: J   ( 1) = 7197617.190646479
            # Quadratic cost function: Jb  ( 1) = 2.101062800065452
            # Quadratic cost function: JoJc( 1) = 7197615.089583679
            for k, v in minimizer_values.items():
                if line.find(v) != -1:
                    if dtg not in sweep: init_sweep(sweep, dtg)
                    if k not in sweep[dtg]: sweep = init_sweep(sweep, dtg, key=k)
                    if dtg not in list(sweep.keys()):
                        sweep = init_sweep(sweep, dtg)
                    elem = line.split()[-1]
                    if 'rho' in k:
                        elem = line.split(',')[0].split()[-1]
                    
                    sweep[dtg][k].append(float(elem))
    
        f.close()

    return sweep

def init_sweep(sweep, dtg, key=None):

    if dtg not in sweep: sweep[dtg] = {}
    if key:
        if key not in sweep[dtg]: sweep[dtg][key] = []

    return sweep

def plot_figures(sweep, image_dir, start, end):

    # prepare figrue
    # fig = plt.figure(figsize=(8,6))
    fig = plt.figure()

    # main plotting window
    rect = (0.1, 0.15, 0.80, 0.75)
    ax = fig.add_axes(rect)
    
    #########################################################################
    ### create a plot ###  minimization with a left-justified y-axis
    #########################################################################
    xax = np.arange(len(sweep[end]['J'])) + 1

    for i, k in enumerate(sweep[end].keys()):
        yax = sweep[end][k]/np.max(sweep[end][k]),
        yax = yax[0][:len(xax)]
        print ( k, np.shape(xax), np.shape(yax) )
        ax.plot(xax, yax, label=k, linewidth=2.0, 
          color=zcolors[i], linestyle=zlines[i] )

    ax.set_xlim(xmin=1, xmax=len(xax))
    ax.set_xlabel('Iteration Number')
    ax.set_ylabel('Parameter Normalized by Max Value')
    ax.legend()

    ###########################################
    ### final labeling and save figure ###
    ###########################################
    # Main plot title
    title = ' '.join(['JEDI', 'Minimization', end[:10]])
    fig.suptitle(title)
        
    # save image file
    image_name = '_'.join( [ 'jedi', 'convergence', end[:10] ] )
    image_name = os.path.join(image_dir, image_name+'.png')
    print('Saving figure: ' + image_name)
    fig.savefig(image_name, format='png') 
    plt.close(fig)

def calculate_dev(sweep, field, watch_dates, x_labels):

    result = []
    deviation = {}
    mean = {}
    stdv = {}  # not used for now

    # calculate mean and stdv for each ZZ
    for hh in ['00', '06', '12', '18']:
        vals = []
        for key in sorted(sweep.keys()):
            if key[-2:] == hh:
                vals.append(sweep[key][field])

        mean[hh] = np.mean(vals)
        stdv[hh] = np.std(vals)

    # calculate deviation
    for key in sorted(sweep.keys()):
        hh = key[-2:]
        deviation[key] = 1. - np.absolute((sweep[key][field] - mean[hh]) / mean[hh])

    # now fill in for entire time window of plot which may have missing dates
    for i, adate in enumerate(watch_dates):
        fdate = '%4i%.2i%.2i%.2i' % (adate.year, adate.month, adate.day, adate.hour)
        if fdate in list(sweep.keys()):
            result.append( deviation[fdate] )
        else:
            result.append( np.float( 0. ) )
    
    return result

#----------------------------------------------------------------------
# Plot helper copied from plot_rad_stats.py
#----------------------------------------------------------------------

def dtg_range(start, end, delta):
    """Return a date range *INCLUSIVE* of the endpoint."""
    range = []
    current = start
    while current <= end:
        range.append(current)
        current += delta
    return range


if __name__ == "__main__":

    import glob
    from optparse import OptionParser

    usage = 'usage: %prog -i input-file -d date-time [-o image dir]'
    parser = OptionParser(usage)
    parser.add_option('-i', '--input-file', dest='files',
                      action='store', default=None,
                      help='Location of file')
    parser.add_option('-d', '--date-time', dest='cdtg',
                      action='store', default=None,
                      help='10-digit date time group')
    parser.add_option('-o', '--image-dir', dest='image_dir',
                      action='store', default=os.getcwd(),
                      help='Output location for image')

    (options, args) = parser.parse_args()

    # chk date
    if (options.cdtg):
        if len(options.cdtg) != 10:
            parser.error("expecting date in 10 character (yyyymmddhh) format \n \
                        received date: %s" % options.cdtg)
        else:
            end_cdtg = options.cdtg
    else:
        parser.error("please provide a date in 10 character (yyyymmddhh) format")

    if not (options.files):
        parser.error("please provide file(s) via -i option")

    if not (glob.glob(options.files)):
        parser.error("file(s) provided with -i option not found: %s" % options.files)

    # call main routine
    main(options.files, options.image_dir, end_cdtg)
