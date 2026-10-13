"""
Inspect and summarize all retrieved literature survey results for Stage 3.7.
Categorizes by pillar and extracts key papers with links, DOIs, and mechanisms.
"""
import json
from pathlib import Path

DATA_DIR = Path(r"D:\ebca\scratch\stage3_7_lit")

def process_all():
    summary_data = {}
    json_files = sorted(DATA_DIR.glob("*.json"))
    
    for f in json_files:
        tag = f.stem
        try:
            content = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
            
        papers = []
        if "papers" in content:  # arXiv format
            for p in content["papers"]:
                papers.append({
                    "title": p.get("title", "").replace("\n", " "),
                    "authors": ", ".join(p.get("authors", [])[:3]),
                    "year": p.get("published", "")[:4],
                    "url": p.get("pdf_url", "") or f"https://arxiv.org/abs/{p.get('id', '')}",
                    "doi": p.get("doi", ""),
                    "summary": (p.get("summary", "") or "")[:280].replace("\n", " "),
                    "source": "arXiv"
                })
        elif "results" in content and isinstance(content["results"], list):
            # Europe PMC format or OpenAlex format
            for p in content["results"]:
                if "title" in p and "authorString" in p:  # Europe PMC
                    doi = p.get("doi", "")
                    url = f"https://doi.org/{doi}" if doi else f"https://europepmc.org/article/MED/{p.get('id', '')}"
                    papers.append({
                        "title": p.get("title", "").replace("\n", " "),
                        "authors": (p.get("authorString", "") or "")[:40],
                        "year": str(p.get("pubYear", "")),
                        "url": url,
                        "doi": doi,
                        "summary": (p.get("abstractText", "") or "")[:280].replace("\n", " "),
                        "source": "Europe PMC"
                    })
                elif "display_name" in p or "title" in p:  # OpenAlex
                    doi = p.get("doi", "")
                    url = doi if doi else p.get("id", "")
                    papers.append({
                        "title": (p.get("title") or p.get("display_name") or "").replace("\n", " "),
                        "authors": f"Cited by: {p.get('cited_by_count', 0)}",
                        "year": str(p.get("publication_year", "")),
                        "url": url,
                        "doi": doi,
                        "summary": f"Primary topic: {p.get('primary_topic', {}).get('display_name', 'N/A') if isinstance(p.get('primary_topic'), dict) else 'N/A'}",
                        "source": "OpenAlex"
                    })
        elif isinstance(content, list): # Direct list (OpenAlex CLI sometimes)
            for p in content:
                doi = p.get("doi", "")
                url = doi if doi else p.get("id", "")
                papers.append({
                    "title": (p.get("title") or p.get("display_name") or "").replace("\n", " "),
                    "authors": f"Cited by: {p.get('cited_by_count', 0)}",
                    "year": str(p.get("publication_year", "")),
                    "url": url,
                    "doi": doi,
                    "summary": f"Primary topic: {p.get('primary_topic', {}).get('display_name', 'N/A') if isinstance(p.get('primary_topic'), dict) else 'N/A'}",
                    "source": "OpenAlex"
                })

        summary_data[tag] = papers
        print(f"[{tag}] Processed {len(papers)} papers")
        
    out_file = DATA_DIR / "master_literature_summary.json"
    out_file.write_text(json.dumps(summary_data, indent=2), encoding="utf-8")
    print(f"\nMaster summary written to {out_file.name} with {len(summary_data)} categories.")

if __name__ == "__main__":
    process_all()
