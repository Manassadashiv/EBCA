import urllib.request
import re
import ssl

ctx = ssl._create_unverified_context()
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def find_pdf_links(page_url):
    print(f"\nChecking landing page: {page_url}", flush=True)
    try:
        req = urllib.request.Request(page_url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            # Look for pdf links
            pdf_links = re.findall(r'href=[\'"]([^\'"]+?\.pdf[^\'"]*?)[\'"]', html, re.I)
            doc_links = re.findall(r'href=[\'"]([^\'"]+?/(?:document|download)[^\'"]*?)[\'"]', html, re.I)
            print(f"  Found {len(pdf_links)} .pdf links, {len(doc_links)} doc/download links:", flush=True)
            for l in (pdf_links + doc_links)[:5]:
                print(f"    -> {l}", flush=True)
    except Exception as e:
        print(f"  Error: {e}", flush=True)

# Check HAL for P2-5
find_pdf_links("https://hal.science/hal-03492410")

# Check Sabanci for P1-5
find_pdf_links("https://research.sabanciuniv.edu/id/eprint/51994/")

# Check Manchester for P2-1
find_pdf_links("https://research.manchester.ac.uk/en/publications/afbd6e42-4ffa-43b8-9a91-59fafadaf113")

# Check UTwente / HAL for P2-2
find_pdf_links("https://hal.univ-lorraine.fr/hal-03318525")
find_pdf_links("https://research.utwente.nl/en/publications/7efc9e0c-4873-4d46-bd37-14e82c1b80f5")

# Check UTwente for P2-4
find_pdf_links("https://research.utwente.nl/en/publications/1af4bf68-43b3-4a75-82e6-405dcfc9c2cc")
