echo Launching jobs

# 4 cores per node (Raspberry) -> max num processes = num nodes * 4

# general command: sbatch -N <num nodes> <script name>
# to execute lanza.sh: sbatch -N <num nodes> lanza.sh <num processes>
# --exclusive allocates an entire node for the job (4 cores)

jobid=`sbatch -N 5 --exclusive lanza.sh 20`
echo "jobid::" $jobid