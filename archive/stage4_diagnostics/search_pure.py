import urllib.request
import urllib.parse
import re
import ssl

ctx = ssl._create_unverified_context()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def search_uva(query):
    print(f"\nSearching UVA Pure for: {query}")
    url = f"https://pure.uva.nl/en/publications/?search={urllib.parse.quote(query)}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            html = r.read().decode('utf-8', errors='ignore')
            links = re.findall(r'href=[\'"]([^\'"]+?/publications/[^\'"]+?)[\'"]', html)
            print(f"Found {len(links)} links:")
            for l in list(dict.fromkeys(links))[:5]:
                print(f"  {l}")
                # Probe this publication page for files
                probe_pub(l)
    except Exception as e:
        print(f"Error: {e}")

def probe_pub(pub_url):
    try:
        req = urllib.request.Request(pub_url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            html = r.read().decode('utf-8', errors='ignore')
            files = re.findall(r'href=[\'"]([^\'"]+?/ws/files/[^\'"]+?\.pdf)[\'"]', html)
            if files:
                print(f"    --> Found PDF file: {files[0]}")
    except Exception as e:
        pass

search_uva("4D printing")
search_uva("Mehrpouya")
search_uva("Barletta")
search_uva("Wang shape memory")
