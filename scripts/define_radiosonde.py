#!/usr/bin/python

import numpy as np

def flatten(l):
    out = []
    for item in l:
        if isinstance(item, (list, tuple)):
            out.extend(flatten(item))
        else:
            out.append(item)
    return out

mandatory_levels = [ 1000, 925, 850, 700, 500, 400, 300, 
                     250, 200, 150, 100, 70, 50, 30, 20, 10, 5]
ly = {
       'num'  :  len(mandatory_levels)         ,
       'bins' :  np.array( mandatory_levels )  ,
       'mid_points'  : []                      }

for j, l in enumerate(mandatory_levels):
    if j == 0:
        ly['mid_points'].append(1100)
    else:
        log_mid = np.exp( np.sqrt(np.log(l)*np.log(ly['bins'][j-1])) )
        ly['mid_points'].append( log_mid )
ly['mid_points'].append(0)
ly['mid_points'] = np.array( ly['mid_points'] )


# get x-axis binning latitudinal --- values in degrees
lx = {'min':float(-90), 'max':float(90), 'bin':float(5)}
lx['num'] = int((lx['max']-lx['min'])/lx['bin'] + 1)
lx['bins'] = lx['min'] + np.arange(lx['num'])*lx['bin']

# WMO Common Code Table C-2: Radiosonde/Sounding System 
raob_type = {}

raob_type['VIZ'] = {  
              'VIZ A'     :  10,
              'VIZ B'     :  11,
              'VIZ Mark 1':  14,
              'VIZ B2'    :  51,
              'Mark 1'    :  21,
              'Mark 2'    :  49,
              'Valcom A'  :  31,
              'Valcom'    :  48,
              'LOCATE Loran-C'  :  38}


raob_type['Sippican'] = { 
             'MK2 GPS/STAR'    :  82, 
             'MK2 GPS/W9000'   :  83, 
             'MARK II/GPS'     :  84, 
             'MARK IIA/GPS'    :  85,
             'MARK II'         :  86, 
             'MARK IIA'        :  87}


raob_type['Vaisala 90s'] = { 
             'RS90'       :  [  71, 72, 73, 74, 78  ], 
             'RS92'       :  [  70, 79, 80, 81  ] }

raob_type['AVK/Vektor (Russia)'] = { 
             'AVK-MRZ'        :  27, 
             'AVK-RF95'       :  53, 
             'AVK-BAR'        :  58, 
             'AVK-RZM-2'      :  68, 
             'AVK-RF95-ARMA'  :  76, 
             'AVK-MRZ-ARMA'   :  75,
             'Vektor-M-RZM-2' :  69, 
             'Vektor-M-MRZ'   :  88, 
             'Vektor-M-BAR'   :  89 }

raob_type['various (Europe)'] = { 
             'Elin'          :  16, 
             'Graw-G'        :  17, 
             'Graw DFM-06'   :  18, 
             'Graw M60'      :  19, 
             'Graw DFM-90'   :  50, 
             'Graw DFM-97'   :  54, 
             'Mesural 1950A' :  23, 
             'Mesural 1945A' :  24, 
             'Mesural MH73A' :  25, 
             'Meteolabor Basora' :  26, 
             'UKMO MK3'      :  33, 
             'Sprenger E076' :  39, 
             'Sprenger E084' :  40, 
             'Sprenger E085' :  41, 
             'Sprenger E086' :  42, 
             'M2K2'          :  56, 
             'M2K2-DC'       :  57,
             'M2K2-R'        :  59,
             'GEOLINK GL98'  :  77 }

raob_type['RS (Japan)'] = { 
             'RS2-80'     :  [ 22, 30],
             'RS2-91'     :  47,
             'RS-016'     :  55} 

raob_type['BAT (S. Africa)'] = { 
             'BAT-16P'     :  97,
             'BAT-16G'     :  98,
             'BAT-4G'      :  99 }

raob_type['other (Vaisala RS18/RS21)'] = { 
             'RS18'       :  35,
             'RS21'       :  36}

raob_type['other (Vaisala 80s)'] = { 
             'RS80'       :  [  37, 52, 60, 61, 62, 63, 66, 67  ] }

raob_type['other (hi-Qual Vaisala 80s)'] = { }

raob_type['other Dropsonde'] = {
             'dropsonde'      :  96 }

raob_type['other (Unknown)'] = { 'unknown': [] }

raob_type['other (Czech)'] = { 
             'Vinohrady'  :  34} 

raob_type['other (Russia)'] = { 
             'Marz2-1'    :  28, 
             'Marz2-2'    :  29} 

raob_type['other (China)'] = { 
             'Shanghai Radio'  :  32}

raob_type['other (India)'] = { 
             'MK3'        :  20}

raob_type['other (Australia)'] = { 
             'Astor'      :  13}

raob_type['other (USA)'] = { 
              'OSC type 909-11-XX'  :   64,
              'VIZ 1499-520'        :   65 }

raob_type['profiler (unspecified)'] = { 
             'unspecified-1'  :   0,
             'unspecified-2'  :   8,
             'unspecified-3'  :   9,
             'unspecified-4'  :  90,
             'unspecified-5'  :  91,
             'unspecified-6'  :  92,
             'unspecified-7'  :  93,
             'unspecified-8'  :  94,
             'unspecified-9'  :  95 }

raob_type['profiler unspecified (hi-Qual)'] = { }

raob_type['profiler iMet (USA)'] = { 
             'iMet-1-BB'  :   1,
             'iMet-1-AB'  :   7 }

raob_type['profiler RS (USA)'] = { 
             'RS SDC'     :   12,
             'RS MSS'     :   45 }

raob_type['profiler EEC (USA)'] = { 
             'EEC type 23' :   15}

raob_type['profiler AIR (USA)'] = { 
              'IS-4A-1680'  :   43,
              'IS-4A-1680X' :   44,
              'IS-4A-403'   :   46}

raob_type['profiler active '] = { 
             'profiler'        :   5,
             'radio-acoustic'  :   6}

raob_type['profiler passive '] = { 
             'reflector'    :   2  ,
             'transponder'  :   3  ,
             'profiler'     :   4  }


raob_station = { 
        'High Quality' :
             {'Hi-Lat Europe'  : {
                     'search_string' :  [r'0[1-2]...'  , r'04...']  ,
                     'countries'     :  ['Norway', 'Sweden', 'Finland', 'Iceland', 'Greenland'] }, 
             'Mid-Lat Europe'  : {
                     'search_string' :  [r'03...'  , r'0[6-8]...', r'1[0-7]...']  , 
                     'countries'     :  ['UK', 'Faeroe Island', 'Denmark', 'Netherlands', 'Belgium', 'Switzerland', 
                                         'France', 'Spain', 'Portugal', 'Germany', 'Austria', 'Czech Republic', 
                                         'Slovakia', 'Poland', 'Hungary', 'Yugoslavia', 'Slovenia', 'Croatia', 
                                         'Romania', 'Bulgaria', 'Italy', 'Greece', 'Turkey', 'Cyprus']  }, 
             'Japan'  : {
                     'search_string' :  [r'47[4-9]..']  , 
                     'countries'     :  ['Japan']    } ,
             'Alaska and Canada'  : {
                     'search_string' :  [r'7[0-1]...']  , 
                     'countries'     :  ['US Alaska', 'Canada']    } ,
             'Antarctica'  : {
                     'search_string' :  [r'89...']  , 
                     'countries'     :  ['Antarctica']    },
             'US Conus'  : {
                     'search_string' :  [r'7[2-4]...']  , 
                     'countries'     :  ['Continental United States']    } ,
             'New Zealand and Australia'  : {
                     'search_string' :  [r'9[3-5]...']  , 
                     'countries'     :  ['New Zealand', 'Australia']    }  }, 
        'Unknown Quality' :
             {'Russia'  : {
                     'search_string' :  [r'[2-3]....']  , 
                     'countries'     :  ['Russia']    }, 
             'Middle East'  : {
                     'search_string' :  [r'4[0-1]...']  , 
                     'countries'     :  ['Syria', 'Lebanon', 'Israel', 'Jordan', 'Saudi Arabia', 'Kuwait', 'Iraq', 'Iran', 
                                  'Afghanistan', 'Qatar', 'United Arab Emirites', 'Oman', 'Yemen', 'Pakistan', 'Bangladesh'] },
             'Indian Subcontinent'  : {
                     'search_string' :  [r'4[2-3]...']  , 
                     'countries'     :  ['India', 'Sri Lanka', 'Maldives']    },
             'Taiwan and S Korea'  : {
                     'search_string' :  [r'46...', r'471..']  , 
                     'countries'     :  ['Taiwan', 'South Korea']    },
             'East Asia non-China'  : {
                     'search_string' :  [r'44...', r'45...', r'470..']  , 
                     'countries'     :  ['Mongolia', 'Nepal', 'Hong Kong', 'North Korea']    },
             'South Asia'  : {
                     'search_string' :  [r'48...']  , 
                     'countries'     :  ['Burma', 'Thailand', 'Malaysia', 'Kuala Lumpur', 'Singapore', 
                                         'Vietnam', 'Laos', 'Cambodia'] },
             'China'  : {
                     'search_string' :  [r'5....']  , 
                     'countries'     :  ['China']    },
             'Africa'  : {
                     'search_string' :  [r'6[0-7]...']  , 
                     'countries'     :  ['Africa not all listed']    },
             'South Africa'  : {
                     'search_string' :  [r'68...']  , 
                     'countries'     :  ['South Africa']    },
             'US Military various'  : {
                     'search_string' :  [r'690[0-1]..', r'690[5-9]..', r'69[1-6]...', r'697..']  , 
                     'countries'     :  ['US Military N America', 'US Military Europe', 'US Military Middle East']    },
             'Mexico and Central America'  : {
                     'search_string' :  [r'7[6-8]...']  , 
                     'countries'     :  ['Mexico', 'Central America not all listed']    },
             'South America'  : {
                     'search_string' :  [r'8[0-8]...']  , 
                     'countries'     :  ['South America not all listed']    },
             'Hawaii and Pacific Islands'  : {
                     'search_string' :  [r'9[1-2]...']  , 
                     'countries'     :  ['US Hawaii', 'Pacific Island not all listed']    },
             'South Pacific'  : {
                     'search_string' :  [r'9[6-8]...']  , 
                     'countries'     :  ['Indonesia', 'Philippines', 'South Pacific Island not all listed']    },
             'Ship Obs'  : {
                     'search_string' :  [r'99..[0-8]']  , 
                     'countries'     :  ['Ship obs not all listed']    },
             'Unknown'  : {
                     'search_string' :  [r'99999']  , 
                     'countries'     :  ['unknown']    }   }
}

known_raobs = []
for t in raob_type.keys():
    known_raobs.append(list(raob_type[t].values()))
known_raobs = flatten(known_raobs)

raob_types = len(list(raob_type.keys()))
sorted_raob_keys = sorted( raob_type.keys() )


# define variables within Raob observation and expected min/max for fg_depar values
var_coding = {  'Z'   :  {  'index' : 0                     , 
                            'name': 'geopotential height'   ,  
                            'min':  -50.0                   ,
                            'max':   50.0                   ,
                            'bin':   10.0                   ,
                            'unit': 'meters'                }       ,
                't'   :  {  'index' : 1                     , 
                            'name'  :  'temperature'        , 
                            'min':  -5.0                    ,
                            'max':   5.0                    ,
                            'bin':   1.0                    ,
                            'unit': 'Kelvin'                }       ,
                'u'   :  {  'index' : 2                     , 
                            'name'  :  'u-wind'             ,
                            'min':  -7.5                    ,
                            'max':   7.5                    ,
                            'bin':   2.5                    ,
                            'unit': 'm/s'                   }       ,
                'v'   :  {  'index' : 3                     , 
                            'name'  :  'v-wind'             ,
                            'min':  -7.5                    ,
                            'max':   7.5                    ,
                            'bin':   2.5                    ,
                            'unit': 'm/s'                   }       ,
                'q'   :  {  'index' : 4                     , 
                            'name'  :  'specific_humidity' ,
                            'min': -3.0                    ,
                            'max':  3.0                    ,
                            'bin':  1.0                    ,
                            'unit': 'g/kg'                  }       }
var_types = len(list(var_coding.keys()))
# sort the var_coding keys by index
get_index = lambda k : var_coding[k]['index']
sorted_var_keys = sorted( var_coding, key=get_index )


sub_domains = { 'northern hemisphere' : 
                          { 'lat_range': [20,80],
                            'lx_index':  [],
                            'title'    : 'NH' },
                'southern hemisphere' : 
                          { 'lat_range': [-80,-20],
                            'lx_index':  [],
                            'title'    : 'SH' },
                'tropics' : 
                          { 'lat_range': [-20,20],
                            'lx_index':  [],
                            'title'    : 'Trop' },
                'southern polar' : 
                          { 'lat_range': [-90,-80],
                            'lx_index':  [],
                            'title'    : 'SP' },
                'northern polar' : 
                          { 'lat_range': [80,90],
                            'lx_index':  [],
                            'title'    : 'NP' },
                'global' : 
                          { 'lat_range': [-90,90],
                            'lx_index':  [],
                            'title'    : 'Glb' },
}

for domain in sub_domains:
    sub_domains[domain]['lx_index'].append( np.where(lx['bins'] == sub_domains[domain]['lat_range'][0] )[0][0] )
    sub_domains[domain]['lx_index'].append( np.where(lx['bins'] == sub_domains[domain]['lat_range'][1] )[0][0] )
