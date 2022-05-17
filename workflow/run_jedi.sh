#!/bin/sh -f
source  ./setupjedi.sh

export  rundir=${TOP_DIR}/run/${EXPT}/${CDATE}/da

if [ ! -d $rundir ]; then mkdir -p $rundir; fi
cd $rundir 
export  hofxout=${rundir}/output/hofx
export  analysisout=${rundir}/output/RESTART
export  satbiasout=${rundir}/output/satbias

if [ ! -d ${hofxout} ]; then mkdir -p ${hofxout}; fi
if [ ! -d ${analysisout} ]; then  mkdir -p ${analysisout}; fi
if [ ! -d ${satbiasout} ]; then  mkdir -p ${satbiasout}; fi

sh ${TEMPLATE_DIR}/template_${DAmethod}_yaml.sh "${OPTS[@]}"

if [ $DAmethod != "3dvar" ]; then ln -sf ${BUMP_DIR}/${BUMP_name} . ; fi

sh  ${TEMPLATE_DIR}/template_jedi_job_on_orion.sh  job_${DAmethod}_${CDATE}.sh ${DAmethod} fv3jedi_var.x

sbatch job_${DAmethod}_${CDATE}.sh

sh ${SCRIPT_DIR}/checkfile.sh ${analysisout}/${yyyy}${mm}${dd}.${hh}0000.fv_core.res.tile1.nc
sh ${SCRIPT_DIR}/checkfile.sh ${analysisout}/${yyyy}${mm}${dd}.${hh}0000.fv_core.res.tile2.nc
sh ${SCRIPT_DIR}/checkfile.sh ${analysisout}/${yyyy}${mm}${dd}.${hh}0000.fv_core.res.tile3.nc
sleep 30
