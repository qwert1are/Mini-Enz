"""Validate catalytic residues in PDB structures and generate chain info."""
from Bio.PDB import PDBParser
import os, json

parser = PDBParser(QUIET=True)
pdb_dir = "/mnt/h/eazyclaw/saved/MiniEnz_Methodology/data/pdbs"

TARGETS = {
    "1LSE": {"chain": "A", "cat_res": [35, 52], "name": "lysozyme"},
    "1SBT": {"chain": "A", "cat_res": [32, 64, 221], "name": "subtilisin"},
    "1BTL": {"chain": "A", "cat_res": [70, 73, 130, 166], "name": "tem1_blactamase"},
    "1TIM": {"chain": "A", "cat_res": [95, 165], "name": "tim"},
    "1GAL": {"chain": "A", "cat_res": [516, 559], "name": "glucose_oxidase"},
    "3LIP": {"chain": "A", "cat_res": [87, 264, 286], "name": "pc_lipase"},
    "1CA2": {"chain": "A", "cat_res": [94, 96, 119, 199, 106], "name": "ca2"},
    "2AE2": {"chain": "A", "cat_res": [139, 155, 159], "name": "tropinone_reductase"},
}

output = {}
for pid, info in TARGETS.items():
    pdb_path = os.path.join(pdb_dir, pid + ".pdb")
    s = parser.get_structure(pid, pdb_path)
    chain = s[0][info["chain"]]
    residues = [(r.get_id()[1], r.get_resname()) 
                for r in chain if r.get_id()[0] == " " and "CA" in r]
    
    cat_confirmed = []
    for rnum in info["cat_res"]:
        found = [r for r in residues if r[0] == rnum]
        if found:
            cat_confirmed.append((rnum, found[0][1]))
        else:
            print("WARNING: {} catalytic residue {} not found!".format(pid, rnum))
    
    first = residues[0][0]
    last = residues[-1][0]
    total = len(residues)
    
    output[pid] = {
        "name": info["name"],
        "chain": info["chain"],
        "residue_range": "{}-{}".format(first, last),
        "total_residues": total,
        "catalytic_confirmed": cat_confirmed,
        "first_res": first,
        "last_res": last,
    }
    
    print("{} ({}): {}aa, cat residues OK".format(pid, info["name"], total))
    for cr in cat_confirmed:
        print("  Res {}: {}".format(cr[0], cr[1]))

with open("/mnt/h/eazyclaw/saved/MiniEnz_Methodology/data/chain_info.json", "w") as f:
    json.dump(output, f, indent=2)
print("\nSaved to chain_info.json")
