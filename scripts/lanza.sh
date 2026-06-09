#!/bin/bash
#SBATCH --job-name=epigraph
#SBATCH --time=03:00:00
#SBATCH --output=logs/%j_output.log
#SBATCH --error=logs/%j_error.log

NUM_PROCESSES=$1
echo "Executing EpiGraph with $1 processes"

scontrol show hostnames $SLURM_JOB_NODELIST > node_list.txt
awk '{ $1 = $1 ":12:" $1; print }' node_list.txt > $HOME/FlexMPIDeveloper/run/nodefile2.dat
rm node_list.txt

if [[ $(hostname) == *"elron"* ]]; then
    MPI_FLAGS="-genvall"
    MPIEXEC_CMD="mpiexec"
else
    MPI_FLAGS=""
    MPIEXEC_CMD="/usr/bin/mpiexec.openmpi"
fi

$MPIEXEC_CMD $MPI_FLAGS -np $1 ./epiGraph random $HOME/EpiGraphFlexMPI/ -cfile $HOME/FlexMPIDeveloper/run/nodefile2.dat -policy-malleability-triggered -lbpolicy-static -ni 1440 -ports 4449 4450 -controller localhost -IOaction 0 -alloc:0
echo "done!"