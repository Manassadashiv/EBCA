import urllib.request
import ssl
import os

ctx = ssl._create_unverified_context()

def download(url, dest):
    print(f"Downloading from {url} to {dest}...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            content = resp.read()
            # Verify if it's a valid PDF (starts with %PDF)
            if content.startswith(b'%PDF'):
                with open(dest, 'wb') as f:
                    f.write(content)
                size_kb = len(content) / 1024
                print(f" SUCCESS! Saved {dest} ({size_kb:.1f} KB, valid PDF)")
                return True
            else:
                print(f" FAILED: Response is not a PDF (header: {content[:30]})")
                return False
    except Exception as e:
        print(f" FAILED with error: {e}")
        return False

# Test P1-3
download('https://www.researchsquare.com/article/rs-7454600/latest.pdf', 'D:/Literature_PDFs/Project1/P1-3_Pisaneschi_2026_PostPrintAnnealing_PLA_SMA.pdf')

# Test P2-5
download('https://hal.science/hal-03492410v1/file/S0264127520304457.pdf', 'D:/Literature_PDFs/Project2/P2-5_LeDuigou_2020_Review_3D4D_NaturalFibre_Biocomposites.pdf')
