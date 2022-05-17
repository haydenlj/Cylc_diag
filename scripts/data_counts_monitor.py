#!/usr/bin/python

import glob
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatch
import operator
import os.path
import sys



def main(stats_dir, dtg, ndays, image_dir, ar_run):


    dtg_indx, mon_indx = time_window(ndays, dtg)

    #  Read data_counts_total_$dtg files
    data, names = read_data_counts(stats_dir, dtg_indx)

    title = ' NAVGEM Observation Monitor\n' + 'Area: GLOBAL   Run: ' + ar_run
    image_name = '_'.join( ['data', 'count', dtg] )
    image_name = os.path.join(image_dir, image_name)
    plot_data_counts(data, names, dtg_indx, mon_indx, image_name, title)


def read_data_counts(stats_dir, dtg_indx):

    ###########################################################
    #  initailize all that will be returned from bias files
    ###########################################################

    data = {}

    names = []
    ncycles = len(dtg_indx)

    for i in range(ncycles):
        stats_file = os.path.join(stats_dir, 'g'+dtg_indx[i], '*data_counts_total_*' + dtg_indx[i])
        stat_files = glob.glob(stats_file)
        if not stat_files:
            print('missing file: ', stats_file)
            continue
        stats_file = stat_files[0] 

        if os.path.exists(stats_file):

            print('reading file : ', stats_file)
            f = open(stats_file, "r")
            file_sections = { 'conventional': False, 'satellite': False, 'summary': False }
            try:
                # position to start of data counts
                while True:
                    stats = next(f)
                    if 'FINAL POST-SWEEP' in stats: break

                # read in the data counts
                while True:
                    stats = next(f)
                    if '||' in stats:
                        if "data_smry" in stats: continue
                        if dtg_indx[i] in stats: continue
                        if "ob_type"   in stats: continue
                        if '-----' in stats: continue
                        if len(stats.strip()) == 0 : continue

                        name = stats[4:21].strip()
                        count = stats[22:32].strip()
                        count = int(count.replace(' ',''))
                        if 'bT' in name: 
                            file_sections['satellite'] = True
                            name = name.replace('bT','')
                            name = name.strip()
                            if 'csr' in name:
                                name = 'GeoCSR'
                            if 'ssmisuas' in name:
                                name = 'SSMIS UAS'
                            if 'atovs' in name:
                                name = 'AMSU-A'
                            name = name.upper()
                        if 'benang' in name: 
                            name = 'GPS-RO'
                        if name == 'raob':
                            file_sections['conventional'] = True
                            if int(dtg_indx[i][8:10])%12 > 0:
                                name = 'offtime raob'
                            else:
                                name = 'raob'
                        #print 'name: ', name, ' count: ', count  # debug
                        if name not in list(data.keys()):
                            names.append(name)
                            data[name] = np.zeros(ncycles,dtype='int32')
                        data[name][i] = count

                        if 'total' in name:
                            file_sections['summary'] = True
                            break

            except (IOError,StopIteration):
                for k, v in file_sections.items():
                    if not v:
                        print(stats_file, "missing section: ", k)
            f.close()

        else:
            print('missing file: ', stats_file)

    if len(list(data.keys())) == 0:
        print('no data found')
        sys.exit()

    return data, names


def plot_data_counts(data, names, dtg_indx, mon_indx, image_name, title):
    ##########################################################

    dmean = {}
    ncycles = len(dtg_indx)

    #for val in data.keys():
    for k in names:
        data_mask = np.ma.masked_less_equal(data[k], 0)
        data_mean = np.mean(data_mask)
        if not data_mean:
            dmean[k] = 0.0
        else:
            dmean[k] = data_mean

    name_sort = sorted(iter(dmean.items()),key=operator.itemgetter(1),reverse=True)

    percent = np.zeros((len(list(data.keys())),ncycles),dtype='float32')

    idx = 0
    for val in name_sort:
        if dmean[val[0]] > 3000:
            percent[idx,:] = 100*data[val[0]]/dmean[val[0]]
        elif dmean[val[0]] > 0:
            rvals = 100*data[val[0]]/dmean[val[0]]
            rvals = np.ceil(rvals*8.)/8.
            rvals = rvals*(rvals <= 12.5) + \
                    40.*np.logical_and(rvals > 12.5,rvals <= 25) + \
                    100.*np.logical_and(rvals > 25,rvals < 175) + \
                    175.*(rvals > 175)
            percent[idx,:] = rvals
        else:
            percent[idx,:] = 0.0
        idx = idx + 1


    ##########################################################
    #
    #  Plot Assimilation Results
    #
    ##########################################################

    font_base = 10
    #fig = plt.figure(figsize=(9.6,7.2))
    fig = plt.figure(figsize=(10.5,7.25))

    pion = (0.15, 0.125, 0.76, 0.80)
    cb_pion = (pion[0], 0.0, pion[2], 0.135)

    ################################
    # LHS  y-axis observation type
    ################################
    # define plotting axis 
    ax1 = fig.add_axes(pion)

    # set min/max of x&y axes[xmin,xmax,ymin,ymax]
    #plt.axis([0,len(dtg_indx),0,len(name_sort)+1])   
    plt.axis([0,len(dtg_indx),0,len(name_sort)])   

    ax1.yaxis.set_ticks(np.arange(len(name_sort))+0.5)
    ylab = []
    for val in name_sort:
        ylab.append(val[0])
    ax1.yaxis.set_ticklabels(ylab,fontsize=font_base,color='k')

    # Suppress tick marks and x-axis labels
    for line in ax1.get_xticklines() + ax1.get_yticklines():
        line.set_visible(False)


    minorLocator = plt.MultipleLocator(1.0)
    ax1.yaxis.set_minor_locator(minorLocator)

    #minorFormattor = plt.FormatStrFormatter('%10.4f')
    #ax1.yaxis.set_minor_formatter(minorFormattor)

    ################################
    # LHS  y-axis observation count
    ################################
    j = 0.0
    for val in name_sort:
        rnd_mean = val[1]
        for dorder in range(2,12):
            if rnd_mean/10**(dorder) < 10*(dorder):
                break
        rnd_mean = np.ceil(rnd_mean*1./10**(dorder))*10**(dorder)
        yup = np.mean(data[val[0]])
        nope = np.mean(percent[int(j),:])
        #print ("%s  %8i  %8i   %8i  %5.2f" % (val[0], val[1], rnd_mean, yup, nope))
        rnd_mean = ("%i"%(rnd_mean))
        #BCR - need a better way to align numbers on left most region of plot and keep y-axis
        plt.text(-23,j,rnd_mean,
                        horizontalalignment='left',
                        fontsize=font_base*1.0,
                        fontweight='demibold')
        j += 1.0

    ################################
    # x-axis only works when set the font specs here??
    ################################
    for line in ax1.get_xticklabels():
        line.set_color('k')
        line.set_fontsize(font_base)
        line.set_fontweight('demibold')

    ###############################
    # RHS y-axis observation type
    ###############################

    # establish a right-hand side axis
    ax2 = ax1.twinx()

    # set min/max of x&y axes[xmin,xmax,ymin,ymax]
    plt.axis([0,len(dtg_indx),0,len(name_sort)])   

    # subset of y-axis labels "monitored" channels
    ax2.yaxis.set_ticks(np.arange(len(name_sort))+0.5)
    ax2.yaxis.set_ticklabels(ylab)
    for line in ax2.get_yticklabels():
        line.set_color('k')
        line.set_fontsize(font_base)
    #  suppress y-tick marks for subset y-axis
    for line in ax2.get_xticklines() + ax2.get_yticklines():
        line.set_visible(False)

    ##############################################
    # x-axis day labels assuming 6-hr update cycle
    ##############################################
    # First and last index add the Month and year after carriage returns
    dtrunc = []
    for d in range(0,len(dtg_indx),4):
        dtrunc.append(dtg_indx[d][6:8])

    # now create duplicate axis for plot and 2nd subset of y-axis labels
    ax = fig.add_axes(pion,sharex=ax1)
    ax.xaxis.set_ticks(list(range(0,len(dtg_indx),4)))

    # first and last index add the Month and year after carriage returns
    ax.xaxis.set_ticklabels( [dtrunc[0] + '\n' + mon_indx[0]] +  
                              dtrunc[1:-1] + 
                             [dtrunc[-1] + '\n' + mon_indx[-1] + dtg_indx[-1][0:4]] )
    for line in ax.get_xticklabels():
        line.set_visible(False)
#       line.set_color('k')                   # these do nothing
#       line.set_fontsize(font_base)          # these do nothing
#       line.set_fontweight('demibold')       # these do nothing

    for line in ax.get_yticklabels():
        line.set_visible(False)


    ##############################################
    # main plotting 
    ##############################################
    # define colorbar ticks and normalize colors (change numpy to python list float)
    my_colors = ['k','r','#ffd700','g',   'c']
    my_labels = [' = 0','0 - 25%','25 - 50%', '50 - 150%','> 150%']
    lowcnt_labels = [' = 0','0 - 12.5%','12.5 - 25%', '25 - 175%','> 175%']
    lab_color = ['w',      'k',   'k',    'k',   'k']
    cmap = matplotlib.colors.ListedColormap(my_colors)
    norm = matplotlib.colors.BoundaryNorm([-1,0,25,50,150,500],ncolors=cmap.N)

    ####  main plot using 'pcolor'  ####
    #   plot the data
    parm_masked = np.ma.masked_less_equal(percent, 0)
    c = plt.pcolor(parm_masked, edgecolors='w', cmap=cmap, linewidths=0.2, norm=norm)

    # set min/max of x&y axes[xmin,xmax,ymin,ymax]
    plt.axis([0,len(dtg_indx),0,len(name_sort)])   

    for line in ax.get_xticklabels():
        line.set_visible(False)
    #   label the plot
    plt.title(title, fontweight='demibold', fontsize=1.5*font_base)


    ##############################################
    # add color legend
    ##############################################
    #   create a true second axes
    cax = fig.add_axes(cb_pion,frameon=False)

    #   add a legend
    for k in range(1,len(my_colors)):
        plt.text(-0.4, 1.0,  'OB CNT',ha='right',va='center',
                              fontsize=font_base*1.5,
                              fontweight='demibold')
        plt.text(0.35,   1.5, 'ob cnt < 3000',ha='center',va='center',color='k',
                              fontsize=1.0*font_base,fontweight='demibold')
        plt.text(k+0.25, 1.5, lowcnt_labels[k],ha='center',va='center',color=lab_color[k],
                              bbox=dict(boxstyle='round',fc=my_colors[k],ec='k'),
                              fontsize=1.5*font_base,fontweight='demibold')
        plt.text(0.35,   0.5, 'ob cnt > 3000',ha='center',va='center',color='k',
                              fontsize=1.0*font_base,fontweight='demibold')
        plt.text(k+0.25, 0.5, my_labels[k],ha='center',va='center',color=lab_color[k],
                              bbox=dict(boxstyle='round',fc=my_colors[k],ec='k'),
                              fontsize=1.5*font_base,fontweight='demibold')
    # set min/max of x&y axes[xmin,xmax,ymin,ymax]
    plt.axis([0,5,0,3])
    cax.xaxis.set_visible(False)
    cax.yaxis.set_visible(False)
    
    image_name = ('%s.png' % image_name )
    print("creating image: " + image_name)
    fig.savefig(image_name, format='png') 
    plt.close(fig)


def time_window(ndays, dtg):
#############################################################################
#   create a list of date-time groups going back ndays at 6-hr intervals
#############################################################################


    ncycles = 4*int(ndays) + 1


    month = [ 'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', \
              'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC' ]
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

    mon_indx = [] # strarr(ncycles)
    dtg_indx = [] # strarr(ncycles)

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

        dtg_indx.append("%.4i%.2i%.2i%.2i" % (iyyyy,imm,idd,ihh))
        mon_indx.append(month[imm-1])

        ihh = ihh - 6

    dtg_indx.reverse()
    mon_indx.reverse()
    return dtg_indx, mon_indx
 
 
if __name__ == "__main__":

    from optparse import OptionParser

    usage = 'usage: %prog -d date-time -i input-loc -o image-dir [-r ar_run] [-n ndays]'

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
    parser.add_option('-r', '--run-name', dest='ar_run',
                      action='store', default=None,
                      help='name of experiment run')

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
    if not os.path.exists(options.image_dir):
        os.makedirs(options.image_dir)

    if not options.ar_run:
        print("no name for experiment run given, specify with -r option")
        ar_run = os.path.split(options.filepath)[-1]
        print("  ===> using directory name: ", ar_run)
    else:
        ar_run = options.ar_run

    main(options.filepath, options.cdtg, options.ndays, options.image_dir, ar_run)
