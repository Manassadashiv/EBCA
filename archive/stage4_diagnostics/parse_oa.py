import json

with open('D:/Literature_PDFs/oa_discovery.json') as f:
    d = json.load(f)

for pid, info in d.items():
    print(f"*** {pid} *** ({info['title'][:50]}...)")
    print(f"  DOI: {info.get('doi')}")
    print(f"  OA Status: {info.get('openalex', {}).get('oa_status')}")
    print("  OA URLs:")
    for typ, u in info.get('oa_urls', []):
        print(f"    [{typ}] {u}")
