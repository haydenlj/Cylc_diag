rm -f model_configure

cat > model_configure <<EOF
total_member:            1
print_esmf:              ${print_esmf:-.false.}
PE_MEMBER01:             $NTASKS_FV3
start_year:              ${PDY:0:4}
start_month:             ${PDY:4:2}
start_day:               ${PDY:6:2}
start_hour:              ${cyc}
start_minute:            0
start_second:            0
fhrot:                   ${IAU_FHROT:0}
nhours_fcst:             ${FHMAX:-6}
RUN_CONTINUE:            ${RUN_CONTINUE:-.false.}
ENS_SPS:                 .false.

dt_atmos:                $DELTIM
output_1st_tstep_rst:    .false.
calendar:                'julian'
cpl:                     ${cpl:-".false."}
memuse_verbose:          .false.
atmos_nthreads:          1
use_hyper_thread:        .false.
ncores_per_node:         $cores_per_node 
restart_interval:        $restart_interval
quilting:                .true.
write_groups:            1
write_tasks_per_group:   $WRTTASK_PER_GROUP
output_history:          ${OUTPUT_HISTORY:-".true."}
write_dopost:            ${WRITE_DOPOST:-".false."}
num_files:               ${NUM_FILES:-2}
filename_base:           'atm' 'sfc'
output_grid:             $OUTPUT_GRID
output_file:             $OUTPUT_FILETYPES
ichunk2d:                ${ichunk2d:-0}
jchunk2d:                ${jchunk2d:-0}
ichunk3d:                ${ichunk3d:-0}
jchunk3d:                ${jchunk3d:-0}
kchunk3d:                ${kchunk3d:-0}
ideflate:                ${ideflate:-1}
nbits:                   ${nbits:-14}
write_nemsioflip:        $WRITE_NEMSIOFLIP
write_fsyncflag:         $WRITE_FSYNCFLAG
imo:                     ${LONB_IMO:-$LONB_CASE}
jmo:                     ${LATB_IMO:-$LATB_CASE}

nfhout:                  $FHOUT
nfhmax_hf:               $FHMAX_HF
nfhout_hf:               $FHOUT_HF
nsout:                   $NSOUT
iau_offset:              ${IAU_OFFSET:-0}
EOF
