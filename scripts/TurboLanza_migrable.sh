#!/bin/bash
echo "Lanzando trabajo con soporte de migración..."

# Slurm elige un nodo libre donde ejecutar la tarea
jobid=$(sbatch -N 2 --exclusive lanza_migrable.sh 8)

echo "Sistema en marcha con JobID: $jobid"
