import json

d = json.load(open(r"D:\ebca\scratch\stage3_7_lit\master_literature_summary.json", encoding="utf-8"))
for k, v in d.items():
    if not k.startswith("test"):
        print(f"\n=== {k.upper()} ({len(v)} papers) ===")
        for p in v[:3]:
            print(f" - [{p['year']}] {p['title']}")
            print(f"   Authors/Impact: {p['authors']}")
            print(f"   URL: {p['url']}")
            if p.get("summary"):
                print(f"   Snippet: {p['summary'][:180]}...")
