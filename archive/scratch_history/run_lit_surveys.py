"""
Orchestrates scientific literature search queries for Stage 3.7.
Uses exact argument lists to avoid Windows PowerShell quote stripping.
Ensures SSL_CERT_FILE is set to certifi's CA bundle.
"""
import os
import sys
import json
import subprocess
from pathlib import Path
import certifi

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

SKILLS_DIR = Path(r"C:\Users\MANAS\.gemini\config\plugins\science\skills")
SCRATCH_DIR = Path(r"D:\ebca\scratch\stage3_7_lit")
SCRATCH_DIR.mkdir(parents=True, exist_ok=True)

ARXIV_SCRIPT = SKILLS_DIR / "literature_search_arxiv" / "scripts" / "search_arxiv.py"
EPMC_SCRIPT = SKILLS_DIR / "literature_search_europepmc" / "scripts" / "europepmc_api.py"
OPENALEX_SCRIPT = SKILLS_DIR / "literature_search_openalex" / "scripts" / "openalex_cli.py"

def run_arxiv(query: str, max_results: int = 6, tag: str = "arxiv") -> dict:
    out_file = SCRATCH_DIR / f"{tag}.json"
    print(f"\n[arXiv] Querying: {query} (max={max_results})")
    cmd = ["uv", "run", str(ARXIV_SCRIPT), "--query", query, "--max_results", str(max_results)]
    res = subprocess.run(cmd, capture_output=True, text=True, env=os.environ)
    if res.returncode != 0:
        print(f"[arXiv ERROR] {res.stderr[:300]}")
        return {}
    try:
        # Extract last JSON block from stdout
        out = res.stdout.strip()
        # Find start of JSON
        idx = out.rfind('{\n  "status":')
        if idx != -1:
            data = json.loads(out[idx:])
        else:
            data = json.loads(out)
        out_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        count = len(data.get("papers", []))
        print(f"[arXiv SUCCESS] Saved {count} papers to {out_file.name}")
        return data
    except Exception as e:
        print(f"[arXiv Parse Error] {e}\nOutput snippet: {res.stdout[:200]}")
        return {}

def run_epmc(query: str, max_results: int = 6, tag: str = "epmc") -> dict:
    out_file = SCRATCH_DIR / f"{tag}.json"
    print(f"\n[Europe PMC] Querying: {query} (max={max_results})")
    cmd = ["uv", "run", str(EPMC_SCRIPT), "search", query, "--max_results", str(max_results), "--output", str(out_file)]
    res = subprocess.run(cmd, capture_output=True, text=True, env=os.environ)
    if res.returncode != 0:
        print(f"[Europe PMC ERROR] {res.stderr[:300]}")
        return {}
    if out_file.exists():
        data = json.loads(out_file.read_text(encoding="utf-8"))
        count = len(data.get("results", []))
        print(f"[Europe PMC SUCCESS] Saved {count} papers to {out_file.name}")
        return data
    return {}

def run_openalex(entity: str, search_query: str, per_page: int = 6, tag: str = "openalex") -> dict:
    out_file = SCRATCH_DIR / f"{tag}.json"
    print(f"\n[OpenAlex] Searching {entity}: {search_query} (per_page={per_page})")
    cmd = ["uv", "run", str(OPENALEX_SCRIPT), "filter", entity, "--search", search_query, "--per-page", str(per_page),
           "--select", "id,doi,title,publication_year,cited_by_count,primary_topic,abstract_inverted_index"]
    res = subprocess.run(cmd, capture_output=True, text=True, env=os.environ)
    if res.returncode != 0:
        print(f"[OpenAlex ERROR] {res.stderr[:300]}")
        return {}
    try:
        data = json.loads(res.stdout)
        out_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        results = data if isinstance(data, list) else data.get("results", [])
        print(f"[OpenAlex SUCCESS] Saved {len(results)} works to {out_file.name}")
        return data
    except Exception as e:
        print(f"[OpenAlex Parse Error] {e}\nStdout: {res.stdout[:200]}")
        return {}

if __name__ == "__main__":
    print("Starting Comprehensive Deep Literature Survey for Stage 3.7...\n")
    
    # ── PILLAR 1: Active Vision, Active Inference & Visual Saccades ──
    run_arxiv('ti:"active inference" AND (all:saccade OR all:gaze OR all:fovea)', max_results=6, tag="p1_arxiv_active_inf_saccades")
    run_arxiv('all:"predictive coding" AND ti:"visual cortex"', max_results=6, tag="p1_arxiv_predictive_coding_vision")
    run_epmc('TITLE:"active vision" OR TITLE:"active inference" AND (saccade OR gaze)', max_results=6, tag="p1_epmc_active_gaze")
    run_openalex("works", "active inference visual saccade foveation", per_page=6, tag="p1_openalex_active_inf_gaze")
    
    # ── PILLAR 2: Subcortical Midbrain & Optic Tectum / Superior Colliculus ──
    run_epmc('TITLE:"superior colliculus" AND gaze AND orienting', max_results=6, tag="p2_epmc_superior_colliculus")
    run_epmc('TITLE:"optic tectum" AND (navigation OR prey OR orienting)', max_results=6, tag="p2_epmc_optic_tectum")
    run_openalex("works", "superior colliculus visual orienting active gaze", per_page=6, tag="p2_openalex_superior_colliculus")
    
    # ── PILLAR 3: Sensorimotor Contingencies, Reafference & Efference Copy ──
    run_epmc('"sensorimotor contingencies" AND vision', max_results=6, tag="p3_epmc_sensorimotor_contingencies")
    run_epmc('"corollary discharge" OR "efference copy" AND visual', max_results=6, tag="p3_epmc_corollary_discharge")
    run_openalex("works", "sensorimotor contingencies visual consciousness o'regan", per_page=6, tag="p3_openalex_sensorimotor_contingencies")
    run_arxiv('all:"sensorimotor contingencies" AND all:robot', max_results=6, tag="p3_arxiv_sensorimotor_robotics")

    # ── PILLAR 4: Cybernetics, Ancient Autonomous Agents & Autopoiesis ──
    run_openalex("works", "grey walter machina speculatrix tortoise", per_page=5, tag="p4_openalex_grey_walter")
    run_openalex("works", "ross ashby homeostat ultrastability", per_page=5, tag="p4_openalex_ashby_homeostat")
    run_openalex("works", "autopoiesis maturana varela living systems", per_page=5, tag="p4_openalex_autopoiesis")
    run_openalex("works", "braitenberg vehicles synthetic psychology", per_page=5, tag="p4_openalex_braitenberg")

    # ── PILLAR 5: Theories of Artificial & Emergent Consciousness ──
    run_openalex("works", "global neuronal workspace consciousness dehaene", per_page=6, tag="p5_openalex_global_workspace")
    run_openalex("works", "integrated information theory consciousness tononi", per_page=6, tag="p5_openalex_iit")
    run_openalex("works", "attention schema theory consciousness graziano", per_page=6, tag="p5_openalex_attention_schema")
    run_epmc('TITLE:"artificial consciousness" OR TITLE:"machine consciousness"', max_results=6, tag="p5_epmc_artificial_consciousness")
    run_arxiv('all:"artificial consciousness" OR all:"machine consciousness"', max_results=6, tag="p5_arxiv_artificial_consciousness")

    # ── PILLAR 6: Neuromorphic Active Vision & Foveation in Robotics ──
    run_arxiv('ti:foveated OR ti:"log-polar" AND all:robot', max_results=6, tag="p6_arxiv_foveated_robotics")
    run_openalex("works", "neuromorphic foveated vision active gaze robotics", per_page=6, tag="p6_openalex_foveated_vision")

    print("\nDeep Literature Survey Execution Finished!")

