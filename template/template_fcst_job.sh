cat > job.sh <<EOF
#!/usr/bin/bash

ulimit -s unlimited
export OMP_NUM_THREADS=1
export OMP_STACKSIZE=1024M
export HOMEgfs=$HOMEgfs
#. /work/noaa/da/cmartin/noscrub/UFO_eval/global-workflow/ush/load_fv3gfs_modules.sh
. /work2/noaa/da/hshao/skylab/scripts/da-fcst/template/load_fv3gfs_modules.sh
module use /work/noaa/da/cmartin/noscrub/UFO_eval/global-workflow/modulefiles
module load module_base.orion
module list

${MPI_RUN} ${MPI_ARGS} /work/noaa/da/cmartin/noscrub/UFO_eval/global-workflow/sorc/fv3gfs.fd/NEMS/exe/global_fv3gfs.x

EOF

