#!/usr/bin/python

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.colors
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import matplotlib.ticker as mticker
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER

cm   = matplotlib.cm.get_cmap('jet')

def plot_global(data, lat, lon, title, image_name, range=[None,None], units='', dot_size=2.5, colormap=cm):

    # plot the data
    font_base = 12

    fig = plt.figure(figsize=(10,6.5))
    image_extent = (-180, 180, -90, 90)

    # the gridspec nrows and ncols, then ratios for each row
    gs = gridspec.GridSpec(4,1,height_ratios=[48,8,8,3],hspace=0)


    # define map for Cartopy
    map_projection = ccrs.PlateCarree()

    ax = plt.subplot(gs[0],projection=map_projection)
    #All these needed for plate carree
    ax.set_extent(image_extent,map_projection)

    gl = ax.gridlines(crs=map_projection, draw_labels=True,
                  linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
    gl.top_xlabels = False
    gl.left_xlabels = False
    gl.xlines = True
    gl.xlocator = mticker.FixedLocator([-180, -120,  -60,    0,   60,  120,  180])
    gl.ylocator = mticker.FixedLocator([-90, -60, -30,   0,  30,  60,  90])
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER


    # data must all be same type (numpy arrays)
    lat = np.array(lat, dtype='float32' )
    lon = np.array(lon, dtype='float32' )
    data = np.array(data, dtype='float32' )
    lon[lon > 180] -= 360.

    # optional mask outside given range
    if range[0]:
        data = np.ma.masked_outside( data, range[0], range[1])
        lat = np.ma.array( lat, mask = data.mask )
        lon = np.ma.array( lon, mask = data.mask )
    else:
        if 'DEPAR' in title or 'CORR' in title:
            symmetric = np.max( [np.abs(data.min()), np.abs(data.max()) ] )
            range = ( -1.*symmetric, symmetric )
        else:
            range = ( data.min(), data.max() )
    if range[0] == range[1]:
        print(' min and max of range are equal, exiting for: ', title)
        return
    #print('range to be used in plot: ', range)

    # nomalize data to colormapping
    norm = matplotlib.colors.Normalize(vmin=range[0], vmax=range[1])

    ax.scatter(lon, lat, s=dot_size, marker="o",
               c=data, norm=norm, edgecolors='none',
               cmap=colormap, transform=ccrs.PlateCarree())
    ax.coastlines()
    gl = ax.gridlines()
    # add a title with some stats from data
    data_stats = ( "min=%10.4g    max=%10.4g    mean=%10.4g  stdv=%10.4g" %
                   (data.min(), data.max(), data.mean(), data.std()) )
    print(data_stats)
    plt.title(data_stats, fontweight='demibold', fontsize=1.0*font_base)

    #  add a colorbar
    histogram_colorbar(data, gs, range=range, clabel=units, colormap=colormap)

    # add an overarching title to figure
    fig.suptitle(title, fontweight='demibold', fontsize=1.5*font_base)

    # write image to file
    print('saving: %s.png' % image_name )
    fig.savefig('%s.png' % image_name, format='png')
    plt.close(fig)

def histogram_colorbar(data, gs, range=None, clabel=None, bins=66, colormap=cm):

    if data is None:
        print("missing data input")
        sys.exit()
    # Use 1-D data for the histogram
    data = data.flatten()

    if range is None:
        N, bins = np.histogram(data,bins=bins)
        bin_frac = 1000. * np.array(N,dtype='float64')/np.float(np.max(N))
        hrange = np.where(bin_frac > 1)
        range = ( bins[np.min(hrange)], bins[np.max(hrange)+1] )
    if range[0] == range[1]:
        print("min and max values are equal")
        sys.exit()

    # add a histogram
    ax2 = plt.subplot(gs[2])
    N, bins, patches = ax2.hist(data,bins,range=range)
    sum = np.sum( N )

    # color the histogram bars according to value
    norm = matplotlib.colors.Normalize(vmin=range[0], vmax=range[1])
    bin_centers = 0.5*(bins[1:] + bins[:-1])
    for (bin_center, patch) in zip(bin_centers, patches):
        patch.set_facecolor(colormap(norm(bin_center)))
    ax2.set_xlim(range[0],range[1])
    ax2.autoscale(enable=True,axis='y')
    ax2.xaxis.set_major_locator(matplotlib.ticker.NullLocator())
    ax2.yaxis.set_major_locator(matplotlib.ticker.NullLocator())
    ax2.axis('off')
    ax2.set_title('Total: ' + str(sum) )

    # add traditional colorbar too
    cax = plt.subplot(gs[3])
    c = matplotlib.colorbar.ColorbarBase(cax, orientation='horizontal', norm=norm, cmap=colormap)
    c.set_label(clabel)
