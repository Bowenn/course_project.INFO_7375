#!/bin/bash
#SBATCH -N 1                                # Number of nodes
#SBATCH -n 1                                # Number of tasks
#SBATCH --partition=gpu
#SBATCH --gres=gpu:h200:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=01:30:00                     # Default; submit_q2_3.sh overrides it per step
#SBATCH -o sbatchLog/%x_%j.out              # %x = job name, %j = job ID
#SBATCH -e sbatchLog/%x_%j.err

# Usage: sbatch q2_3_step.sbatch <train|encode|search>

set -euo pipefail

STEP="$1"

module load anaconda3/2024.06

. /shared/EL9/explorer/anaconda3/2024.06/etc/profile.d/conda.sh
eval "$(conda shell.bash hook)"
conda activate $HOME/INFO7375.202710/conda-env/a3
export PYTHONNOUSERSITE=1
which python
python --version
nvidia-smi

# ---- Project paths (adjust if your A3 folder is elsewhere) ----
A3_DIR=$HOME/p-self/course_project.INFO_7375/A3
cd "$A3_DIR"
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)/src"

export HF_HOME=/scratch/$USER/hf_cache
mkdir -p "$HF_HOME"

cd "$A3_DIR/src/retriever"

echo "===== Step: $STEP | start: $(date) ====="
case "$STEP" in
  train)  bash scripts/train_msmarco.sh ;;
  encode) bash scripts/encode_fiqa.sh ;;
  search) bash scripts/search_fiqa.sh ;;
  *) echo "Unknown step: $STEP (use train, encode, or search)"; exit 1 ;;
esac
echo "===== Step: $STEP | end: $(date) ====="
