"""
Fetch PDB metadata for replacement structures: 1TIM, 3LIP, 1CA2
"""
import requests
import json
import os
from urllib.request import urlretrieve
import sys
sys.stdout.reconfigure(encoding='utf-8')

REPLACEMENTS = [
    ("1TIM", "Triosephosphate isomerase"),
    ("3LIP", "P. cepacia lipase"),
    ("1CA2", "Carbonic anhydrase II"),
]

output_dir = r"H:\eazyclaw\saved\MiniEnz_Methodology\data"

for pid, name in REPLACEMENTS:
    print(f"{pid} ({name}):")
    try:
        r = requests.get(f"https://data.rcsb.org/rest/v1/core/entry/{pid}", timeout=15)
        if r.status_code == 200:
            data = r.json()
            title = data.get("struct", {}).get("title", "N/A")
            res_list = data.get("rcsb_entry_info", {}).get("resolution_combined", [])
            res = res_list[0] if res_list else "N/A"
            
            # Count chains
            chains = []
            total = 0
            for eid, entity in data.get("polymer_entities", {}).items():
                if entity.get("entity_poly", {}).get("rcsb_entity_polymer_type") == "Protein":
                    n = entity.get("entity_poly", {}).get("rcsb_sample_sequence_length", 0)
                    chains.append((eid, n))
                    total += n
            print(f"  Resolution: {res}A, Total protein: {total}aa")
            print(f"  Chains: {chains}")
            print(f"  Title: {title[:120]}")
        else:
            print(f"  API: {r.status_code}")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Download
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

print("Done.")
