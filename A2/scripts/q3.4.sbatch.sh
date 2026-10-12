#!/bin/bash
#SBATCH -N 1                                # Number of nodes
#SBATCH -n 1                                # Number of tasks
#SBATCH --partition=gpu
#SBATCH --gres=gpu:h200:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:20:00
#SBATCH -D /home/shi.bow/sbatchDir            # Working directory
#SBATCH -o sbatchLog/%j/output.txt          # Standard output file
#SBATCH -e sbatchLog/%j/error.txt           # Standard error file

module load anaconda3/2024.06

. /shared/EL9/explorer/anaconda3/2024.06/etc/profile.d/conda.sh
eval "$(conda shell.bash hook)"
conda activate /home/shi.bow/p/conda_env/common_h200
which python
python --version
cd $SLURM_SUBMIT_DIR

python src/lm/train.py "$1"


for cfg in configs/sweep/*.yaml; do
  sbatch --job-name=$(basename $cfg .yaml) scripts/q3.4.sbatch.sh $cfg
done
squeue -u $USER