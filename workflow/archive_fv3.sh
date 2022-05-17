#!/bin/sh
#set -x

# cp fv3 forecast from run directory ($DATA/RESTART) to save directory ($savedir)
# this script is intended to be used as part of cylc suite scripts and 
# replaces a similar section inside run_fv3.sh (by H. Zhang 202111)
# H.Shao 202203


  # Copy gdas and enkf member restart files
  if [ $CDUMP = "gdas" -a $rst_invt1 -gt 0 ]; then
    cd $DATA/RESTART
    mkdir -p $savedir/RESTART
    for rst_int in $restart_interval ; do
     if [ $rst_int -ge 0 ]; then
       RDATE=$(date -u --date="${rst_int} hours ${CDATE:0:4}-${CDATE:4:2}-${CDATE:6:2} ${CDATE:8:2}" +%Y%m%d%H )
       rPDY=${RDATE:0:8}
       rcyc=${RDATE:8:2}
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

