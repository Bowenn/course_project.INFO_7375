#!/bin/bash
# Queue the three Q2.3 steps. Each step starts only if the previous one succeeded.
# Usage: bash submit_q2_3.sh
set -euo pipefail

mkdir -p sbatchLog

TRAIN_ID=$(sbatch --parsable --job-name=a3_train  --time=01:30:00 \
           q2_3_step.sbatch train)

ENCODE_ID=$(sbatch --parsable --job-name=a3_encode --time=00:45:00 \
            --dependency=afterok:$TRAIN_ID  q2_3_step.sbatch encode)

SEARCH_ID=$(sbatch --parsable --job-name=a3_search --time=00:30:00 \
            --dependency=afterok:$ENCODE_ID q2_3_step.sbatch search)

echo "train:  $TRAIN_ID"
echo "encode: $ENCODE_ID (waits for $TRAIN_ID)"
echo "search: $SEARCH_ID (waits for $ENCODE_ID)"
