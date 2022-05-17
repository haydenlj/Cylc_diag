#!/bin/ksh
################################################################################
 set -x

USE_METASCHEDULAR=${USE_METASCHEDULAR:-F}

if [[ ${USE_METASCHEDULAR} == F ]]; then
  source ${SCRIPT_DIR}/setupfv3.sh
  export PDY=$(echo $CDATE | cut -c1-8)
  export cyc=$(echo $CDATE | cut -c9-10)
  DATA=${TOP_DIR}/fv3scratch/${EXPT}
  ROTDIR=${TOP_DIR}/run/${EXPT}/
  savedir=${ROTDIR}/${CDATE}/atmos
fi

OUTPUT_FILETYPE=${OUTPUT_FILETYPE:-"netcdf"}

# Model config options
export MEMBER=${MEMBER:-"-1"}  # deterministic
[[ "$OUTPUT_FILETYPE" = "netcdf" ]] && affix="nc"
#-------------------------------------------------------
if [ ! -d $ROTDIR ]; then mkdir -p $ROTDIR; fi
mkdata=NO
if [ ! -d $DATA ]; then
   mkdata=YES
   mkdir -p $DATA
fi
cd $DATA || exit 8
if [ ! -d $DATA/INPUT ]; then
  mkdir -p $DATA/INPUT
else
  rm $DATA/INPUT/*
fi
if [ ! -d $DATA/RESTART ]; then
  mkdir -p $DATA/RESTART
else
  rm $DATA/RESTART/*
fi
#-------------------------------------------------------
if [ ! -d $savedir ]; then mkdir -p $savedir; fi

GDATE=$PREDATE
gPDY=${yyyymmdd_pre}
gcyc=${hh_pre}

if [ $cycling = .true. ]; then
  icdir=$ROTDIR/${CDATE}/da/output/
else
  icdir=$ROTDIR/${GDATE}/atmos
fi

# sfc feed from sfcanl
#sCDATE=$( date -u --date="-3 hours ${CDATE:0:4}-${CDATE:4:2}-${CDATE:6:2} ${CDATE:8:2}" +%Y%m%d%H )
sPDY=$PDY
scyc=$cyc
#-------------------------------------------------------

# Link all (except sfc_data) restart files from $icdir
for file in $(ls $icdir/RESTART/${PDY}.${cyc}0000.*.nc); do
  file2=$(echo $(basename $file))
  file2=$(echo $file2 | cut -d. -f3-) # remove the date from file
  fsuf=$(echo $file2 | cut -d. -f1)
  if [ $fsuf != "sfc_data" ]; then
     $NLN $file $DATA/INPUT/$file2
  fi
done

if [ $CDATE -gt $INIT_DATE ]; then
  $NLN $ROTDIR/${GDATE}/atmos/RESTART/${PDY}.${cyc}0000.fv_core.res.nc $DATA/INPUT/fv_core.res.nc
else
  $NLN ${PREP_DATA_DIR}/IC_${NPZ}/${PREDATE}/RESTART/${PDY}.${cyc}0000.fv_core.res.nc $DATA/INPUT/fv_core.res.nc
fi

# Link sfcanl_data restart files from source with cycling date info
# for file in $(ls ${sfcfeed}/${sPDY}.${scyc}0000.*.nc); do
#   file2=$(echo $(basename $file))
#   file2=$(echo $file2 | cut -d. -f3-) # remove the date from file
#   fsufanl=$(echo $file2 | cut -d. -f1)
#   if [ $fsufanl = "sfcanl_data" ] ||  [ $fsufanl = "sfc_data" ]; then
#     file2=$(echo $file2 | sed -e "s/sfcanl_data/sfc_data/g")
#     $NLN $file $DATA/INPUT/$file2
#   fi
# done
 
# Link sfc_data restart files from source without date
if [[ ${USE_METASCHEDULAR} == F ]]; then
for file in $(ls ${sfcfeed}/sfc*nc); do
  file2=$(echo $(basename $file))
  fsufanl=$(echo $file2 | cut -d. -f1)
  if [ $fsufanl = "sfcanl_data" ] ||  [ $fsufanl = "sfc_data" ]; then
    file2=$(echo $file2 | sed -e "s/sfcanl_data/sfc_data/g")
    $NLN $file $DATA/INPUT/$file2
  fi
done
fi

nfiles=$(ls -1 $DATA/INPUT/* | wc -l)
if [ $nfiles -le 0 ]; then
  echo "Initial conditions must exist in $DATA/INPUT, ABORT!"
  msg="Initial conditions must exist in $DATA/INPUT, ABORT!"
  postmsg "$jlogfile" "$msg"
  exit 1
fi
#--------------------------------------------------------------------------
# Grid and orography data
for n in $(seq 1 $ntiles); do
  $NLN $FIXfv3/$CASE/${CASE}_grid.tile${n}.nc     $DATA/INPUT/${CASE}_grid.tile${n}.nc
  $NLN $FIXfv3/$CASE/${CASE}_oro_data.tile${n}.nc $DATA/INPUT/oro_data.tile${n}.nc
done
$NLN $FIXfv3/$CASE/${CASE}_mosaic.nc  $DATA/INPUT/grid_spec.nc

if [ ${new_o3forc:-YES} = YES ]; then
    O3FORC=ozprdlos_2015_new_sbuvO3_tclm15_nuchem.f77
else
    O3FORC=global_o3prdlos.f77
fi
H2OFORC=${H2OFORC:-"global_h2o_pltc.f77"}

$NLN $FIX_AM/${O3FORC}                         $DATA/global_o3prdlos.f77
$NLN $FIX_AM/${H2OFORC}                        $DATA/global_h2oprdlos.f77
$NLN $FIX_AM/global_solarconstant_noaa_an.txt  $DATA/solarconstant_noaa_an.txt
$NLN $FIX_AM/global_sfc_emissivity_idx.txt     $DATA/sfc_emissivity_idx.txt

$NLN $FIX_AM/global_co2historicaldata_glob.txt $DATA/co2historicaldata_glob.txt
$NLN $FIX_AM/co2monthlycyc.txt                 $DATA/co2monthlycyc.txt
if [ $ICO2 -gt 0 ]; then
  for file in $(ls $FIX_AM/fix_co2_proj/global_co2historicaldata*) ; do
    $NLN $file $DATA/$(echo $(basename $file) | sed -e "s/global_//g")
  done
fi

$NLN $FIX_AM/global_climaeropac_global.txt     $DATA/aerosol.dat
if [ $IAER -gt 0 ] ; then
  for file in $(ls $FIX_AM/global_volcanic_aerosols*) ; do
    $NLN $file $DATA/$(echo $(basename $file) | sed -e "s/global_//g")
  done
fi

# the pre-conditioning of the solution
# =0 implies no pre-conditioning
# >0 means new adiabatic pre-conditioning
# <0 means older adiabatic pre-conditioning
na_init=${na_init:-1}
[[ $warm_start = ".true." ]] && export na_init=0

if [ ${TYPE} = "nh" ]; then # non-hydrostatic options
  hydrostatic=".false."
  phys_hydrostatic=".false."     # enable heating in hydrostatic balance in non-hydrostatic simulation
  use_hydro_pressure=".false."   # use hydrostatic pressure for physics
  if [ $warm_start = ".true." ]; then
    make_nh=".false."              # restarts contain non-hydrostatic state
  else
    make_nh=".true."               # re-initialize non-hydrostatic state
  fi
fi

if [ $(echo $MONO | cut -c-4) = "mono" ];  then # monotonic options
  export d_con=${d_con_mono:-"0."}
  export do_vort_damp=".false."
  if [ ${TYPE} = "nh" ]; then # non-hydrostatic
    export hord_mt=${hord_mt_nh_mono:-"10"}
    export hord_xx=${hord_xx_nh_mono:-"10"}
  fi
else # non-monotonic options
  export d_con=${d_con_nonmono:-"1."}
  export do_vort_damp=".true."
  if [ ${TYPE} = "nh" ]; then # non-hydrostatic
    export hord_mt=${hord_mt_nh_nonmono:-"5"}
    export hord_xx=${hord_xx_nh_nonmono:-"5"}
  fi
fi

#if [ $(echo $MONO | cut -c-4) != "mono" -a $TYPE = "nh" ]; then
 # export vtdm4=${vtdm4_nh_nonmono:-"0.06"}
#else
#  export vtdm4=${vtdm4:-"0.05"}
#fi

if [ $warm_start = ".true." ]; then # warm start from restart file
  export nggps_ic=".false."
  export ncep_ic=".false."
  export external_ic=".false."
  export mountain=".true."
fi

# Stochastic Physics Options
if [ ${SET_STP_SEED:-"YES"} = "YES" ]; then
  ISEED_SKEB=$((CDATE*1000 + MEMBER*10 + 1))
  ISEED_SHUM=$((CDATE*1000 + MEMBER*10 + 2))
  ISEED_SPPT=$((CDATE*1000 + MEMBER*10 + 3))
else
  ISEED=${ISEED:-0}
fi
DO_SKEB=${DO_SKEB:-"NO"}
DO_SPPT=${DO_SPPT:-"NO"}
DO_SHUM=${DO_SHUM:-"NO"}

if [ $DO_SKEB = "YES" ]; then
    do_skeb=".true."
fi
if [ $DO_SHUM = "YES" ]; then
    do_shum=".true."
fi
if [ $DO_SPPT = "YES" ]; then
    do_sppt=".true."
fi
# build the diag_table with the experiment name and date stamp
cat > diag_table << EOF
FV3 Forecast
${sPDY:0:4} ${sPDY:4:2} ${sPDY:6:2} ${scyc} 0 0
EOF
cat $DIAG_TABLE >> diag_table

$NCP $DATA_TABLE  data_table
$NCP $FIELD_TABLE field_table

#------------------------------------------------------------------
if [ $cplwav = ".false." ]; then
  cp ${TEMPLATE_DIR}/nems.configure .
else
  sh ${TEMPLATE_DIR}/template_nems_configure.sh 
fi

sh ${TEMPLATE_DIR}/template_model_configure.sh

atmos_model_nml=""
if [ $RUN_CCPP = "YES" ]; then
 atmos_model_nml="ccpp_suite = $CCPP_SUITE"
fi
sh ${TEMPLATE_DIR}/template_input_nml.sh
#------------------------------------------------------------------
# make symbolic links to write forecast files directly in savedir
cd $DATA
if [ $QUILTING = ".true." -a $OUTPUT_GRID = "gaussian_grid" ]; then
  fhr=$FHMIN
  while [ $fhr -le $FHMAX ]; do
    FH3=$(printf %03i $fhr)
    FH2=$(printf %02i $fhr)
    atmi=atmf${FH3}.$affix
    sfci=sfcf${FH3}.$affix
    logi=logf${FH3}
    pgbi=GFSPRS.GrbF${FH2}
    flxi=GFSFLX.GrbF${FH2}
    atmo=$savedir/${CDUMP}.t${cyc}z.atmf${FH3}.$affix
    sfco=$savedir/${CDUMP}.t${cyc}z.sfcf${FH3}.$affix
    logo=$savedir/${CDUMP}.t${cyc}z.logf${FH3}.txt
    pgbo=$savedir/${CDUMP}.t${cyc}z.master.grb2f${FH3}
    flxo=$savedir/${CDUMP}.t${cyc}z.sfluxgrbf${FH3}.grib2
    eval $NLN $atmo $atmi
    eval $NLN $sfco $sfci
    eval $NLN $logo $logi
    if [ $WRITE_DOPOST = ".true." ]; then
      eval $NLN $pgbo $pgbi
      eval $NLN $flxo $flxi
    fi
    FHINC=$FHOUT
    if [ $FHMAX_HF -gt 0 -a $FHOUT_HF -gt 0 -a $fhr -lt $FHMAX_HF ]; then
      FHINC=$FHOUT_HF
    fi
    fhr=$((fhr+FHINC))
  done
fi

#------------------------------------------------------------------
if [[ ${USE_METASCHEDULAR} == T ]]; then
  sh ${TEMPLATE_DIR}/template_fcst_job.sh fcst
  exit 0
fi
sh ${TEMPLATE_DIR}/template_fv3_job.sh fcst
sbatch job.sh
sh ${SCRIPT_DIR}/checkfile.sh $DATA/RESTART/fv_core.res.tile6.nc
sh ${SCRIPT_DIR}/checkfile.sh $DATA/RESTART/coupler.res
sh ${SCRIPT_DIR}/checkfile.sh $DATA/RESTART/phy_data.tile1.nc
#------------------------------------------------------------------
if [ $SEND = "YES" ]; then

  # Copy gdas and enkf member restart files
  if [ $CDUMP = "gdas" -a $rst_invt1 -gt 0 ]; then
    cd $DATA/RESTART
    mkdir -p $savedir/RESTART
    for rst_int in $restart_interval ; do
     if [ $rst_int -ge 0 ]; then
       RDATE=$(date -u --date="${rst_int} hours ${CDATE:0:4}-${CDATE:4:2}-${CDATE:6:2} ${CDATE:8:2}" +%Y%m%d%H )
       rPDY=$(echo $RDATE | cut -c1-8)
       rcyc=$(echo $RDATE | cut -c9-10)
       for file in $(ls ${rPDY}.${rcyc}0000.*) ; do
         $NCP $file $savedir/RESTART/$file
       done
       if [ $rst_int -eq $FHMAX ]; then
       # need to rename some files and then copy
         $NCP coupler.res $savedir/RESTART/${rPDY}.${rcyc}0000.coupler.res
         $NCP fv_core.res.nc $savedir/RESTART/${rPDY}.${rcyc}0000.fv_core.res.nc
         for file in $(ls fv_core.res.tile*) ; do
           $NCP $file $savedir/RESTART/${rPDY}.${rcyc}0000.$file
         done
         for file in $(ls fv_tracer.res.tile*) ; do
           $NCP $file $savedir/RESTART/${rPDY}.${rcyc}0000.$file
         done
         for file in $(ls phy_data.tile*) ; do
           $NCP $file $savedir/RESTART/${rPDY}.${rcyc}0000.$file
         done
         for file in $(ls sfc_data.tile*) ; do
           $NCP $file $savedir/RESTART/${rPDY}.${rcyc}0000.$file
         done
         for file in $(ls fv_srf_wnd.res.tile*) ; do
           $NCP $file $savedir/RESTART/${rPDY}.${rcyc}0000.$file
         done
       fi
     fi
    done
  fi
fi
