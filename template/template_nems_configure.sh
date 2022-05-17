###-------------------------------------------------------------
if [ -e nems.configure] rm -f nems.configure

if [ $cplwav = ".true." ]; then ## ww3 version of nems.configure

# Switch on cpl flag
cpl=.true.
NTASKS_FV3m1=$((NTASKS_FV3-1))
atm_petlist_bounds=" 0 $((NTASKS_FV3-1))"
wav_petlist_bounds=" $((NTASKS_FV3)) $((NTASKS_FV3m1+npe_wav))"
###  atm_petlist_bounds=" 0   1511"
###  atm_petlist_bounds=$atm_petlist_bounds
###  wav_petlist_bounds="1512 1691"
###  wav_petlist_bounds=$wav_petlist_bounds
coupling_interval_sec=${coupling_interval_sec:-1800}

cat > nems.configure <<EOF
EARTH_component_list: ATM WAV
EARTH_attributes::
  Verbosity = high
  HierarchyProtocol = off
::

ATM_model:                      fv3
ATM_petlist_bounds:             ${atm_petlist_bounds}
ATM_attributes::
  Verbosity = 0
  DumpFields = false
::

WAV_model:                      ww3
WAV_petlist_bounds:             ${wav_petlist_bounds}
WAV_attributes::
  Verbosity = high
::

runSeq::
  @${coupling_interval_sec}
    ATM
    ATM -> WAV :SrcTermProcessing=0:TermOrder=SrcSeq
    WAV
  @
::
EOF


else  ## fv3 standalone version of nems.configure
cat > nems.configure <<EOF
EARTH_component_list: ATM
ATM_model:            fv3
runSeq::
  ATM
::
EOF
fi
