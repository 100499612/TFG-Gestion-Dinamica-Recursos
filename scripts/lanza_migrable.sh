#!/bin/bash
#SBATCH --job-name=epigraph
#SBATCH --time=03:00:00
#SBATCH --output=logs/%j_output.log
#SBATCH --error=logs/%j_error.log

NUM_PROCESSES=$1
echo "Executing EpiGraph with $1 processes"

# 1. Obtenemos los nodos reales asignados por Slurm y creamos el archivo
scontrol show hostnames $SLURM_JOB_NODELIST > node_list.txt
awk '{ $1 = $1 ":12:" $1; print }' node_list.txt > $HOME/FlexMPIDeveloper/run/nodefile2.dat
rm node_list.txt

# (Hemos eliminado los comandos 'sed' aquí, ya que el awk de arriba 
# genera dinámicamente los nodos limpios en cada migración)

# 2. Adaptación a Elron / Tucán
if [[ $(hostname) == *"elron"* ]]; then
    MPI_FLAGS="-genvall"
    MPIEXEC_CMD="mpiexec"
else
    MPI_FLAGS=""
    MPIEXEC_CMD="/usr/bin/mpiexec.openmpi"
fi

# 3. Lanzamiento
$MPIEXEC_CMD $MPI_FLAGS -np $1 ./epiGraph random $HOME/EpiGraphFlexMPI/ -cfile $HOME/FlexMPIDeveloper/run/nodefile2.dat -policy-malleability-triggered -lbpolicy-static -ni 1440 -ports 4449 4450 -controller localhost -IOaction 0 -alloc:0

echo "done!"