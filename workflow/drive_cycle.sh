#!/bin/sh
source  ./setupjedi.sh

export SDATE=2021080400
export EDATE=2021080400

export CDATE=$SDATE
while (( $CDATE <= $EDATE )); do
  export yyyy=${CDATE:0:4}
  export mm=${CDATE:4:2}
  export dd=${CDATE:6:2}
  export hh=${CDATE:8:2}
  export PREDATE=$( date -u --date="-${assim_freq} hours ${CDATE:0:4}-${CDATE:4:2}-${CDATE:6:2} ${CDATE:8:2}" +%Y%m%d%H )
  export yyyymmdd_pre=${PREDATE:0:8}
  export hh_pre=${PREDATE:8:2}

# run DA
#  --- background is needed from data feed in the first cycle
  if [ $CDATE -eq $INIT_DATE ]; then
     export BKG_path=${INPUT_DATA_DIR}/c${RES}_gdas/gdas.${yyyymmdd_pre}/${hh_pre}//atmos/RESTART
  else
     export BKG_path=${TOP_DIR}/run/${EXPT}/${PREDATE}/atmos/RESTART
  fi
  export ENS_path=${INPUT_DATA_DIR}/ensemble/c${RES}/enkfgdas.${yyyy}${mm}${dd}/${hh}/atmos
  sh run_jedi.sh $CDATE

#  run the NWP model
#  --- sfcfeed
#      surface files are updated from gdas restart files. note: resolution 
#   export sfcfeed=${INPUT_DATA_DIR}/restart/gdas.${yyyy}${mm}${dd}/${hh}//atmos/RESTART
#      surface files are updated from ensemble files 
  export sfcfeed=${ENS_path}/mem001/COLD
  sleep 20
  sh run_fv3.sh $CDATE

# advance date
  export CDATE=$(date -u --date="${assim_freq} hours ${CDATE:0:4}-${CDATE:4:2}-${CDATE:6:2} ${CDATE:8:2}" +%Y%m%d%H )
done
