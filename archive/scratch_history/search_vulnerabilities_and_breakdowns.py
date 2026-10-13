import json
import subprocess
import sys
from pathlib import Path

OPENALEX_CLI = r"C:\Users\MANAS\.gemini\config\plugins\science\skills\literature_search_openalex\scripts\openalex_cli.py"
EUROPEPMC_CLI = r"C:\Users\MANAS\.gemini\config\plugins\science\skills\literature_search_europepmc\scripts\europepmc_api.py"

VULNERABILITY_QUERIES = {
    "r_stdp_instabilities": [
        "spike timing dependent plasticity runaway instability homeostatic scaling",
        "reward modulated STDP credit assignment drift noise",
        "synaptic saturation silent synapses neuromorphic learning failure"
    ],
    "hdc_capacity_limits": [
        "hyperdimensional computing capacity limits clean up memory noise",
        "vector symbolic architecture bundling saturation crosstalk",
        "sparse distributed memory capacity catastrophic forgetting"
    ],
    "replay_sleep_vulnerabilities": [
        "hippocampal replay catastrophic forgetting hallucination neural network",
        "synaptic homeostasis hypothesis sleep over pruning",
        "two stage memory consolidation interference catastrophic"
    ],
    "persistence_compounding_breakdowns": [
        "continual learning catastrophic forgetting drift benchmark",
        "lifelong learning state persistence drift degradation",
        "epigenetic robotics developmental decay stability"
    ]
}

def query_openalex(query, max_results=5):
    cmd = [
        "uv", "run", OPENALEX_CLI, "filter", "works",
        "--search", query,
        "--select", "id,doi,title,publication_year,cited_by_count,primary_topic",
        "--sort", "cited_by_count:desc",
        "--per-page", str(max_results)
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        results = []
        for item in data.get("results", []):
            results.append({
                "source": "OpenAlex",
                "id": item.get("id"),
                "doi": item.get("doi"),
                "title": item.get("title"),
                "year": item.get("publication_year"),
                "citations": item.get("cited_by_count"),
                "topic": item.get("primary_topic", {}).get("display_name") if item.get("primary_topic") else None
            })
        return results
    except Exception as e:
        print(f"Error {query}: {e}", file=sys.stderr)
        return []

def query_europepmc(query, max_results=3):
    out_file = Path(r"d:\ebca\scratch\temp_vulnerability_epmc.json")
    cmd = [
        "uv", "run", EUROPEPMC_CLI, "search",
        query,
        "--max_results", str(max_results),
        "--sort", "CITED desc",
        "--output", str(out_file)
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        if out_file.exists():
            with open(out_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            results = []
            for item in data.get("results", []):
                results.append({
                    "source": "EuropePMC",
                    "id": item.get("id"),
                    "doi": item.get("doi"),
                    "title": item.get("title"),
                    "year": item.get("pubYear"),
                    "citations": item.get("citedByCount")
                })
            return results
    except Exception as e:
        print(f"EuropePMC error {query}: {e}", file=sys.stderr)
        return []

def main():
    survey = {}
    for cat, queries in VULNERABILITY_QUERIES.items():
        survey[cat] = {}
        for q in queries:
            print(f"Harvesting vulnerability literature: {q}")
            oa = query_openalex(q, max_results=4)
            ep = query_europepmc(q, max_results=3)
            # deduplicate
            seen = set()
            combined = []
            for item in oa + ep:
                ident = (item.get("doi") or item.get("title") or "").lower().strip()
                if ident and ident not in seen:
                    seen.add(ident)
                    combined.append(item)
            survey[cat][q] = combined
            print(f"  Got {len(combined)} papers.")

    out_file = Path(r"d:\ebca\scratch\vulnerabilities_literature.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(survey, f, indent=2)
    print(f"\nSaved vulnerability survey to {out_file}")

if __name__ == "__main__":
    main()
