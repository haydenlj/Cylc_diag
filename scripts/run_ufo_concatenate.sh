#!/bin/sh

atime=${atime:-20220204T06Z_PT6H}
dtg=$1

ztypes=(
atms_n20_output
radiosonde
aircraft
satwind
gnssro_NBAM
)

source /work/noaa/da/jedipara/ewok/bin/ewok
cd ${SCRATCH}/${dtg}/da/output/hofx/
for atype in ${ztypes[@]}; do 
    afile=${SCRATCH}/${dtg}/Data/${atype}_${dtg}.nc4
    python /work/noaa/da/bruston/data_repos/ioda/MergeIODA_hofx.py -i ${atype}_${dtg}_[0-9][0-9][0-9][0-9].nc4 -o ${afile}
done
unset_ewok
