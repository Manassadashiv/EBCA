import urllib.request
import urllib.parse
import json
import ssl

ctx = ssl._create_unverified_context()

papers = [
    {
        'id': 'P1-1',
        'title': 'An experimental investigation on performance of NiTi-based shape memory alloy 4D printed actuators for bending application',
        'doi': '10.1007/s00170-022-09875-w'
    },
    {
        'id': 'P1-2',
        'title': 'A study of the functional capabilities of shape memory alloy-based 4D printed analogous bending actuators',
        'doi': '10.1007/s40964-023-00456-1'
    },
    {
        'id': 'P1-3',
        'title': 'Post-print annealing: a simple strategy for enhancing adhesion in FDM-printed PLA-SMA composites',
        'doi': '10.1088/1361-665X/ae4ae9'
    },
    {
        'id': 'P1-4',
        'title': '4D-printing of hybrid composites: integration of shape memory alloy wires on material level using SLA printing technique',
        'doi': ''
    },
    {
        'id': 'P1-5',
        'title': '4D printing of reusable mechanical metamaterial energy absorber, experimental and numerical investigation',
        'doi': '10.1088/1361-665X/addead'
    },
    {
        'id': 'P2-1',
        'title': 'Programming multistage shape memory and variable recovery force with 4D printing parameters',
        'doi': '10.1002/admt.201900535'
    },
    {
        'id': 'P2-2',
        'title': '4D printing of shape memory polylactic acid (PLA)',
        'doi': '10.1016/j.polymer.2021.124080'
    },
    {
        'id': 'P2-3',
        'title': 'Statistical analysis of mechanical properties of wood-PLA composites prepared via additive manufacturing',
        'doi': '10.1080/1023666X.2019.1630940'
    },
    {
        'id': 'P2-4',
        'title': '4D printing of shape memory polylactic acid (PLA) components: investigating the role of the operational parameters in fused deposition modelling (FDM)',
        'doi': '10.1016/j.jmapro.2020.11.036'
    },
    {
        'id': 'P2-5',
        'title': 'A review of 3D and 4D printing of natural fibre biocomposites',
        'doi': '10.1016/j.matdes.2020.108911'
    },
    {
        'id': 'P2-6',
        'title': 'Effect of printing layer thickness on water absorption and mechanical properties of 3D-printed wood/PLA composite materials',
        'doi': '10.1007/s00170-019-03299-9'
    }
]

results = {}

for p in papers:
    pid = p['id']
    doi = p['doi']
    title = p['title']
    print(f"=== Checking {pid} ===", flush=True)
    info = {'doi': doi, 'title': title, 'oa_urls': []}
    
    # 1. OpenAlex
    try:
        if doi:
            oa_url = f"https://api.openalex.org/works/https://doi.org/{doi}"
        else:
            oa_url = f"https://api.openalex.org/works?filter=title.search:{urllib.parse.quote(title)}"
        
        req = urllib.request.Request(oa_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            work = data if doi else (data.get('results', [{}])[0] if data.get('results') else {})
            info['openalex'] = {
                'id': work.get('id'),
                'title': work.get('title'),
                'is_oa': work.get('open_access', {}).get('is_oa'),
                'oa_status': work.get('open_access', {}).get('oa_status'),
                'oa_url': work.get('open_access', {}).get('oa_url'),
                'best_oa_location': work.get('best_oa_location')
            }
            if work.get('best_oa_location', {}).get('pdf_url'):
                info['oa_urls'].append(('openalex_best_pdf', work['best_oa_location']['pdf_url']))
            for loc in work.get('locations', []):
                if loc.get('pdf_url'):
                    info['oa_urls'].append(('openalex_loc_pdf', loc['pdf_url']))
                elif loc.get('landing_page_url'):
                    info['oa_urls'].append(('openalex_loc_landing', loc['landing_page_url']))
    except Exception as e:
        info['openalex_err'] = str(e)
        
    # 2. Unpaywall (if doi)
    if doi:
        try:
            upw_url = f"https://api.unpaywall.org/v2/{doi}?email=user@academic.edu"
            req = urllib.request.Request(upw_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                info['unpaywall'] = {
                    'is_oa': data.get('is_oa'),
                    'oa_status': data.get('oa_status'),
                    'best_oa_location': data.get('best_oa_location')
                }
                if data.get('best_oa_location', {}).get('url_for_pdf'):
                    info['oa_urls'].append(('unpaywall_pdf', data['best_oa_location']['url_for_pdf']))
                for loc in data.get('oa_locations', []):
                    if loc.get('url_for_pdf'):
                        info['oa_urls'].append(('unpaywall_loc_pdf', loc['url_for_pdf']))
        except Exception as e:
            info['unpaywall_err'] = str(e)
            
    # 3. Europe PMC
    try:
        query = f"DOI:{doi}" if doi else f'TITLE:"{title}"'
        epmc_url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={urllib.parse.quote(query)}&format=json"
        req = urllib.request.Request(epmc_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            results_list = data.get('resultList', {}).get('result', [])
            if results_list:
                item = results_list[0]
                info['europepmc'] = {
                    'id': item.get('id'),
                    'pmcid': item.get('pmcid'),
                    'isOpenAccess': item.get('isOpenAccess'),
                    'hasPDF': item.get('hasPDF')
                }
                if item.get('pmcid'):
                    info['oa_urls'].append(('epmc_pmcid_pdf', f"https://www.ebi.ac.uk/europepmc/webservices/rest/{item['pmcid']}/fullTextXML"))
    except Exception as e:
        info['europepmc_err'] = str(e)

    results[pid] = info
    print(f"{pid}: is_oa={info.get('openalex', {}).get('is_oa')}, oa_urls={len(info.get('oa_urls', []))}", flush=True)

with open('D:/Literature_PDFs/oa_discovery.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\nAll done! Saved discovery to D:/Literature_PDFs/oa_discovery.json", flush=True)
