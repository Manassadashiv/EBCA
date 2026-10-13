import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open(r'd:\ebca\scratch\vulnerabilities_literature.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for cat, queries in data.items():
    print(f"\n==========================================")
    print(f"CATEGORY: {cat}")
    print(f"==========================================")
    for q, papers in queries.items():
        print(f"\n  Query: {q}")
        for p in papers[:3]:
            y = p.get('year')
            t = p.get('title')
            c = p.get('citations')
            d = p.get('doi')
            print(f"    * [{y}] {t} (Cited: {c}) | DOI: {d}")
