#!/usr/bin/env python

"""
Parse and plot NAVGEM radiance stats files.

1st command line argument is the directory holding /g${DTG}/*_ar_1_${DTG} files.
    Example directory: /radsm_data/ar_monitor/ar_radiance_ops
2nd optional argument is the end DTG. By default it's today 00Z
    Example DTG: 2010071500
3nd optional argument is the number of look-back days. By default it would be 30 days.
    Exmaple: 30

Original Author: Kai Xu, CSC, NRL 
Modified by:     Tim Whitcomb, NRL
Modified by:  Benjamin Ruston, NRL

"""

import datetime
import glob
import itertools
import logging
import optparse
import os.path
import sys
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mplticker
import numpy as np

from define_radiometer import sat_sen
#from IPython import embed as shell

try:
    parse_datetime = datetime.datetime.strptime
except AttributeError:
    parse_datetime = lambda str, fmt: datetime.datetime(*(time.strptime(str, fmt)[0:6]))

LOG        = logging.getLogger(__name__)
LOG_FORMAT = '%(message)s'

COLUMN_CHAN       = 0
COLUMN_NCHAN      = 1
COLUMN_XIV        = 2
COLUMN_STDV_XIV   = 3
COLUMN_RAW_XIV    = 5
COLUMN_STATUS     = 9

FMT_YYYYMMDDHH = '%Y%m%d%H'
FMT_YYYYMMDD   = '%Y%m%d'
FMT_YYYYMM     = '%Y%m'

FONT_BASE      = 12
FIGURE_OPTIONS = {'figsize': (6.5,5.0)}
AXES_DIMS      = (0.125, 0.09, 0.825, 0.785)

DEFAULT_END_DATE  = datetime.datetime.today()
DEFAULT_LOOK_BACK = 30  # days


#----------------------------------------------------------------------
# Top-Level
#----------------------------------------------------------------------

def main(argv=None):

    from optparse import OptionParser

    usage = 'usage: %prog [options] -i directory -d end-dtg [-n lookback-period -o image-dir -r exp-name]'
    parser = optparse.OptionParser(usage)
    parser.add_option('-v', '--verbose', dest='verbose', action='store_true',
                      help='Display progress messages.', default=True)
    parser.add_option('-q', '--quiet', dest='verbose', action='store_false',
                      help='Suppress progress messages.')
    parser.add_option('-i', '--directory', dest='directory', 
                       action='store', default=None,
                       help='directory path to input, sensor summary files')
    parser.add_option('-o', '--image-dir', dest='image_dir', 
                       action='store', default=os.getcwd(),
                       help='directory to output images')
    parser.add_option('-d', '--end-date', dest='end_date', 
                       action='store', default=DEFAULT_END_DATE,
                       help='date time group for end of time window')
    parser.add_option('-n', '--ndays', dest='look_back', 
                       action='store', default=DEFAULT_LOOK_BACK,
                       help='size of time window in days')
    parser.add_option('-r', '--exp-name', dest='exp_name', 
                       action='store', default=None,
                       help='experiment name to use in labeling')
    (options, args) = parser.parse_args(argv)

    # get input data path assuming g$CRDATE directories exist here
    if not options.directory:
        parser.error("no path to monitoring directories given, specify with -i option")
    if not os.path.isdir(options.directory):    
        parser.error("Missing monitoring directory: %s"% options.directory)

    # create output directory if it does not exist
    if not os.path.exists(options.image_dir):
        os.makedirs(options.image_dir)

    # convert 10-digit datetime to date object, use default object (today) if none provided
    if options.end_date == DEFAULT_END_DATE:
        end_date = options.end_date
    else:
        try:
            end_date = parse_datetime(options.end_date, FMT_YYYYMMDDHH)
        except:
            parser.error("end date supplied with -d should be 10-digit yyyymmddhh provided: %s"% options.end_date)
 
    # make sure look back is an integer
    try:
        look_back = int(options.look_back)
    except:
        parser.error("number of days supplied with -n should be integer provided: %s"% options.look_back)
    start_date = end_date - datetime.timedelta(look_back)

    # if no experiment name is given use base of directory name
    if not options.exp_name:
        options.exp_name = os.path.basename(options.directory)

    # Set up the message display - use logging for easy supression, but format
    # the messages to look just like print statements for now.
    if options.verbose:
        log_level = logging.DEBUG 
    else:
        log_level = logging.CRITICAL
    logging.basicConfig(level=log_level, format=LOG_FORMAT)
    

    process_sensors(options, start_date, end_date)


def process_sensors(options, start_date, end_date):
    """
    Given a directory of ar_monitor log files and a starting and end date
    for the monitoring window, generate a series of figures.

    """
    LOG.debug('Starting DTG is: %s' % start_date.strftime(FMT_YYYYMMDDHH))
    LOG.debug('Ending DTG is:   %s' % end_date.strftime(FMT_YYYYMMDDHH))

    directory = options.directory
    image_dir = options.image_dir
    exp_name  = options.exp_name

    for sensor in sat_sen:
        raw_data  = read_rad_stats(sensor, directory, start_date, end_date)
        if len(list(raw_data.keys())) == 0:
            print("No data found for sensor=%s"%(sensor))
            continue
        stat_data = compute_summary_stats(raw_data)

        plot_figures(stat_data, sensor, start_date, end_date, 
                     image_dir, exp_name)


#----------------------------------------------------------------------
# Data Parsing 
#----------------------------------------------------------------------

def read_rad_stats(sensor, directory, start, end):
    """
    Given a directory of ar_monitor log files (i.e. *_ar_1_$DTG) and a 
    starting and end date for the monitoring window, read the log files 
    for the given sensor.

    Return a nested dictionary:
        Satellite containing the given sensor
            datetime of available data
                Raw lines from the statistics file for this sat/sensor/dtg
                (one line per channel)
                    
    """
    data = {}
 
    sats = " ".join(["%s"%el for el in sat_sen[sensor]['sat'] ])
    LOG.debug(' ===> Processing all: %s for these sats: %s' % (sensor, sats))
    exp   = os.path.join(directory, 'g*', '*' + sensor + '*_ar_1_??????????')
    files = glob.glob(exp)

    file_dtg        = lambda fn: parse_datetime(fn.rsplit('_')[-1], FMT_YYYYMMDDHH)
    files_in_window = [fn for fn in files if start <= file_dtg(fn) <= end]
    for file in sorted(files_in_window):
            
        dtg = file_dtg(file)

        LOG.debug('Reading %s' % file)
        f = open(file, 'r')

        while True:
            try:
                line = next(f)
                    
                while 'RECOMPUTED' not in line:
                    line = next(f)
                while 'chan' not in line:
                    line = next(f)


                output = []
                line = next(f)
                sat = line.split()[0]
                while '---' not in line:
                    if line.find(sat) != -1: # Filter out garbage line
                        if ('assim' in line or 'monit' in line) and sat.lower() in sats.lower():
                            output.append(line)
                    line = next(f)

                # put into rad stats data dictionary
                key = '%s_%s' % (sat, sensor)
                if len(output) > 0:
                    if key not in data:
                        data[key] = {}
                    data[key][dtg] = output
            except StopIteration:
                # Jump here if any of the next() calls fails
                break
        f.close()

    return data
            

def compute_summary_stats(raw_data):
    """
    Generate a set of summary statistics for each sat/sensor in the data read
    from the monitor file.

    """
    stat_data = {}
    available_sat_sensors = [s for s in raw_data if raw_data[s]]
    for sat_sensor_name in available_sat_sensors:
        stat_data[sat_sensor_name] = get_sensor_stats(raw_data[sat_sensor_name])
    return stat_data
    

def get_sensor_stats(raw_sensor_data):
    """
    Given a set of raw lines (1 per channel) from the monitor file, prepare
    a set of summary statistics as a nested dictionary:

    Sensor Channel
        Date-time group        
            Tuple of statistics parsed from file (see below for details)
    """

    sat_sensor_summary = {}

    for dtg in sorted(raw_sensor_data):
        raw_lines = raw_sensor_data[dtg]
        for line in raw_lines:
            elem = line.split()
            
            if len(elem) == 10:
                # Old format (without satID)
                step = 0
            else:         
                # New format (with satID)
                step = 1
            
            chan       = elem[COLUMN_CHAN + step]
            raw_innov  = float(elem[COLUMN_RAW_XIV + step])
            innov      = float(elem[COLUMN_XIV + step])
            stdv_innov = float(elem[COLUMN_STDV_XIV + step])
            nchan      = int(elem[COLUMN_NCHAN + step])
            status     = elem[COLUMN_STATUS + step].strip()

            if chan not in sat_sensor_summary: 
                sat_sensor_summary[chan] = {}
            sat_sensor_summary[chan][dtg] = (raw_innov, innov, stdv_innov, nchan, status)

    return sat_sensor_summary


#----------------------------------------------------------------------
# Plot Generation
#----------------------------------------------------------------------

def plot_figures(stat_data, sensor, start_date, end_date, image_dir, exp_name,
                 ignore_nan=False):
    """
    Given raw data from the monitoring files (i.e. divided up by day and 
    channel), the sensor to be processed, and the limits of the monitoring
    window, produce a series of rad-grams and observation count plots for
    this sensor

    """

    sensor_image_dir = os.path.join(image_dir, sensor)
    if not os.path.exists(sensor_image_dir):
        os.makedirs(sensor_image_dir)

    for sat_sensor_name in stat_data:
        LOG.debug('   --- plotting rad grams for: %s' % sat_sensor_name)
        title = sat_sensor_name.replace('_', ' ').upper()
        for channel in sorted(stat_data[sat_sensor_name]):
            plot_rad_grams(stat_data[sat_sensor_name][channel], channel,  
                           title, 'rad_gram_' + sat_sensor_name + '_', sensor_image_dir,
                           start_date, end_date, exp_name, ignore_nan=True)

    LOG.debug('   --- plotting ob counts for: %s' % sensor)
    if 'geo_csr' not in sensor:
        for channel in sat_sen[sensor]['freq']:
            frequency  = sat_sen[sensor]['freq'][channel]
            try: plot_ob_count(stat_data, sensor, channel, frequency, sensor_image_dir, start_date, end_date, exp_name)
            except:pass
    else:
        for sat_sensor in list(stat_data.keys()):
            sat = sat_sensor.split('_')[0]
            imager_name = sat_sen[sensor][sat]
            for channel in stat_data[sat_sensor]:
                frequency = sat_sen[sensor][imager_name][channel]
                plot_ob_count(stat_data, sensor, channel, frequency, sensor_image_dir, 
                              start_date, end_date, exp_name, available_sensors=[sat_sensor])


def plot_rad_grams(channel_stats, channel, title, filename_base, image_dir, 
                   start_date, end_date, exp_name, ignore_nan=False):
    """
    Given the statistics for a single channel (divided by date-time group), 
    plot a rad-gram showing first guess and analysis departure statistics over the given time window.  
    The plots are saved in the supplied output directory using the given filename 
    base as a starting point for filenames of various channels.

    """

    # Extract data to plot
    dtgs_available = sorted(channel_stats.keys())
    innov       = np.array([channel_stats[dtg][1] for dtg in dtgs_available])
    raw_innov   = np.array([channel_stats[dtg][0] for dtg in dtgs_available])
    stdv_innov  = np.array([channel_stats[dtg][2] for dtg in dtgs_available])
    assimilated = np.any([channel_stats[dtgs_available[-1]][4] == 'assim'])

    full_innov      = spread_data(innov, dtgs_available, start_date, end_date)
    full_raw_innov  = spread_data(raw_innov, dtgs_available, start_date, end_date)
    full_stdv_innov = spread_data(stdv_innov, dtgs_available, start_date, end_date)

    # Create plotting canvas
    fig     = plt.figure(**FIGURE_OPTIONS)
    ax      = fig.add_axes(AXES_DIMS)

    # Create the plots
    xses = list(range(len(full_innov)))
    ax.plot(xses, full_raw_innov, 'b-')
    ax.plot(xses, full_innov, 'r-')
    ax.fill_between(xses, full_innov-full_stdv_innov, 
                    full_innov+full_stdv_innov, alpha=0.1, facecolor='r',
                    edgecolor='none')
    ax.axhline(y=0, color='k')

    # Figure out how to label the plot
    label = None
    for sensor in sat_sen:
        if sensor in filename_base:
            if 'geo_csr' not in sensor:
                label = '%s ch%02i' % (sensor, int(channel))
                freq  = sat_sen[sensor]['freq'][channel]
            else:
                for sat in sat_sen[sensor]['sat']:
                    if sat in filename_base: break
                imager_name = sat_sen[sensor][sat]
                label = '%s ch%02i' % (sensor, int(channel))
                freq  = sat_sen[sensor][imager_name][channel]
    if label is None:
        label = 'unknown ch%02i' % int(channel)
        freq  = 'unknown freq'

    # Y-Axis Labels
    if assimilated:
        ax.set_ylabel(label, color='r', fontsize = FONT_BASE)
    else:
        ax.set_ylabel(' '.join([label,'(monitor)']), fontsize = FONT_BASE)

    # X-Axis Labels
    plot_x_labels(ax, dtgs_available, start_date, end_date)

    # Main Labels
    fig.suptitle('Departure %s ch%02i %s' % (title, int(channel), freq),
                 fontweight='demibold', fontsize = FONT_BASE)
    if not ignore_nan:
        rawmean = full_raw_innov.mean()
        bcmean = full_innov.mean()
        bcstd = full_stdv_innov.mean()
    else:
        rawmean = np.nanmean(full_raw_innov)
        bcmean = np.nanmean(full_innov)
        bcstd = np.nanmean(full_stdv_innov)
    raw_xiv = ( "bias=%7.2g" % rawmean ).replace(" ", "")
    mean_xiv = ( "mean=%7.2g" % bcmean ).replace(" ", "")
    stdv_xiv = ( "stdv=%7.2g" % bcstd ).replace(" ", "")
    plot_title = ( "  ".join( [raw_xiv, mean_xiv, stdv_xiv, 'exp:'+exp_name] ) )
    ax.set_title(plot_title, fontsize = FONT_BASE)

    dtg_string = end_date.strftime(FMT_YYYYMMDDHH)
    filename   = os.path.join(image_dir, 
                              '%sch%02d_%s.png' % (filename_base, 
                                                   int(channel), dtg_string))
    LOG.debug('Save file to %s' % filename)
    fig.savefig(filename, format='png')
    plt.close(fig)


def plot_ob_count(stat_data, sensor, channel, frequency, image_dir, start_date, end_date, exp_name, available_sensors=None):
    """
    Plot a timeseries of the observation counts over the specified time
    window for a given sensor and a given channel, placing the result in the
    supplied directory.

    """

    fig     = plt.figure(**FIGURE_OPTIONS)
    ax      = fig.add_axes(AXES_DIMS)

    line_colors       = itertools.cycle(['r', 'g', 'b', 'm', 'c', 'y', 'k'])
    if not available_sensors:
        available_sensors = [s for s in stat_data if channel in stat_data[s]]
    for line_color, sat_sensor_name in zip(line_colors, available_sensors):
        channel_stats   = stat_data[sat_sensor_name][channel]
        available_dates = sorted(channel_stats.keys())
        assimilated     = np.any([channel_stats[d][4] == 'assim'
                               for d in available_dates])
        channel_counts  = np.array([channel_stats[d][3] 
                                    for d in available_dates])

        satellite           = sat_sensor_name.split('_')[0]
        full_channel_counts = spread_data(channel_counts, available_dates, 
                                          start_date, end_date)
        if assimilated:
            styled_line='-'
        else:
            styled_line=':'
        plt.plot(list(range(len(full_channel_counts))), full_channel_counts,
                color=line_color, label=satellite, linewidth=2, 
                linestyle=styled_line)

    leg = ax.legend(loc='best', labelspacing=0.025)
    leg.draw_frame(False)
    for t in leg.get_texts():
        t.set_fontsize(0.75*FONT_BASE)

    # Different satellites may have data at different date times - classify
    # a date as having missing data if *any* of the sat/sensors are missing
    all_dtgs      = [d for sat_sensor_name in available_sensors 
                       for d in stat_data[sat_sensor_name][channel]]
    complete_dtgs = [dtg
                     for dtg, group in itertools.groupby(sorted(all_dtgs))
                     if len(list(group)) == len(available_sensors)]
    plot_x_labels(ax, complete_dtgs, start_date, end_date)

    # Main titles
    plt.suptitle("Ob Count %s ch%2i %s" % (sensor, int(channel), frequency),
                 fontweight='demibold', fontsize = FONT_BASE)
    plt.title('solid (assimilate)    dotted (monitor)   exp:' + exp_name, fontsize = FONT_BASE)

    dtg_string = end_date.strftime(FMT_YYYYMMDDHH)
    if 'geo_csr' in sensor:
        image_name = ( 'ob_count_%s_ch%02d_%s.png' % (sat_sensor_name, int(channel), dtg_string))
    else:
        image_name = ( 'ob_count_%s_ch%02d_%s.png' % (sensor, int(channel), dtg_string))
    filename   = os.path.join(image_dir, image_name)
    LOG.debug('Save file to %s' % filename)
    fig.savefig(filename, format='png')
    plt.close(fig)

    
#----------------------------------------------------------------------
# Plot Helpers
#----------------------------------------------------------------------

def plot_x_labels(ax, dtgs_available, start_date, end_date):
    """
    Plot a series of x-labels on the given axis for the given time window.

    The available date-time groups are used to mark any missing days in
    red.

    """
    x_labels = get_x_labels(dtgs_available, start_date, end_date)

    ax.set_xlim(xmax=max(x_labels['index']))
    ax.xaxis.set_major_locator(mplticker.FixedLocator(x_labels['index']))
    ax.xaxis.set_ticklabels(x_labels['name'])
    for (is_missing, label) in zip(x_labels['missing'], ax.get_xticklabels()):
        if is_missing:
            label.set_color('r')
        else:
            label.set_color('k')
        label.set_fontsize(FONT_BASE*0.65)
        label.set_fontweight('demibold')
    

def get_x_labels(dtgs_available, start_date, end_date):
    """
    Given the start and end date of a time window, along with a list of dtgs
    within that window, generate a series of labels for each day with the 
    following properties:
        - Name    (the actual label)
        - Index   (integer position of label within larger time window)
        - Missing (whether any data is missing on a given day)

    This assumes that the start of the time window is a 00Z watch.

    """
    x_labels            = {}
    x_labels['name']    = []
    x_labels['index']   = []
    x_labels['missing'] = []

    # Label only the 00Z watch
    label_delta = datetime.timedelta(days=1)
    label_dates = dtg_range(start_date, end_date, label_delta)

    # Figure out where the 00Z watches are in our master list
    watch_delta = datetime.timedelta(hours=6)
    watch_dates = dtg_range(start_date, end_date, watch_delta)
    x_labels['index'] = [watch_dates.index(d) for d in label_dates]

    # Flag any date that has missing data for the 00Z, 06Z, 12Z, or 18Z watch:
    # We already know the dates, so we can safely ignore the "unique keys"
    # returned by itertools.groupby()
    data_present        = [d in dtgs_available for d in watch_dates]
    just_days           = [datetime.datetime(d.year, d.month, d.day)
                           for d in watch_dates]
    get_day             = lambda t: t[0]
    get_present         = lambda t: t[1]
    group_iter          = itertools.groupby(list(zip(just_days, data_present)), 
                                            key=get_day)
    present_by_day      = [list(g) for _, g in group_iter]
    x_labels['missing'] = [not np.all([get_present(f) for f in present_flags]) 
                                   for present_flags in present_by_day]
    
    # First and last index add the Month and year after carriage returns, but
    # all other labels are just the day
    day_label            = lambda d: d.strftime('%d')
    full_label           = lambda d: '\n'.join([d.strftime('%d'), 
                                                d.strftime('%b').upper(), 
                                                d.strftime('%Y')])
    x_labels['name']     = [day_label(d) for d in label_dates]
    x_labels['name'][0]  = full_label(label_dates[0])
    x_labels['name'][-1] = full_label(label_dates[-1])

    return x_labels

#----------------------------------------------------------------------
# Miscellaneous Helpers
#----------------------------------------------------------------------

def dtg_range(start, end, delta):
    """Return a date range *INCLUSIVE* of the endpoint."""
    range = []
    current = start
    while current <= end:
        range.append(current)
        current += delta
    return range
    

def spread_data(compressed_data, dtgs_available, window_start, window_end):
    """
    Given data at a sequence of date-time groups that lie in a subset of a
    larger window, return an array covering the entire time period with the
    supplied data inserted at the proper times and masked where there is no
    data available.

    """
    # Generate the full date range
    delta      = datetime.timedelta(hours=6)
    date_range = dtg_range(window_start, window_end, delta)

    data_available   = np.array([d in dtgs_available for d in date_range])
    data_unavailable = np.logical_not(data_available)

    expanded_data                 = np.zeros(len(date_range),
                                             dtype=compressed_data.dtype)
    expanded_data[data_available] = compressed_data
    return np.ma.masked_where(data_unavailable, expanded_data)


if __name__ == "__main__":
    main()
