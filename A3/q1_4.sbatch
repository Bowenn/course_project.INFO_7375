#!/bin/bash
#SBATCH -N 1                                # Number of nodes
#SBATCH -n 1                                # Number of tasks
#SBATCH --partition=gpu
#SBATCH --gres=gpu:h200:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=01:00:00                     # Assignment says <10 min; margin for downloads
#SBATCH --job-name=a3_q1_4
#SBATCH -o sbatchLog/%x_%j.out
#SBATCH -e sbatchLog/%x_%j.err

set -euo pipefail

module load anaconda3/2024.06

. /shared/EL9/explorer/anaconda3/2024.06/etc/profile.d/conda.sh
eval "$(conda shell.bash hook)"
conda activate /courses/INFO7375.202710/students/shi.bow/conda-env/a3
export PYTHONNOUSERSITE=1
which python
python --version
nvidia-smi

# ---- Project paths ----
A3_DIR=$HOME/p-self/course_project.INFO_7375/A3
cd "$A3_DIR"                                # run from the A3 root, as the assignment says
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)/src"

export HF_HOME=/scratch/$USER/hf_cache
mkdir -p "$HF_HOME"

echo "===== Q1.4 start: $(date) ====="
python src/calculator/main.py
echo "===== Q1.4 end: $(date) ====="
