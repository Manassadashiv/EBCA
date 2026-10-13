import subprocess
import json
from pathlib import Path

OPENALEX_CLI = r"C:\Users\MANAS\.gemini\config\plugins\science\skills\literature_search_openalex\scripts\openalex_cli.py"

specific_queries = [
    "Izhikevich Solving the distal reward problem through linkage of STDP and dopamine",
    "Fremaux Gerstner Neuromodulated Spike-Timing-Dependent Plasticity Three-Factor",
    "Kanerva Hyperdimensional Computing An Introduction to Computing in Distributed Representation",
    "Tony Plate Holographic Reduced Representations Distributed representations",
    "McClelland complementary learning systems hippocampus neocortex",
    "Tononi Cirelli Sleep and the Price of Plasticity Synaptic Homeostasis",
    "Maturana Varela Autopoiesis and Cognition The Realization of the Living",
    "Michael Levin Technological Approach to Mind Everywhere TAME",
    "Consciousness in Artificial Intelligence Insights from the Science of Consciousness Bengio Long"
]

res_list = []
for q in specific_queries:
    cmd = [
        "uv", "run", OPENALEX_CLI, "filter", "works",
        "--search", q,
        "--select", "id,doi,title,publication_year,cited_by_count,primary_topic",
        "--per-page", "2"
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        for item in data.get("results", []):
            res_list.append({
                "query": q,
                "id": item.get("id"),
                "doi": item.get("doi"),
                "title": item.get("title"),
                "year": item.get("publication_year"),
                "citations": item.get("cited_by_count")
            })
            print(f"[{item.get('publication_year')}] {item.get('title')} (Cited: {item.get('cited_by_count')})")
    except Exception as e:
        print(f"Error {q}: {e}")

with open(r"d:\ebca\scratch\targeted_papers.json", "w", encoding="utf-8") as f:
    json.dump(res_list, f, indent=2)

print(f"Saved {len(res_list)} targeted landmark papers.")
