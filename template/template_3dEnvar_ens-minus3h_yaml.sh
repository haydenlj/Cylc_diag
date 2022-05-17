echo "generating 3denvar yaml file"

yaml=${DAmethod}.yaml
[[ -e $yaml ]] && rm -f $yaml

# should the 3 hours come from assim win?
BGNDATE=$( date -u --date="-3 hours ${CDATE:0:4}-${CDATE:4:2}-${CDATE:6:2} ${CDATE:8:2}" +%Y%m%d%H )
yyyy_b=${yyyy:-${BGNDATE:0:4}}
mm_b=${mm:-${BGNDATE:4:2}}
dd_b=${dd:-${BGNDATE:6:2}}
hh_b=${hh:-${BGNDATE:8:2}}

yyyy=${yyyy:-${CDATE:0:4}}
mm=${mm:-${CDATE:4:2}}
dd=${dd:-${CDATE:6:2}}
hh=${hh:-${CDATE:8:2}}

dtg=${dtg:-${yyyy}${mm}${dd}.${hh}0000}
dtg_e=${dtg_e:-${yyyy}${mm}${dd}.${hh}0000}

cat > $yaml << EOF
cost function:
  cost type: 3D-Var
  window begin: '${yyyy_b}-${mm_b}-${dd_b}T${hh_b}:00:00Z'
  window length: PT6H
  analysis variables: &3dvars [ua,va,t,ps,sphum,liq_wat,o3mr]
  geometry:
    fms initialization:
       namelist filename: ${JEDIsrc}/fv3-jedi/test/Data/fv3files/fmsmpp.nml
       field table filename: ${JEDIsrc}/fv3-jedi/test/Data/fv3files/field_table_gfdl
    akbk: ${JEDIsrc}/fv3-jedi/test/Data/fv3files/akbk${NPZ}.nc4
    layout: [$layout,$layout]
    io_layout: [1,1]
    npx: $RESP
    npy: $RESP
    npz: $NPZ
    ntiles: 6
    fieldsets:
    - fieldset: ${JEDIsrc}/fv3-jedi/test/Data/fieldsets/dynamics.yaml
    - fieldset: ${JEDIsrc}/fv3-jedi/test/Data/fieldsets/ufo.yaml
  background:
    filetype: gfs
    datapath: ${BKG_path}
    filename_core: ${dtg}.fv_core.res.nc
    filename_trcr: ${dtg}.fv_tracer.res.nc
    filename_sfcd: ${dtg}.sfc_data.nc
    filename_sfcw: ${dtg}.fv_srf_wnd.res.nc
    filename_cplr: ${dtg}.coupler.res
    state variables: [u,v,t,delp,sphum,ice_wat,liq_wat,o3mr,phis,
                      slmsk,sheleg,tsea,vtype,stype,vfrac,stc,smc,snwdph,
                      rainwat,snowwat,graupel,cld_amt,DZ,W,
                      u_srf,v_srf,f10m]
  background error:
    covariance model: ensemble
    members from template:
      template:
        filetype: gfs
        state variables:  *3dvars
        datapath: ${ENS_path}/mem%mem%/RESTART/
        filename_core: ${dtg_e}.fv_core.res.nc
        filename_trcr: ${dtg_e}.fv_tracer.res.nc
        filename_sfcd: ${dtg_e}.sfc_data.nc
        filename_sfcw: ${dtg_e}.fv_srf_wnd.res.nc
        filename_cplr: ${dtg}.coupler.res
      pattern: %mem%
      nmembers: $nmem
      zero padding: 3 
    localization:
      localization variables: *3dvars
      localization method: SABER
      saber block:
        saber block name: BUMP_NICAS
        input variables: *3dvars
        output variables: *3dvars
        bump:
          prefix: ${BUMP_name}/fv3jedi_bumpparameters_nicas_3D_gfs
          method: loc 
          strategy: common
          load_nicas_local: 1
          verbosity: main
          io_keys: [common]
          io_values: [fixed_${localization}]
  observations:
  - obs space:
      name: $ROOPR
      obsdatain:
        obsfile: ${OBS_DIR}/gnssro_obs_${CDATE}.nc4
        obsgrouping:
          group variables: [ "record_number" ]
          sort variable: "impact_height"
          sort order: "ascending"
      obsdataout:
        obsfile: ${hofxout}/gnssro_${ROoper}_${CDATE}.nc4
      simulated variables: [bending_angle]
    obs operator:
      name: $ROOPR
      obs options:
EOF

OPTS=("$@")
if [ ${#OPTS[@]} > 0 ]; then
  for iopt in ${OPTS[@]}
  do
    vector0=`echo  $iopt |cut -d : -f1`
    vector1=`echo  $iopt |cut -d : -f2`
    echo "        ${vector0}: ${vector1}" >> $yaml
  done
fi

cat >> $yaml <<  EOF
    obs error:
      covariance model: diagonal
    obs filters:
    - filter: Domain Check
      filter variables:
      - name: bending_angle
      where:
      - variable:
          name: impact_height@MetaData
        minvalue: 0
        maxvalue: 50000
    - filter: ROobserror
      filter variables:
      - name: bending_angle
      errmodel: $errmodel
    - filter: $BackgroundCheck
      filter variables:
      - name: bending_angle 
      threshold: $threshold
EOF

cat >> $yaml <<   EOF
variational:
  minimizer:
    algorithm: $minimizer
  iterations:
  - ninner: $Ninter1
    gradient norm reduction: 1e-10
    test: on
    geometry:
      akbk: ${JEDIsrc}/fv3-jedi/test/Data/fv3files/akbk${NPZ}.nc4
      layout: [$layout,$layout]
      io_layout: [1,1]
      npx: $RESP
      npy: $RESP
      npz: $NPZ
      ntiles: 6
      fieldsets:
      - fieldset: ${JEDIsrc}/fv3-jedi/test/Data/fieldsets/dynamics.yaml
      - fieldset: ${JEDIsrc}/fv3-jedi/test/Data/fieldsets/ufo.yaml
    diagnostics:
      departures: ombg
  - ninner: $Ninter2
    gradient norm reduction: 1e-10
    test: on
    geometry:
      akbk: ${JEDIsrc}/fv3-jedi/test/Data/fv3files/akbk${NPZ}.nc4
      layout: [$layout,$layout]
      io_layout: [1,1]
      npx: $RESP
      npy: $RESP
      npz: $NPZ
      ntiles: 6
      fieldsets:
      - fieldset: ${JEDIsrc}/fv3-jedi/test/Data/fieldsets/dynamics.yaml
      - fieldset: ${JEDIsrc}/fv3-jedi/test/Data/fieldsets/ufo.yaml
    diagnostics:
      departures: ombg
final:
  diagnostics:
    departures: oman
output:
  filetype: gfs
  datapath: ${analysisout}
  filename_core: fv_core.res.nc
  filename_trcr: fv_tracer.res.nc
  filename_sfcd: sfc_data.nc
  filename_sfcw: fv_srf_wnd.res.nc
  filename_cplr: coupler.res
  first: PT0H
  frequency: PT1H

EOF
