import os
import sys
import json
import subprocess
from pathlib import Path

OPENALEX_CLI = r"C:\Users\MANAS\.gemini\config\plugins\science\skills\literature_search_openalex\scripts\openalex_cli.py"
EUROPEPMC_CLI = r"C:\Users\MANAS\.gemini\config\plugins\science\skills\literature_search_europepmc\scripts\europepmc_api.py"

TOPICS = {
    "4.1_synaptic_plasticity": [
        "reward modulated spike timing dependent plasticity",
        "three factor learning rule neuromodulation eligibility traces",
        "homeostatic synaptic scaling Turrigiano stability",
        "biological credit assignment backpropagation without gradient"
    ],
    "4.2_hdc_episodic_memory": [
        "hyperdimensional computing episodic memory continual learning",
        "vector symbolic architecture catastrophic forgetting",
        "sparse distributed memory Kanerva associative memory",
        "holographic reduced representations cognitive architecture"
    ],
    "4.3_memory_consolidation_replay": [
        "hippocampal sharp wave ripples memory consolidation replay",
        "complementary learning systems McClelland memory replay",
        "synaptic homeostasis hypothesis sleep Tononi Cirelli",
        "reverse replay neuromorphic offline learning"
    ],
    "4.4_autopoiesis_lifelong_persistence": [
        "autopoiesis Maturana Varela living systems autonomy",
        "lifelong developmental robotics state persistence",
        "dissipative structures self organization living systems",
        "embodied cognitive architecture identity continuity"
    ],
    "frontier_artificial_consciousness_emergence": [
        "integrated information theory consciousness Tononi",
        "global neuronal workspace theory conscious access Dehaene",
        "active inference selfhood Markov blanket Friston",
        "attention schema theory self modeling Graziano",
        "artificial consciousness criteria tests empirical"
    ]
}

def query_openalex(query, max_results=10):
    cmd = [
        "uv", "run", OPENALEX_CLI, "filter", "works",
        "--search", query,
        "--select", "id,doi,title,publication_year,cited_by_count,primary_topic,abstract_inverted_index",
        "--sort", "cited_by_count:desc",
        "--per-page", str(max_results)
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        results = []
        for item in data.get("results", []):
            # reconstruct abstract if available
            abstract = ""
            inv = item.get("abstract_inverted_index")
            if inv:
                words = {}
                for w, pos_list in inv.items():
                    for pos in pos_list:
                        words[pos] = w
                abstract = " ".join([words[i] for i in sorted(words.keys())])
            results.append({
                "source_db": "OpenAlex",
                "id": item.get("id"),
                "doi": item.get("doi"),
                "title": item.get("title"),
                "year": item.get("publication_year"),
                "citations": item.get("cited_by_count"),
                "topic": item.get("primary_topic", {}).get("display_name") if item.get("primary_topic") else None,
                "abstract": abstract[:600] + ("..." if len(abstract) > 600 else "")
            })
        return results
    except Exception as e:
        print(f"OpenAlex error on '{query}': {e}", file=sys.stderr)
        return []

def query_europepmc(query, max_results=5):
    out_file = Path(r"d:\ebca\scratch\temp_epmc.json")
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
                    "source_db": "EuropePMC",
                    "id": item.get("id"),
                    "doi": item.get("doi"),
                    "title": item.get("title"),
                    "year": item.get("pubYear"),
                    "citations": item.get("citedByCount"),
                    "pmcid": item.get("pmcid"),
                    "abstract": (item.get("abstractText") or "")[:600] + ("..." if len(item.get("abstractText") or "") > 600 else "")
                })
            return results
    except Exception as e:
        print(f"EuropePMC error on '{query}': {e}", file=sys.stderr)
    return []

def main():
    survey_data = {}
    for topic_key, queries in TOPICS.items():
        print(f"=== Harvesting Topic: {topic_key} ===")
        survey_data[topic_key] = {}
        for q in queries:
            print(f"  Searching: {q}")
            oa_res = query_openalex(q, max_results=6)
            epmc_res = query_europepmc(q, max_results=4)
            # deduplicate by doi or title
            combined = []
            seen = set()
            for r in oa_res + epmc_res:
                ident = (r.get("doi") or r.get("title") or "").lower().strip()
                if ident and ident not in seen:
                    seen.add(ident)
                    combined.append(r)
            survey_data[topic_key][q] = combined
            print(f"    Found {len(combined)} distinct papers.")
    
    out_path = Path(r"d:\ebca\scratch\stage4_survey_data.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(survey_data, f, indent=2)
    print(f"\nAll topics harvested successfully -> {out_path}")

if __name__ == "__main__":
    main()
