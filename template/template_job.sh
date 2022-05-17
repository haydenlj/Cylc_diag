echo "generating job script"

jobname=$1
yaml=$2
EXE=$3

cat > $jobname  <<EOF
#!/usr/bin/bash
#-------------------------------------------------------------------------------
#SBATCH --job-name=$yaml
#SBATCH -A da-cpu
##SBATCH -p orion
##SBATCH -q batch
#SBATCH -p debug
#SBATCH -q debug
#SBATCH --ntasks $NTASKS_JEDI
#SBATCH --cpus-per-task=1
#SBATCH --exclusive
##SBATCH -t 80:00
#SBATCH -t 30:00
##SBATCH --output=stdout.%j
#-------------------------------------------------------------------------------
source /etc/bashrc
module purge
module use -a ${JEDIopt}/modulefiles/core
module load jedi/intel-impi
module list
ulimit -s unlimited
ulimit -v unlimited

export SLURM_EXPORT_ENV=ALL
export HDF5_USE_FILE_LOCKING=FALSE
export OOPS_DEBUG=$OOPS_DEBUG
export OOPS_TRACE=$OOPS_TRACE

#-------------------------------------------------------------------------------
 srun --ntasks=$NTASKS_JEDI --cpu_bind=core --distribution=block:block ${JEDIbin}/${EXE} ${yaml}.yaml log/log_${yaml}
#-------------------------------------------------------------------------------
EOF
