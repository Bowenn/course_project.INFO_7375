"""Find example test instances for Q1.5 in pythia-1b-asdiv/eval.jsonl.

Usage (from the A3 root):
    python q1_5_find.py            # show 5 examples of each case
    python q1_5_find.py 10         # show 10 examples of each case
"""
import sys

import numpy as np
import pandas as pd

N = int(sys.argv[1]) if len(sys.argv) > 1 else 5

df = pd.read_json("pythia-1b-asdiv/eval.jsonl", lines=True)

correct_calc = np.isclose(df["label-calc"], df["label"])
correct_no_calc = np.isclose(df["label-no-calc"], df["label"])

case_a = df[correct_calc & ~correct_no_calc]   # Q1.5A: calculator fixes it
case_b = df[~correct_calc]                     # Q1.5B: wrong even with calculator


def show(title, rows):
    print("=" * 80)
    print(f"{title}  ({len(rows)} instances in total)")
    print("=" * 80)
    for idx, row in rows.head(N).iterrows():
        print(f"\n--- test index {idx} ---")
        print(f"[gold target]    {row['target']}   (label = {row['label']})")
        print(f"[with calc]      {row['answer-calc'].split('Answer:')[-1]}")
        print(f"[without calc]   {row['answer-no-calc'].split('Answer:')[-1]}")
        print(f"[full prompt]    {row['text']}")
    print()


show("Q1.5A: incorrect WITHOUT calculator, correct WITH calculator", case_a)
show("Q1.5B: incorrect even WITH calculator", case_b)
