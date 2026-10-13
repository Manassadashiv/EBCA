import json
import codecs
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

with open(r'd:\ebca\scratch\stage4_survey_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

with open(r'd:\ebca\scratch\survey_summary.txt', 'w', encoding='utf-8') as out:
    for topic, queries in data.items():
        out.write(f"\n{'='*70}\nTOPIC: {topic}\n{'='*70}\n")
        for q, papers in queries.items():
            out.write(f"\n  Query: {q} ({len(papers)} papers)\n")
            for p in papers:
                y = p.get("year")
                t = p.get("title")
                c = p.get("citations")
                d = p.get("doi")
                src = p.get("source_db")
                out.write(f"    * [{src}|{y}] {t} (Cited: {c}) | DOI: {d}\n")

print("Written summary to d:\\ebca\\scratch\\survey_summary.txt")
