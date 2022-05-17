#!/bin/sh

atime=${atime:-20220204T06Z_PT6H}
dtg=${DTG:-2022020412}

ztypes=(
aircraft
)
#atms_n20
#radiosonde
#gdas_gnssro

source /work/noaa/da/jedipara/ewok/bin/ewok
cd ${SCRATCH}/${dtg}/Data
for atype in ${ztypes[@]}; do 
    afile=${atime}_${atype}.nc4
    python ${DATA_REPOS}/ioda/MergeIODA_hofx.py -i ${atime}_${atype}_[0-9][0-9][0-9][0-9].nc4 -o ${afile}
done
unset_ewok
