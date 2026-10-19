import urllib.request
import re
import ssl
import json

ctx = ssl._create_unverified_context()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def check_url(name, url):
    print(f"\n--- Checking {name} ({url}) ---", flush=True)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            html = r.read().decode('utf-8', errors='ignore')
            # Find any pdf, download, or bitstream links
            links = re.findall(r'href=[\'"]([^\'"]+?(?:bitstream|download|document|\.pdf)[^\'"]*?)[\'"]', html, re.I)
            print(f"  Found {len(links)} candidate links:", flush=True)
            for l in links[:10]:
                print(f"    * {l}", flush=True)
            return links
    except Exception as e:
        print(f"  Error: {e}", flush=True)
        return []

check_url("P2-2 NUS", "https://scholarbank.nus.edu.sg/handle/10635/232906")
check_url("P2-2 Amsterdam DARE", "https://dare.uva.nl/personal/pure/en/publications/4d-printing-of-shape-memory-polylactic-acid-pla(8740d2a7-5dbd-4f0d-b263-f280b1c652a3).html")
check_url("P2-5 HAL doc", "https://hal.science/hal-03492410/file/S0264127520304457.pdf")
check_url("P1-5 Sabanci", "https://research.sabanciuniv.edu/id/eprint/51994/")
check_url("P2-4 Roma Tre", "http://hdl.handle.net/11590/376923")
