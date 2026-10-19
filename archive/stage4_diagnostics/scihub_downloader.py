import urllib.request
import re
import ssl
import os

ctx = ssl._create_unverified_context()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

papers = [
    ('P1-1', '10.1007/s00170-022-09875-w', 'D:/Literature_PDFs/Project1/P1-1_Sreesha_2022_NiTi_4D_Actuators_Bending.pdf'),
    ('P1-2', '10.1007/s40964-023-00456-1', 'D:/Literature_PDFs/Project1/P1-2_Ladakhan_2023_SMA_4D_Bending_Actuators.pdf'),
    ('P1-5', '10.1088/1361-665X/addead', 'D:/Literature_PDFs/Project1/P1-5_Fallah_2025_4D_Metamaterial_EnergyAbsorber.pdf'),
    ('P2-1', '10.1002/admt.201900535', 'D:/Literature_PDFs/Project2/P2-1_Wang_2019_4D_MultiStageShapeMemory.pdf'),
    ('P2-3', '10.1080/1023666X.2019.1630940', 'D:/Literature_PDFs/Project2/P2-3_Vigneshwaran_2019_WoodPLA_Mechanical.pdf'),
    ('P2-4', '10.1016/j.jmapro.2020.11.036', 'D:/Literature_PDFs/Project2/P2-4_Barletta_2021_4D_PLA_FDM_Parameters.pdf'),
    ('P2-5', '10.1016/j.matdes.2020.108911', 'D:/Literature_PDFs/Project2/P2-5_LeDuigou_2020_Review_3D4D_NaturalFibre_Biocomposites.pdf'),
    ('P2-6', '10.1007/s00170-019-03299-9', 'D:/Literature_PDFs/Project2/P2-6_Ayrilmis_2019_WoodPLA_LayerThickness.pdf')
]

for pid, doi, dest in papers:
    if os.path.exists(dest) and os.path.getsize(dest) > 10000:
        print(f"[{pid}] Already exists ({os.path.getsize(dest)} bytes), skipping.", flush=True)
        continue

    print(f"\n[{pid}] Fetching from sci-hub.st for DOI {doi}...", flush=True)
    try:
        page_url = f"https://sci-hub.st/{doi}"
        req = urllib.request.Request(page_url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
            html = r.read().decode('utf-8', errors='ignore')
            
        # Extract pdf link
        matches = re.findall(r'<embed[^>]+src=[\'"]([^\'"]+)[\'"]', html)
        if not matches:
            matches = re.findall(r'<iframe[^>]+src=[\'"]([^\'"]+)[\'"]', html)
        if not matches:
            matches = re.findall(r'onclick=[\'"]location\.href=[\'"]([^\'"]+)[\'"]', html)
        if not matches:
            matches = re.findall(r'href=[\'"]([^\'"]+\.pdf[^\'"]*)[\'"]', html)

        if matches:
            pdf_url = matches[0]
            if pdf_url.startswith('//'):
                pdf_url = 'https:' + pdf_url
            elif pdf_url.startswith('/'):
                pdf_url = 'https://sci-hub.st' + pdf_url
            
            print(f"  Found PDF URL: {pdf_url}", flush=True)
            # Download PDF
            pdf_req = urllib.request.Request(pdf_url, headers=headers)
            with urllib.request.urlopen(pdf_req, context=ctx, timeout=30) as pdf_resp:
                content = pdf_resp.read()
                if content.startswith(b'%PDF'):
                    with open(dest, 'wb') as f:
                        f.write(content)
                    print(f"  SUCCESS! Saved {dest} ({len(content)/1024:.1f} KB)", flush=True)
                else:
                    print(f"  Downloaded content is not a PDF (header: {content[:20]})", flush=True)
        else:
            print("  No PDF link found on Sci-Hub page.", flush=True)
    except Exception as e:
        print(f"  Error: {e}", flush=True)

print("\nAll downloads finished!", flush=True)
