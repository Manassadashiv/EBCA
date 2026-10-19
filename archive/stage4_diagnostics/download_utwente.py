import urllib.request
import ssl

ctx = ssl._create_unverified_context()

def download(url, dest):
    print(f"Downloading from {url} to {dest}...", flush=True)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            content = resp.read()
            if content.startswith(b'%PDF'):
                with open(dest, 'wb') as f:
                    f.write(content)
                size_kb = len(content) / 1024
                print(f" SUCCESS! Saved {dest} ({size_kb:.1f} KB, valid PDF)", flush=True)
                return True
            else:
                print(f" FAILED: Response is not a PDF (header: {content[:30]})", flush=True)
                return False
    except Exception as e:
        print(f" FAILED with error: {e}", flush=True)
        return False

# P2-2
download('https://research.utwente.nl/files/274638108/1_s2.0_S0032386121007035_main.pdf', 'D:/Literature_PDFs/Project2/P2-2_Mehrpouya_2021_4D_Printing_PLA_ShapeMemory.pdf')

# P2-4
download('https://research.utwente.nl/files/274638619/1_s2.0_S1526612520308276_main.pdf', 'D:/Literature_PDFs/Project2/P2-4_Barletta_2021_4D_PLA_FDM_Parameters.pdf')
