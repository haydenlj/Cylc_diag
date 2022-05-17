echo "generating hyb-3dvar yaml file including, ro, radiosonde, satwinds, aircraft, and atms n20 data"

yaml=${DAmethod}.yaml
if [ -e $yaml ]; then rm -f $yaml; fi

BGNDATE=$( date -u --date="-3 hours ${CDATE:0:4}-${CDATE:4:2}-${CDATE:6:2} ${CDATE:8:2}" +%Y%m%d%H )
yyyy_b=`echo $BGNDATE | cut -c 1-4`
mm_b=`echo $BGNDATE | cut -c 5-6`
dd_b=`echo $BGNDATE | cut -c 7-8`
hh_b=`echo $BGNDATE | cut -c 9-10`

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
  analysis variables: &3dvars  [ua,va,t,ps,sphum,liq_wat,o3mr]
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
                      rainwat,snowwat,graupel,cld_amt,w,DZ,
                      u_srf,v_srf,f10m]
  background error:
    covariance model: hybrid
    components:
    - covariance:
        covariance model: SABER
        saber blocks:
        - saber block name: BUMP_NICAS
          saber central block: true
          input variables: &control_vars [psi,chi,t,ps,sphum,liq_wat,o3mr]
          output variables: *control_vars
          active variables: &active_vars [psi,chi,t,ps,sphum,liq_wat,o3mr]
          bump:
            datadir: $staticB_TOP
            verbosity: main
            strategy: specific_univariate
            load_nicas_local: true
            grids:
            - prefix: nicas_${trainperiod}/nicas_${trainperiod}_3D
              variables: [stream_function,velocity_potential,air_temperature,specific_humidity,cloud_liquid_water,ozone_mass_mixing_ratio]
            - prefix: nicas_${trainperiod}/nicas_${trainperiod}_2D
              variables: [surface_pressure]
            universe radius:
              filetype: gfs
              psinfile: true
              datapath: ${staticB_TOP}/cor_${trainperiod}
              filename_core: cor_rh.fv_core.res.nc
              filename_trcr: cor_rh.fv_tracer.res.nc
              filename_cplr: cor_rh.coupler.res
              date: $sampledate
        - saber block name: StdDev
          input variables: *control_vars
          output variables: *control_vars
          active variables: *active_vars
          file:
            filetype: gfs
            psinfile: true
            datapath: ${staticB_TOP}/var_${trainperiod}
            filename_core: stddev.fv_core.res.nc
            filename_trcr: stddev.fv_tracer.res.nc
            filename_cplr: stddev.coupler.res
            date: $sampledate
        - saber block name: BUMP_VerticalBalance
          input variables: *control_vars
          output variables: *control_vars
          active variables: *active_vars
          bump:
            datadir: ${staticB_TOP}
            prefix: vbal_${trainperiod}/vbal_${trainperiod}
            verbosity: main
            universe_rad: 2000.0e3
            load_vbal: true
            load_samp_local: true
            fname_samp: vbal_${fnamesample}/vbal_${fnamesample}_sampling
            vbal_block: [true, true,false, true,false,false]
        - saber block name: BUMP_PsiChiToUV
          input variables: *control_vars
          output variables: *3dvars
          active variables: [psi,chi,ua,va]
          bump:
            datadir: ${staticB_TOP}
            prefix: psichitouv_${trainperiod}/psichitouv_${trainperiod}
            verbosity: main
            universe_rad: 2000.0e3
            load_wind_local: true
      weight:
        value: $weight_static
    - covariance:
        covariance model: ensemble
        members from template:
          template:
            filetype: gfs
            state variables:  &ensvars [ud,vd,t,ps,sphum,liq_wat,o3mr]
            datapath: ${ENS_path}/mem%mem%/RESTART/
            filename_core: ${dtg_e}.cold2fv3.fv_core.res.nc
            filename_trcr: ${dtg_e}.cold2fv3.fv_tracer.res.nc
            filename_cplr: ${dtg_e}.cold2fv3.coupler.res
          pattern: %mem%
          nmembers: $nmem
          zero padding: 3
        localization:
          localization method: SABER
          saber block:
            saber block name: BUMP_NICAS
            input variables: *3dvars
            output variables: *3dvars
            linear variable change:
              linear variable change name: Control2Analysis
              input variables: *ensvars
              output variables: *3dvars
            bump:
              prefix: ${BUMP_name}/fv3jedi_bumpparameters_nicas_3D_gfs
              method: loc
              strategy: common
              load_nicas_local: true
              verbosity: main
              io_keys: [common]
              io_values: [fixed_${localization}]
      weight:
        value: $weight_ensemble
  observations:
  - obs space:
      name: $ROOPR
      obsdatain:
        obsfile: ${OBS_DIR}/gnssro/gnssro_obs_${CDATE}.nc4
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

cat >> $yaml <<  EOF
  # aircraft
  # --------
  - obs space:
      name: aircraft
      obsdatain:
        obsfile: ${IODA_OBS_DIR}/aircraft/${yyyy_b}${mm_b}${dd_b}T${hh_b}Z_PT6H_aircraft.nc4
      obsdataout:
        obsfile: ${hofxout}/aircraft_${CDATE}.nc4
      simulated variables: [air_temperature, specific_humidity]
    # derived simulated variables: [eastward_wind, northward_wind]
    obs operator:
      name: VertInterp
      variables:
      - name: air_temperature
      - name: specific_humidity
    # - name: eastward_wind
    # - name: northward_wind
      vertical coordinate: height
      observation vertical coordinate: height
    obs filters:
      # First step is to create the needed derived simulated variables.
    # - filter: Variable Transforms
    #   Transform: "WindComponents"
      #
      - filter: Bounds Check
        filter variables:
        - name: air_temperature
        minvalue: 195
        maxvalue: 327
        action:
          name: reject
      #
      - filter: Bounds Check
        filter variables:
        - name: specific_humidity
        minvalue: 1.0E-7
        maxvalue: 0.034999999
        action:
          name: reject
      #
      # Begin by assigning all ObsError to a constant value. These will get overwritten for specific types.
      - filter: Perform Action
        filter variables:
        - name: air_temperature
        action:
          name: assign error
          error parameter: 2.0             # 2.0 K
      # Assign the initial observation error, based on pressure (for AMDAR and MDCRS; itype=131,133)
      - filter: Perform Action
        filter variables:
        - name: air_temperature
        action:
          name: assign error
          error function:
            name: ObsErrorModelStepwiseLinear@ObsFunction
            options:
              xvar:
                name: MetaData/height
              xvals: [50, 500, 1000, 1500, 9000, 10000, 11000, 12000, 13000, 14000, 16000, 18000]
              errors: [1.2, 1.1, 0.9, 0.8, 0.8, 0.9, 1.2, 1.2, 1.0, 0.8, 1.3, 1.7]
      # Begin by assigning all ObsError to a constant value. These will get overwritten for specific types.
      - filter: Perform Action
        filter variables:
        - name: specific_humidity
        action:
          name: assign error
          error parameter: 1.0E-3
      # Assign the initial observation error, based on height/pressure ONLY MDCRS
      - filter: Perform Action
        filter variables:
        - name: specific_humidity
        action:
          name: assign error
          error function:
            name: ObsErrorModelStepwiseLinear@ObsFunction
            options:
              xvar:
                name: MetaData/height
              xvals: [100, 5000, 10000, 12000, 14000, 16000]
              errors: [0.25, 0.2, 0.2, 0.25, 0.35, 0.2]
              scale_factor_var: ObsValue/specific_humidity
      # Gross error check with (O - B) / ObsError greater than threshold.
      - filter: Background Check
        filter variables:
        - name: air_temperature
        threshold: 7.0
        absolute threshold: 8.0
        action:
          name: reject
        defer to post: true
      #
      - filter: Background Check
        filter variables:
        - name: specific_humidity
        threshold: 8.0
        action:
          name: reject
        defer to post: true
      # Reject specific humidity where temperature was rejected.
      - filter: RejectList
        filter variables:
        - name: specific_humidity
        where:
        - variable: QCflagsData/air_temperature
          minvalue: 1
        defer to post: true

EOF

cat >> $yaml <<  EOF
  - obs space:
      name: satwinds
      _source: ldm
      obsdatain:
        obsfile: ${SAT_OBS_DIR}/satwinds_obs_${CDATE}.nc4
      obsdataout:
        obsfile: ${hofxout}/satwinds_${CDATE}.nc4
      simulated variables: [eastward_wind, northward_wind]
    obs operator:
      name: VertInterp
      variables:
      - name: eastward_wind
      - name: northward_wind
    obs filters:
      # Assign the initial observation error, based on height/pressure
      - filter: Perform Action
        filter variables:
        - name: eastward_wind
        - name: northward_wind
        action:
          name: assign error
          error function:
            name: ObsErrorModelStepwiseLinear@ObsFunction
            options:
              xvar:
                name: MetaData/air_pressure
              xvals: [100000, 95000, 80000, 65000, 60000, 55000, 50000, 45000, 40000, 35000, 30000, 25000, 20000, 15000, 10000]   #Pressure (Pa)
              errors: [1.4, 1.5, 1.6, 1.8, 1.9, 2.0, 2.1, 2.3, 2.6, 2.8, 3.0, 3.2, 2.7, 2.4, 2.1]
      # Observation Range Sanity Check
      - filter: Bounds Check
        filter variables:
        - name: eastward_wind
        - name: northward_wind
        minvalue: -130
        maxvalue: 130
        action:
          name: reject
      #
      - filter: Bounds Check
        filter variables:
        - name: eastward_wind
        - name: northward_wind
        test variables:
        - name: Velocity@ObsFunction
        maxvalue: 130.0
        action:
          name: reject
      #
      - filter: Bounds Check
        filter variables:
        - name: eastward_wind
        - name: northward_wind
        test variables:
        - name: MetaData/satwind_quality_ind_no_fc
        minvalue: 80.0
        action:
          name: reject
      # Reject when pressure greater than 925 mb.
      - filter: Bounds Check
        filter variables:
        - name: eastward_wind
        - name: northward_wind
        test variables:
        - name: MetaData/air_pressure
        maxvalue: 92500
      # MODIS-Aqua/Terra (257) and (259), reject when pressure less than 125 mb.
      - filter: Bounds Check
        filter variables:
        - name: eastward_wind
        - name: northward_wind
        test variables:
        - name: MetaData/air_pressure
        minvalue: 12500
      # Multiple satellite platforms, reject when pressure is more than 50 mb above tropopause.
      - filter: Difference Check
        filter variables:
        - name: eastward_wind
        - name: northward_wind
        reference: TropopauseEstimate@ObsFunction
        value: MetaData/air_pressure
        minvalue: -5000                    # 50 hPa above tropopause level, negative p-diff
        action:
          name: reject
      # Difference check surface_pressure and ObsValue/air_pressure, if less than 100 hPa, reject.
      - filter: Difference Check
        filter variables:
        - name: eastward_wind
        - name: northward_wind
        reference: GeoVaLs/surface_pressure
        value: MetaData/air_pressure
        maxvalue: -10000
      # Reject when difference of wind direction is more than 50 degrees.
      - filter: Bounds Check
        filter variables:
        - name: eastward_wind
        - name: northward_wind
        test variables:
        - name: WindDirAngleDiff@ObsFunction
          options:
            minimum_uv: 3.5
        maxvalue: 50.0
        action:
          name: reject
        defer to post: true
      # AVHRR (244), MODIS (257,258,259), VIIRS (260), GOES (247) use a LNVD check.
      - filter: Bounds Check
        filter variables:
        - name: eastward_wind
        - name: northward_wind
        test variables:
        - name: SatWindsLNVDCheck@ObsFunction
        maxvalue: 3
        action:
          name: reject
        defer to post: true
      # AVHRR and MODIS (ObsType=244,257,258,259) use a SPDB check.
      - filter: Bounds Check
        filter variables:
        - name: eastward_wind
        - name: northward_wind
        test variables:
        - name: SatWindsSPDBCheck@ObsFunction
          options:
            error_min: 1.4
            error_max: 20.0
        maxvalue: 1.75
        action:
          name: reject
        defer to post: true
      # Gross error check with (O - B) / ObsError greater than threshold.
      - filter: Background Check
        filter variables:
        - name: eastward_wind
        - name: northward_wind
        threshold: 6.0
        action:
          name: reject
      # Reject eastward wind where northward wind was rejected and vice versa.
      - filter: RejectList
        filter variables:
        - name: northward_wind
        where:
        - variable: QCflagsData/eastward_wind
          minvalue: 1
        defer to post: true
      - filter: RejectList
        filter variables:
        - name: eastward_wind
        where:
        - variable: QCflagsData/northward_wind
          minvalue: 1
        defer to post: true
EOF

cat >> $yaml <<   EOF
  # radiosonde
  # ----------
  - obs space:
      name: radiosonde
      obsdatain:
        obsfile: ${OBS_DIR}/${yyyy_b}${mm_b}${dd_b}T${hh_b}Z_PT6H_radiosonde.nc4
        obsgrouping:
          group variables: [station_id, LaunchTime]
          sort variable: air_pressure
          sort order: ascending
      obsdataout:
        obsfile: ${hofxout}/radiosonde_${CDATE}.nc4
      simulated variables: [air_temperature, specific_humidity, eastward_wind, northward_wind]
    obs operator:
      name: Composite
      components:
      - name: VertInterp
        variables:
        - name: air_temperature
        - name: specific_humidity
        - name: eastward_wind
        - name: northward_wind
      da_psfc_scheme: UKMO
    obs filters:
      - filter: Bounds Check
        filter variables:
        - name: air_temperature
        minvalue: 195
        maxvalue: 327
        action:
          name: reject
      - filter: Bounds Check
        filter variables:
        - name: specific_humidity
        minvalue: 1.0E-8
        maxvalue: 0.034999999
        action:
          name: reject
      - filter: Bounds Check
        filter variables:
        - name: eastward_wind
        - name: northward_wind
        minvalue: -130
        maxvalue: 130
        action:
          name: reject
      - filter: Bounds Check
        filter variables:
        - name: eastward_wind
        - name: northward_wind
        minvalue: -130
        maxvalue: 130
        action:
          name: reject
      - filter: Bounds Check
        filter variables:
        - name: eastward_wind
        - name: northward_wind
        test variables:
        - name: Velocity@ObsFunction
        maxvalue: 130.0
        action:
          name: reject
      - filter: Perform Action
        filter variables:
        - name: eastward_wind
        - name: northward_wind
        action:
          name: assign error
          error parameter: 1.4
      - filter: Perform Action
        filter variables:
        - name: specific_humidity
        action:
          name: assign error
          error parameter: 1.0E-3
      - filter: Perform Action
        filter variables:
        - name: air_temperature
        action:
          name: assign error
          error function:
            name: ObsErrorModelStepwiseLinear@ObsFunction
            options:
              xvar:
                name: MetaData/air_pressure
              xvals: [100000, 95000, 90000, 85000, 35000, 30000, 25000, 20000, 15000, 10000, 7500, 5000, 4000, 3000, 2000, 1000]
              errors: [1.2, 1.1, 0.9, 0.8, 0.8, 0.9, 1.2, 1.2, 1.0, 0.8, 0.8, 0.9, 0.95, 1.0, 1.25, 1.5]
      - filter: Perform Action
        filter variables:
        - name: specific_humidity
        action:
          name: assign error
          error function:
            name: ObsErrorModelStepwiseLinear@ObsFunction
            options:
              xvar:
                name: MetaData/air_pressure
              xvals: [25000, 20000, 10]
              errors: [0.2, 0.4, 0.8]
              scale_factor_var: ObsValue/specific_humidity
      - filter: Perform Action
        filter variables:
        - name: eastward_wind
        - name: northward_wind
        action:
          name: assign error
          error function:
            name: ObsErrorModelStepwiseLinear@ObsFunction
            options:
              xvar:
                name: MetaData/air_pressure
              xvals: [100000, 95000, 80000, 65000, 60000, 55000, 50000, 45000, 40000, 35000, 30000, 25000, 20000, 15000, 10000]
              errors: [1.4, 1.5, 1.6, 1.8, 1.9, 2.0, 2.1, 2.3, 2.6, 2.8, 3.0, 3.2, 2.7, 2.4, 2.1]
      - filter: Bounds Check
        filter variables:
        - name: eastward_wind
        - name: northward_wind
        test variables:
        - name: WindDirAngleDiff@ObsFunction
          options:
            minimum_uv: 3.5
        maxvalue: 50.0
        action:
          name: reject
        defer to post: true
      - filter: Background Check
        filter variables:
        - name: air_temperature
        threshold: 7.0
        absolute threshold: 9.0
        action:
          name: reject
        defer to post: true
      - filter: Background Check
        filter variables:
        - name: eastward_wind
        - name: northward_wind
        threshold: 6.0
        absolute threshold: 19.0
        action:
          name: reject
        defer to post: true
      - filter: Background Check
        filter variables:
        - name: specific_humidity
        threshold: 8.0
        action:
          name: reject
        defer to post: true
      - filter: RejectList
        filter variables:
        - name: northward_wind
        where:
        - variable: QCflagsData/eastward_wind
          minvalue: 1
        defer to post: true
      - filter: RejectList
        filter variables:
        - name: eastward_wind
        where:
        - variable: QCflagsData/northward_wind
          minvalue: 1
        defer to post: true
      - filter: RejectList
        filter variables:
        - name: specific_humidity
        where:
        - variable: QCflagsData/air_temperature
          minvalue: 1
        defer to post: true

EOF

echo ${OBS_DIR}/atms/${yyyy_b}${mm_b}${dd_b}T${hh_b}Z_PT6H_atms_n20.nc4
echo ${OBS_DIR}/atms/${yyyy_b}${mm_b}${dd_b}T${hh_b}Z_PT6H_atms.nc4/instr
export  rundir=${TOP_DIR}/run/${EXPT}/${CDATE}/da
export  satbiasout=${rundir}/output/satbias

if [ ! -d ${satbiasout} ]; then  mkdir -p ${satbiasout}; fi

export ymd_pre=${PREDATE:0:8}
export hh_pre=${PREDATE:8:2}
export SATINFO=${PREP_DATA_DIR}/satbias/${ymd_pre}/${hh_pre}/
echo "adding  atms_n20 to yaml"
export LAPSEFILE=/work2/noaa/da/hailingz/work/Data/satbias/tlapmean/atms_n20_tlapmean.txt
export SATBIAS_IN=${SATINFO}/satbias_atms_n20.nc4
export SATBIAS_COV=${SATINFO}/satbias_atms_n20.nc4
export SATBIAS_OUT=${TOP_DIR}/${CDATE}/da/output/satbias_atms_n20.nc4

#if [ $CDATE -ne $INIT_DATE ]; then
#   export SATBIAS_COV=${TOP_DIR}/${PREDATE}/da/output/satbias_atms_n20.nc4
#else
#   export SATBIAS_COV=${SATINFO_FIX}/satbias_atms_n20.nc4
#fi

cat >> $yaml <<   EOF
  #ATMS n20
  - obs operator:
      name: CRTM
      Absorbers: [H2O,O3]
      obs options:
        Sensor_ID: &Sensor_ID atms_n20
        EndianType: little_endian
        CoefficientPath: /work2/noaa/da/hailingz/work/Data/crtm/
    obs space:
      name: *Sensor_ID 
      obsdatain:
        obsfile: ${OBS_DIR}/atms/${yyyy_b}${mm_b}${dd_b}T${hh_b}Z_PT6H_atms_n20.nc4
      obsdataout:
        obsfile: ${hofxout}/atms_n20_output_${CDATE}.nc4
      simulated variables: [brightness_temperature]
      channels: &atms_n20_channels 1-22 
    obs error:
      covariance model: diagonal
    obs bias:
      input file: ${SATBIAS_IN}
      output file: ${SATBIAS_OUT}
      variational bc:
        predictors: &predictors1
        - name: constant
        - name: lapse_rate
          order: 2
          tlapse: &atms_n20_tlap $LAPSEFILE
        - name: lapse_rate
          tlapse: *atms_n20_tlap
        - name: emissivity
        - name: scan_angle
          order: 4
        - name: scan_angle
          order: 3
        - name: scan_angle
          order: 2
        - name: scan_angle
      covariance:
        minimal required obs number: 20
        variance range: [1.0e-6, 10.]
        step size: 1.0e-4
        largest analysis variance: 10000.0
        prior:
          input file: ${SATBIAS_COV}
          inflation:
            ratio: 1.1
            ratio for small dataset: 2.0
        output file: ${satbiasout}/satbias_cov_atms_n20.nc4
    obs filters:
    - filter: BlackList
      filter variables:
      - name: brightness_temperature
        channels: *atms_n20_channels
      action:
        name: assign error
        error function:
          name: ObsErrorModelRamp@ObsFunction
          channels: *atms_n20_channels
          options:
            channels: *atms_n20_channels
            xvar:
              name: CLWRetSymmetricMW@ObsFunction
              options:
                clwret_ch238: 1
                clwret_ch314: 2
                clwret_types: [ObsValue, HofX]
            x0:    [ 0.030,  0.030,  0.030,  0.020,  0.030,
                     0.080,  0.150,  0.000,  0.000,  0.000,
                     0.000,  0.000,  0.000,  0.000,  0.000,
                     0.020,  0.030,  0.030,  0.030,  0.030,
                     0.050,  0.100]
            x1:    [ 0.350,  0.380,  0.400,  0.450,  0.500,
                     1.000,  1.000,  0.000,  0.000,  0.000,
                     0.000,  0.000,  0.000,  0.000,  0.000,
                     0.350,  0.500,  0.500,  0.500,  0.500,
                     0.500,  0.500]
            err0:  [ 4.500,  4.500,  4.500,  2.500,  0.550,
                     0.300,  0.300,  0.400,  0.400,  0.400,
                     0.450,  0.450,  0.550,  0.800,  3.000,
                     4.000,  4.000,  3.500,  3.000,  3.000,
                     3.000,  3.000]
            err1:  [20.000, 25.000, 12.000,  7.000,  3.500,
                     3.000,  0.800,  0.400,  0.400,  0.400,
                     0.450,  0.450,  0.550,  0.800,  3.000,
                    19.000, 30.000, 25.000, 16.500, 12.000,
                     9.000,  6.500]
#  CLW Retrieval Check
    - filter: Bounds Check
      filter variables:
      - name: brightness_temperature
        channels: 1-7, 16-22
      test variables:
      - name: CLWRetMW@ObsFunction
        options:
          clwret_ch238: 1
          clwret_ch314: 2
          clwret_types: [ObsValue]
      maxvalue: 999.0
      action:
        name: reject
#  Hydrometeor Check (cloud/precipitation affected chanels)
    - filter: Bounds Check
      filter variables:
      - name: brightness_temperature
        channels: *atms_n20_channels
      test variables:
      - name: HydrometeorCheckATMS@ObsFunction
        channels: *atms_n20_channels
        options:
          channels: *atms_n20_channels
          obserr_clearsky:  [ 4.500,  4.500,  4.500,  2.500,  0.550,
                              0.300,  0.300,  0.400,  0.400,  0.400,
                              0.450,  0.450,  0.550,  0.800,  3.000,
                              4.000,  4.000,  3.500,  3.000,  3.000,
                              3.000,  3.000]
          clwret_function:
            name: CLWRetMW@ObsFunction
            options:
              clwret_ch238: 1
              clwret_ch314: 2
              clwret_types: [ObsValue]
          obserr_function:
            name: ObsErrorModelRamp@ObsFunction
            channels: *atms_n20_channels
            options:
              channels: *atms_n20_channels
              xvar:
                name: CLWRetSymmetricMW@ObsFunction
                options:
                  clwret_ch238: 1
                  clwret_ch314: 2
                  clwret_types: [ObsValue, HofX]
              x0:    [ 0.030,  0.030,  0.030,  0.020,  0.030,
                       0.080,  0.150,  0.000,  0.000,  0.000,
                       0.000,  0.000,  0.000,  0.000,  0.000,
                       0.020,  0.030,  0.030,  0.030,  0.030,
                       0.050,  0.100]
              x1:    [ 0.350,  0.380,  0.400,  0.450,  0.500,
                       1.000,  1.000,  0.000,  0.000,  0.000,
                       0.000,  0.000,  0.000,  0.000,  0.000,
                       0.350,  0.500,  0.500,  0.500,  0.500,
                       0.500,  0.500]
              err0:  [ 4.500,  4.500,  4.500,  2.500,  0.550,
                       0.300,  0.300,  0.400,  0.400,  0.400,
                       0.450,  0.450,  0.550,  0.800,  3.000,
                       4.000,  4.000,  3.500,  3.000,  3.000,
                       3.000,  3.000]
              err1:  [20.000, 25.000, 12.000,  7.000,  3.500,
                      3.000,  0.800,  0.400,  0.400,  0.400,
                      0.450,  0.450,  0.550,  0.800,  3.000,
                     19.000, 30.000, 25.000, 16.500, 12.000,
                      9.000,  6.500]
      maxvalue: 0.0
      action:
        name: reject
#  Topography check
    - filter: BlackList
      filter variables:
      - name: brightness_temperature
        channels: *atms_n20_channels
      action:
        name: inflate error
        inflation variable:
          name: ObsErrorFactorTopoRad@ObsFunction
          channels: *atms_n20_channels
          options:
            sensor: *Sensor_ID
            channels: *atms_n20_channels
#  Transmittnace Top Check
    - filter: BlackList
      filter variables:
      - name: brightness_temperature
        channels: *atms_n20_channels
      action:
        name: inflate error
        inflation variable:
          name: ObsErrorFactorTransmitTopRad@ObsFunction
          channels: *atms_n20_channels
          options:
            channels: *atms_n20_channels
#  Surface Jacobian check
    - filter: BlackList
      filter variables:
      - name: brightness_temperature
        channels: *atms_n20_channels
      action:
        name: inflate error
        inflation variable:
          name: ObsErrorFactorSurfJacobianRad@ObsFunction
          channels: *atms_n20_channels
          options:
            channels: *atms_n20_channels
            obserr_demisf: [0.010, 0.020, 0.015, 0.020, 0.200]
            obserr_dtempf: [0.500, 2.000, 1.000, 2.000, 4.500]
#  Situation dependent Check
    - filter: BlackList
      filter variables:
      - name: brightness_temperature
        channels: *atms_n20_channels
      action:
        name: inflate error
        inflation variable:
          name: ObsErrorFactorSituDependMW@ObsFunction
          channels: *atms_n20_channels
          options:
            sensor: *Sensor_ID
            channels: *atms_n20_channels
            clwobs_function:
              name: CLWRetMW@ObsFunction
              options:
                clwret_ch238: 1
                clwret_ch314: 2
                clwret_types: [ObsValue]
            clwbkg_function:
              name: CLWRetMW@ObsFunction
              options:
                clwret_ch238: 1
                clwret_ch314: 2
                clwret_types: [HofX]
            scatobs_function:
              name: SCATRetMW@ObsFunction
              options:
                scatret_ch238: 1
                scatret_ch314: 2
                scatret_ch890: 16
                scatret_types: [ObsValue]
            clwmatchidx_function:
              name: CLWMatchIndexMW@ObsFunction
              channels: *atms_n20_channels
              options:
                channels: *atms_n20_channels
                clwobs_function:
                  name: CLWRetMW@ObsFunction
                  options:
                    clwret_ch238: 1
                    clwret_ch314: 2
                    clwret_types: [ObsValue]
                clwbkg_function:
                  name: CLWRetMW@ObsFunction
                  options:
                    clwret_ch238: 1
                    clwret_ch314: 2
                    clwret_types: [HofX]
                clwret_clearsky: [ 0.030,  0.030,  0.030,  0.020,  0.030,
                                   0.080,  0.150,  0.000,  0.000,  0.000,
                                   0.000,  0.000,  0.000,  0.000,  0.000,
                                   0.020,  0.030,  0.030,  0.030,  0.030,
                                   0.050,  0.100]
            obserr_clearsky:  [ 4.500,  4.500,  4.500,  2.500,  0.550,
                                0.300,  0.300,  0.400,  0.400,  0.400,
                                0.450,  0.450,  0.550,  0.800,  3.000,
                                4.000,  4.000,  3.500,  3.000,  3.000,
                                3.000,  3.000]
#  Gross check
    - filter: Background Check
      filter variables:
      - name: brightness_temperature
        channels: *atms_n20_channels
      function absolute threshold:
      - name: ObsErrorBoundMW@ObsFunction
        channels: *atms_n20_channels
        options:
          sensor: *Sensor_ID
          channels: *atms_n20_channels
          obserr_bound_latitude:
            name: ObsErrorFactorLatRad@ObsFunction
            options:
              latitude_parameters: [25.0, 0.25, 0.04, 3.0]
          obserr_bound_transmittop:
            name: ObsErrorFactorTransmitTopRad@ObsFunction
            channels: *atms_n20_channels
            options:
              channels: *atms_n20_channels
          obserr_bound_topo:
            name: ObsErrorFactorTopoRad@ObsFunction
            channels: *atms_n20_channels
            options:
              channels: *atms_n20_channels
              sensor: *Sensor_ID
          obserr_function:
            name: ObsErrorModelRamp@ObsFunction
            channels: *atms_n20_channels
            options:
              channels: *atms_n20_channels
              xvar:
                name: CLWRetSymmetricMW@ObsFunction
                options:
                  clwret_ch238: 1
                  clwret_ch314: 2
                  clwret_types: [ObsValue, HofX]
              x0:    [ 0.030,  0.030,  0.030,  0.020,  0.030,
                       0.080,  0.150,  0.000,  0.000,  0.000,
                       0.000,  0.000,  0.000,  0.000,  0.000,
                       0.020,  0.030,  0.030,  0.030,  0.030,
                       0.050,  0.100]
              x1:    [ 0.350,  0.380,  0.400,  0.450,  0.500,
                       1.000,  1.000,  0.000,  0.000,  0.000,
                       0.000,  0.000,  0.000,  0.000,  0.000,
                       0.350,  0.500,  0.500,  0.500,  0.500,
                       0.500,  0.500]
              err0:  [ 4.500,  4.500,  4.500,  2.500,  0.550,
                       0.300,  0.300,  0.400,  0.400,  0.400,
                       0.450,  0.450,  0.550,  0.800,  3.000,
                       4.000,  4.000,  3.500,  3.000,  3.000,
                       3.000,  3.000]
              err1:  [20.000, 25.000, 12.000,  7.000,  3.500,
                       3.000,  0.800,  0.400,  0.400,  0.400,
                       0.450,  0.450,  0.550,  0.800,  3.000,
                      19.000, 30.000, 25.000, 16.500, 12.000,
                       9.000,  6.500]
          obserr_bound_max: [4.5, 4.5, 3.0, 3.0, 1.0,
                             1.0, 1.0, 1.0, 1.0, 1.0,
                             1.0, 1.0, 1.0, 2.0, 4.5,
                             4.5, 2.0, 2.0, 2.0, 2.0,
                             2.0, 2.0]
      action:
        name: reject
#  Inter-channel check
    - filter: Bounds Check
      filter variables:
      - name: brightness_temperature
        channels: *atms_n20_channels
      test variables:
      - name: InterChannelConsistencyCheck@ObsFunction
        channels: *atms_n20_channels
        options:
          channels: *atms_n20_channels
          sensor: *Sensor_ID
          use_flag: [ 1,  1,  1,  1,  1,
                      1,  1,  1,  1,  1,
                      1,  1,  1,  1, -1,
                      1,  1,  1,  1,  1,
                      1,  1]
      maxvalue: 1.0e-12
      action:
        name: reject
#  Useflag check
    - filter: Bounds Check
      filter variables:
      - name: brightness_temperature
        channels: *atms_n20_channels
      test variables:
      - name: ChannelUseflagCheckRad@ObsFunction
        channels: *atms_n20_channels
        options:
          channels: *atms_n20_channels
          use_flag: [ 1,  1,  1,  1,  1,
                      1,  1,  1,  1,  1,
                      1,  1,  1,  1, -1,
                      1,  1,  1,  1,  1,
                      1,  1]
      minvalue: 1.0e-12
      action:
        name: reject
    - filter: Gaussian_Thinning
      horizontal_mesh: 145

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

