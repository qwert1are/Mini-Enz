"""
Fetch PDB metadata and validate structures for MiniEnz benchmark.
"""
import requests
import json
import os
from urllib.request import urlretrieve
import sys
sys.stdout.reconfigure(encoding='utf-8')

PDB_IDS = [
    "1LSE",  # Lysozyme
    "1SBT",  # Subtilisin (serine protease)
    "1BTL",  # TEM-1 beta-lactamase
    "1CBG",  # Glycoside hydrolase
    "1GAL",  # Glucose oxidase (oxidoreductase)
    "1LBS",  # Lipase (Candida rugosa)
    "1ALK",  # Alkaline phosphatase
    "2AE2",  # Carbonyl reductase
]

output_dir = r"H:\eazyclaw\saved\MiniEnz_Methodology\data"

results = []

for pid in PDB_IDS:
    info = {"pdb": pid, "title": "", "resolution": "", "chains": [], "total_aa": 0}
    
    # Get PDB metadata
    try:
        r = requests.get(f"https://data.rcsb.org/rest/v1/core/entry/{pid}", timeout=15)
        if r.status_code == 200:
            data = r.json()
            info["title"] = data.get("struct", {}).get("title", "N/A")
            
            refine = data.get("rcsb_entry_info", {})
            res_list = refine.get("resolution_combined", [])
            info["resolution"] = res_list[0] if res_list else "N/A"
            
            # Polymer entities
            chains_detail = []
            for eid, entity in data.get("polymer_entities", {}).items():
                if entity.get("entity_poly", {}).get("rcsb_entity_polymer_type") == "Protein":
                    n = entity.get("entity_poly", {}).get("rcsb_sample_sequence_length", 0)
                    chains_detail.append(f"chain_{eid}={n}aa")
                    info["total_aa"] += n
            info["chains"] = chains_detail
            
            results.append(info)
            print(f"{pid}: {info['resolution']}A, {info['total_aa']}aa total, {'; '.join(chains_detail)}")
            print(f"  {info['title'][:100]}")
        else:
            print(f"{pid}: API returned {r.status_code}")
    except Exception as e:
        print(f"{pid}: API error - {e}")
    
    # Download PDB if needed
    pdb_path = os.path.join(output_dir, "pdbs", f"{pid}.pdb")
    if not os.path.exists(pdb_path):
        try:
            url = f"https://files.rcsb.org/download/{pid}.pdb"
            urlretrieve(url, pdb_path)
            print(f"  Downloaded: {os.path.getsize(pdb_path)/1024:.1f} KB")
        except Exception as e:
            print(f"  Download failed: {e}")
    else:
        print(f"  Already exists: {os.path.getsize(pdb_path)/1024:.1f} KB")
    print()

# Save summary
summary_path = os.path.join(output_dir, "pdb_summary.json")
with open(summary_path, 'w') as f:
    json.dump(results, f, indent=2)
print(f"Summary saved to {summary_path}")
print("Done.")
