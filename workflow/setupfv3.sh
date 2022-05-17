#!/bin/sh
set -x

# set up fv3 forecast
# H.Zhang 202111
# https://github.com/NOAA-EMC/global-workflow/blob/develop/parm/config/config.fv3
# update to 127-level version
# H.Zhang 202202

USE_METASCHEDULAR=${USE_METASCHEDULAR:-F}

if [[ ${USE_METASCHEDULAR} == F ]]; then
    source ./setup.sh
fi

###  format, output config
###  -------------------------------------------------------------
export CDUMP=gdas
export rCDUMP=$CDUMP

#-  Surface cycle update frequency; CDUMP dependent
export FHCYC=1 
export FTSFS=10
export rst_invt1=3
export NTHREADS_FV3=1
export print_esmf=.false.
export OUTPUT_GRID="gaussian_grid"
export OUTPUT_FILETYPES="netcdf"
export WRITE_NEMSIOFLIP=".true."
export WRITE_FSYNCFLAG=".true."
export WRITE_DOPOST=".false."
export affix="nc"
export QUILTING=".true."
export print_freq=6
export restart_interval='6 -1'
export FHMAX=6    # maximal forecast time for output.
export FHOUT=6    # Output frequency during forecast time from 0 to fhmax
export FHMAX_HF=0 # The maximal forecast hour for high frequency output
export FHOUT_HF=1 # Output frequency during forecast time from 0 to fhmaxhf hour
export NSOUT=-1
export FHMIN=0
export FHINC=6
export IAU_FHROT=0
###  -------------------------------------------------------------
###  format, output config

###  Model configuration
###  -------------------------------------------------------------
export warm_start=.true.
export TYPE="nh"
export MONO="non-mono"
export cplwav=".false."
export RUN_CCPP=NO

#- TYPE dependent
export hydrostatic=".false."
export phys_hydrostatic=".false." 
export use_hydro_pressure=".false."

if [ $warm_start = ".true." ]; then
  export make_nh=".false." # restarts contain non-hydrostatic state
else
  export  make_nh=".true."  # re-initialize non-hydrostatic state
fi
###  -------------------------------------------------------------
###  Model configuration 

### CASE config
###  -------------------------------------------------------------
#- fv3 layout and computing resource 
export ntiles=6
export layout_x=6
export layout_y=6
export NNODE=16
export TASKS_PER_NODE=16
export WRTTASK_PER_GROUP=40
export NTASKS_FV3=$((layout_x*layout_y*6+WRTTASK_PER_GROUP))
export cores_per_node=40
#- mountain blocking, ogwd, cgwd, cgwd src scaling
export cdmbgwd=1.1,0.72,1.0,1.0

#- CASE DEPENDENT config
export DELTIM=240
export k_split=2
export n_split=6

#- spectral truncation and regular grid resolution based on FV3 resolution 
res=$(echo $CASE |cut -c2-5)
resp=$((res+1))
export npx=$resp
export npy=$resp
export JCAP_CASE=$((2*res-2))
export LONB_CASE=$((4*res))
export LATB_CASE=$((2*res))
export JCAP=${JCAP:-$JCAP_CASE}
export LONB=${LONB:-$LONB_CASE}
export LATB=${LATB:-$LATB_CASE}
export LONB_IMO=${LONB_IMO:-$LONB_CASE}
export LATB_JMO=${LATB_JMO:-$LATB_CASE}
## to remove export npz=64
LEVS=$((NPZ+1))
export LEVS=$LEVS
###  -------------------------------------------------------------
### CASE config

# executables and fix files
export HOMEgfs=/work/noaa/da/cmartin/noscrub/UFO_eval/global-workflow
export FCSTEXECDIR=$HOMEgfs/sorc/fv3gfs.fd/NEMS/exe
export FCSTEXEC=global_fv3gfs.x
export FIX_DIR=/work2/noaa/da/hailingz/work/fv3-workflow/fix
export FIX_AM=${FIX_DIR}/fix_am
export FIXfv3=${FIX_DIR}/fix_fv3_gmted2010
export PARMgfs=${HOMEgfs}/parm
export PARM_POST=${PARMgfs}/post
export PARM_FV3DIAG=${PARMgfs}/parm_fv3diag
export FIXgfs=${HOMEgfs}/fix
export USHgfs=${HOMEgfs}/ush
export UTILgfs=${HOMEgfs}/util
export EXECgfs=${HOMEgfs}/exec
export SCRgfs=${HOMEgfs}/scripts
export FNGLAC="$FIX_AM/global_glacier.2x2.grb"
export FNGLAC="$FIX_AM/global_glacier.2x2.grb"
export FNMXIC="$FIX_AM/global_maxice.2x2.grb"
export FNTSFC="$FIX_AM/RTGSST.1982.2012.monthly.clim.grb"
export FNSNOC="$FIX_AM/global_snoclim.1.875.grb"
export FNZORC="igbp"
export FNALBC2="$FIX_AM/global_albedo4.1x1.grb"
export FNAISC="$FIX_AM/CFSR.SEAICE.1982.2012.monthly.clim.grb"
export FNTG3C="$FIX_AM/global_tg3clim.2.6x1.5.grb"
export FNVEGC="$FIX_AM/global_vegfrac.0.144.decpercent.grb"
export FNMSKH="$FIX_AM/global_slmask.t1534.3072.1536.grb"
export FNVMNC="$FIX_AM/global_shdmin.0.144x0.144.grb"
export FNVMXC="$FIX_AM/global_shdmax.0.144x0.144.grb"
export FNSLPC="$FIX_AM/global_slope.1x1.grb"
export FNALBC="$FIX_AM/global_snowfree_albedo.bosu.t${JCAP}.${LONB}.${LATB}.rg.grb"
export FNVETC="$FIX_AM/global_vegtype.igbp.t${JCAP}.${LONB}.${LATB}.rg.grb"
export FNSOTC="$FIX_AM/global_soiltype.statsgo.t${JCAP}.${LONB}.${LATB}.rg.grb"
export FNABSC="$FIX_AM/global_mxsnoalb.uariz.t${JCAP}.${LONB}.${LATB}.rg.grb"
export FNSMCC="$FIX_AM/global_soilmgldas.statsgo.t${JCAP}.${LONB}.${LATB}.grb"
[[ ! -f $FNALBC ]] && FNALBC="$FIX_AM/global_snowfree_albedo.bosu.t1534.3072.1536.rg.grb"
[[ ! -f $FNVETC ]] && FNVETC="$FIX_AM/global_vegtype.igbp.t1534.3072.1536.rg.grb"
[[ ! -f $FNSOTC ]] && FNSOTC="$FIX_AM/global_soiltype.statsgo.t1534.3072.1536.rg.grb"
[[ ! -f $FNABSC ]] && FNABSC="$FIX_AM/global_mxsnoalb.uariz.t1534.3072.1536.rg.grb"
# executables and fix files

#fv3 tables
export DIAG_TABLE=$PARM_FV3DIAG/diag_table
export DATA_TABLE=$PARM_FV3DIAG/data_table
export FIELD_TABLE=$PARM_FV3DIAG/field_table_gfdl_satmedmf
#fv3 tables

# model configure
  # output and format
export OUTPUT_GRID="gaussian_grid"
export OUTPUT_FILETYPES="netcdf"
export WRITE_NEMSIOFLIP=".true."
export WRITE_FSYNCFLAG=".true."
export WRITE_DOPOST=".false."
export affix="nc"  
export QUILTING=".true."
export print_freq=6
# model configure


###  input.nml config 
###  ----------------------------------------------------------------
export do_ugwp=.false. 
export do_tofd=.true.
export n_sponge=42

#- LEVS dependent config (64)
export d2_bg_k1=0.20
export d2_bg_k2=0.04
export tau=10.0
export rf_cutoff=7.5e2
if [ $LEVS = "128" -a "$CDUMP" = "gdas" ]; then
   export  d2_bg_k1=0.20
   export  d2_bg_k2=0.0
   export  tau=5.0
   export  rf_cutoff=1.0e3
fi

#- PBL/turbulance schemes
export hybedmf=".false."
export satmedmf=".true."
export isatmedmf=1
tbf=""
if [ $satmedmf = ".true." ]; then tbf="_satmedmf" ; fi

#- Land surface model. (2--NoahMP, landice=F); (1--Noah, landice=T)
export lsm=1

#- Radiation options 
export IAER=5111    #spectral band mapping method for aerosol optical properties
export ICO2=2
export iovr_lw=3    #de-correlation length cloud overlap method (Barker, 2008) 
export iovr_sw=3    #de-correlation length cloud overlap method (Barker, 2008) 
export iovr=3       #de-correlation length cloud overlap method (Barker, 2008) 
export icliq_sw=2   #cloud optical coeffs from AER's newer version v3.9-v4.0 for hu and stamnes

#- Microphysics configuration
export dnats=0
export cal_pre=".true."
export do_sat_adj=".false."
export random_clds=".true."
  #-- imp_physics Options: 99-ZhaoCarr, 8-Thompson; 6-WSM6, 10-MG, 11-GFDL
export imp_physics=11
    #-- imp_physics dependent (11)
export ncld=5
export FIELD_TABLE="$HOMEgfs/parm/parm_fv3diag/field_table_gfdl${tbf}"
export nwat=6
export dnats=1
export cal_pre=".false."
export do_sat_adj=".true."
export random_clds=".false."
export lgfdlmprad=".true."
export effr_in=".true."
export reiflag=2
export hord_mt_nh_nonmono=5
export hord_xx_nh_nonmono=5
export vtdm4_nh_nonmono=0.02
export nord=2
export dddmp=0.1
export d4_bg=0.12
export vtdm4=0.02

#- IAU related parameters
export DOIAU="NO"        # diable 4DIAU 

#- NSST parameters contained within nstf_name
export NST_MODEL=2
export NST_SPINUP=0  # 1 if prior to 2017072000
export NST_RESV=0
export ZSEA1=0
export ZSEA2=0
export nstf_name=${nstf_name:-"$NST_MODEL,$NST_SPINUP,$NST_RESV,$ZSEA1,$ZSEA2"}
export nst_anl=".true."  # .true. or .false., NSST analysis over lake
export NST_GSI=3
export NSTINFO=0
if [ $NST_GSI -gt 0 ]; then export NSTINFO=4; fi

#- Stochastic physics parameters (only for ensemble forecasts)
  #-- set to false for deterministic run
export do_sppt=.false.
export do_shum=.false.
export do_skeb=.false.

###  ----------------------------------------------------------------
###  input.nml config 
