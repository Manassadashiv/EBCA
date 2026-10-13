import json

with open(r'd:\ebca\scratch\stage4_survey_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

total = sum(len(papers) for topic in data.values() for papers in topic.values())
print(f"Total entries harvested: {total}")

for topic, queries in data.items():
    print(f"\n==========================================")
    print(f"TOPIC: {topic}")
    print(f"==========================================")
    for q, papers in queries.items():
        print(f"\n  Query: {q} ({len(papers)} papers)")
        for p in papers[:3]:
            y = p.get("year")
            t = p.get("title")
            c = p.get("citations")
            d = p.get("doi")
            print(f"    * [{y}] {t} (Cited: {c}) | DOI: {d}")
