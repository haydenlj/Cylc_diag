# (C) Copyright 2021-2021 UCAR
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.

import netCDF4 as nc
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import os
import re


class Diagnostic:
    """
    Given a filename, fetches file and contains basic diagnostic data
    needed for binning or plotting
    Attributes:
        platform: ex) 'amsua_n19'
        date: ex) 2020-12-14T21:00:00Z. Must be in this format
    """

    def __init__(self,
                 filename: str,
                 platform: str,
                 date: str
                 ):

        self.filename = filename
        self.platform = platform
        self.date = date

        # read data and extract metadata
        self.data = nc.Dataset(self.filename)
        self.lon = self.data['MetaData']['longitude'][:]
        self.lat = self.data['MetaData']['latitude'][:]
        self.vert = self.data['MetaData']['altitude'][:]
        self.satid = self.data['MetaData']['occulting_sat_id'][:]
        
        # extract data to plot
        # TODO: add qc filter?
        self.obs = self.data['ObsValue']['bending_angle'][:]
        self.hofx = self.data['hofx']['bending_angle'][:]
    
        # calculate diagnostics
        self.omb = self.obs - self.hofx


class ScatterMap:
    """
    Creates a map with points colored by value
    Attributes:
        lon: an array of longitudes
        lat: an array of latitudes
        vert: an array of altitudes
        vals: an array of values for points' colors
        title: will be displayed above map figure and will name png file
        image_path: path to directory for saving the resulting images
    """

    def __init__(self, diag, image_path: str, colmin=None, colmax=None):
        self.lon = diag.lon
        self.lat = diag.lat
        self.vert = diag.vert
        self.vals = diag.satid
        self.sat_id = pd.read_csv('sat_id.csv', index_col=0).to_dict()
        self.title = f"{diag.platform} occulting_sat_id value {diag.date}"
        self.image_path = image_path
        self.filename_ob = f"{diag.platform}.all.occulting_sat_id.ob.{re.sub('[^0-9]', '', diag.date)}.png"
        self.filename_omb = f"{diag.platform}.all.occulting_sat_id.omb.{re.sub('[^0-9]', '', diag.date)}.png"
        self.filename_hofx = f"{diag.platform}.all.occulting_sat_id.hofx.{re.sub('[^0-9]', '', diag.date)}.png"
        self.colmin = colmin
        self.colmax = colmax
        self.plot()
       
        
    def plot(self):

        # subset by surface level
        self.lat = self.lat[np.where(self.vert<1000)]
        self.lon = self.lon[np.where(self.vert<1000)]
        self.vals = self.vals[np.where(self.vert<1000)]

        # change sat id to categorical
        self.vals_cat = []
        for val in self.vals:
            try:
                self.vals_cat.append(self.sat_id['name'][val])
            except:
                self.vals_cat.append('unknown')

        # define colorbar
        stdev = np.nanstd(self.vals)
        mean = np.nanmean(self.vals)
        # diverging colormap, centered around zero
        if np.nanmin(self.vals) < 0:
            cmax = self.colmax if self.colmax is not None else abs(mean + (2 * stdev))
            cmin = self.colmin if self.colmin is not None else -cmax
            cmap = 'RdBu'
        # sequential colormap, centered around mean
        else:
            cmax = self.colmax if self.colmax is not None else mean + (2 * stdev)
            cmin = self.colmin if self.colmin is not None else np.maximum(mean - (2 * stdev), 0.0)
            cmap = 'viridis'

        # initialize the plot pointing to the projection
        fig = plt.figure(figsize=(18, 12))
        ax = plt.axes(projection=ccrs.PlateCarree(central_longitude=0))
        plt.rcParams['font.size'] = '16'


        # plot grid lines
        gl = ax.gridlines(crs=ccrs.PlateCarree(central_longitude=0), draw_labels=True,
                          linewidth=1, color='gray', alpha=0.5, linestyle='-')
        gl.top_labels = False
        gl.xlocator = mticker.FixedLocator(
            [-180, -135, -90, -45, 0, 45, 90, 135, 179.9])
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")

        # scatter data
        df = pd.DataFrame(list(zip(self.lon, self.lat, self.vals_cat)), columns = ['Lon' , 'Lat', 'id'])
        groups = df.groupby("id")
        for name, group in groups:
             ax.plot(group["Lon"], group["Lat"], marker="o", linestyle="", label=name)
        plt.legend(loc="lower left", ncol=4)

        # plot globally
        ax.set_global()

        # draw coastlines
        ax.coastlines()

        # figure labels
        plt.title(self.title)
        ax.text(0.45, -0.1, 'Longitude', transform=ax.transAxes, ha='left')
        ax.text(-0.08, 0.4, 'Latitude', transform=ax.transAxes,
                rotation='vertical', va='bottom')

        # save plot
        if not os.path.isdir(self.image_path):
            os.makedirs(self.image_path)

        plt.savefig(os.path.join(self.image_path, self.filename_ob))
        plt.savefig(os.path.join(self.image_path, self.filename_hofx))
        plt.savefig(os.path.join(self.image_path, self.filename_omb))
        plt.close(fig)


class VerticalProfile:
    """
    Creates a map with points colored by value
    Attributes:
        vert: an array of altitudes
        vals: an array of values for points' colors
        title: will be displayed above map figure and will name png file
        image_path: path to directory for saving the resulting images
    """

    # bin specifications
    min_alt = 0
    max_alt = 62000
    bin_size = 1000
    alt_bins = np.arange(min_alt, max_alt, bin_size)

    def __init__(self, diag, subject: str, image_path: str):
        self.vert = diag.vert
        self.vals = getattr(diag, subject) 
        self.subject = subject
        self.title = f"{diag.platform} bending_angle {subject} {diag.date}"
        self.image_path = image_path
        self.filename = f"{diag.platform}.bending_angle.{subject}.{re.sub('[^0-9]', '', diag.date)}.png"
        self.plot()

    def plot(self):

        # initialize the plot 
        fig = plt.figure(figsize=(18, 12))
        ax = plt.axes()
        plt.rcParams['font.size'] = '16'
        ax.set_ylim([self.min_alt, self.max_alt])

        # vertically bin data
        self.df = pd.DataFrame(list(zip(self.vals, self.vert)), columns = ['val' , 'vert'])
        self.df['binned'] = pd.cut(self.df['vert'], self.alt_bins, 
                                    labels = self.alt_bins[:-1] + (self.bin_size/2))
        self.profdf = self.df.groupby(self.df['binned']).apply(lambda g: g.mean(skipna=True))
        
        # scale by 1000 for mili-radians
        self.profdf['val'] = self.profdf['val']*1000


        print(self.profdf)

        #if self.subject == 'hofx' or self.subject == 'obs':
            # remove negative values
            #self.profdf['val'][self.profdf['val']<0] = 0
            # remove zeros
            #self.profdf.replace(0, np.nan, inplace=True)

        # line data
        # ax.set_xlim([np.nanmin(self.profdf['val']), np.nanmax(self.profdf['val'])])
        sc = ax.plot(self.profdf['val'], list(self.profdf.index), lw=2)
       
        # figure labels
        plt.title(self.title)
        ax.text(0.45, -0.1, 'Bending Angle (mili-radian)', transform=ax.transAxes, ha='left')
        ax.text(-0.08, 0.4, 'Altitude (m)', transform=ax.transAxes,
                rotation='vertical', va='bottom')

        # save plot
        if not os.path.isdir(self.image_path):
            os.makedirs(self.image_path)

        plt.savefig(os.path.join(self.image_path, self.filename))
        plt.close(fig)
