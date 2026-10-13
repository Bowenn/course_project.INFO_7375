#!/bin/bash
set -e
P=data/q42_prefixes.jsonl
mkdir -p outputs/q42
for T in 0.01 0.7 1.0; do
  echo "===== temperature $T ====="
  # your model (generate.py prints the perplexity itself)
  python src/lm/generate.py --config outputs/final-j/config.yaml --prefixes $P \
      --max_new_tokens 32 --temperature $T 2>&1 | grep Perplexity | sed "s/^/ours: /"
  cp outputs/final-j/generation.jsonl outputs/q42/ours_T$T.jsonl

  # Pythia-1.4B
  python src/lm/use_pythia.py --prefixes $P --max_new_tokens 32 --temperature $T \
      --output_dir outputs/q42 > /dev/null 2>&1
  mv outputs/q42/generation_pythia.jsonl outputs/q42/pythia_T$T.jsonl
  python -c "
import json, sys
for line in open(sys.argv[1]):
    print(json.dumps({'document': json.loads(line)['generation']}))
" outputs/q42/pythia_T$T.jsonl > outputs/q42/pythia_T${T}_docs.jsonl
  python src/lm/evaluate_perplexity.py --documents outputs/q42/pythia_T${T}_docs.jsonl \
      --batch_size 1 2>&1 | grep Perplexity | sed "s/^/pythia: /"
done

