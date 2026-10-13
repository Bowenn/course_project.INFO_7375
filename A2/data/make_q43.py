import json, os, re, sys
sys.path.insert(0, "data")
from make_ppl_example_jsonl import northeastern_university_wiki, jabberwocky

# A. remove every "the" (both "the" and "The", as whole words)
no_the = re.sub(r"\b[Tt]he\b ?", "", northeastern_university_wiki)

# B. your mimic poem: REPLACE these example words with your own nonsense words
swaps = {
    "brillig": "grwwdwd", "slithy": "plooox", "toves": "bbbles",
    "mimsy": "snwwwwwwy", "borogoves": "cacacacacaats",
    "Jabberwock": "GrozzlewumxxxXXp", "JuOOub": "FPPzzfub",
    "frumious": "blustrous", "Bandersnatch": "Quillersnap",
    "vorpal": "zindle", "manxome": "blorish", "Tumtum": "Wimwam",
    "uffish": "ogglish", "whiffling": "snorfling", "tulgey": "brimsy",
    "galumphing": "skrambling", "beamish": "glimsy",
    "frabjous": "snazzlous", "Callooh": "Fallooh", "Callay": "Fallay",
}
mimic = jabberwocky
for old, new in swaps.items():
    mimic = re.sub(rf"\b{old}\b", new, mimic)

os.makedirs("data/q43", exist_ok=True)
for name, text in [("neu", northeastern_university_wiki), ("neu_no_the", no_the),
                   ("jabberwocky", jabberwocky), ("mimic", mimic)]:
    with open(f"data/q43/{name}.jsonl", "w") as f:
        f.write(json.dumps({"document": text}) + "\n")
print(mimic)
