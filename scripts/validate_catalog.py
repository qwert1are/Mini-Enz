"""
MiniEnz: Final enzyme catalog with validated PDB data.
Reads PDB files directly for accurate chain/residue counts.
"""
import os, json, sys
sys.stdout.reconfigure(encoding='utf-8')

# Final 8-enzyme list with catalytic residues
# Replaced: 1CBG→1TIM, 1LBS→3LIP, 1ALK→1CA2
ENZYMES = [
    {
        "pdb": "1LSE", "name": "Hen Egg Lysozyme", "ec": "3.2.1.17",
        "fold": "alpha+beta (lysozyme-like)",
        "catalytic": [35, 52], "cat_names": ["Glu35", "Asp52"],
        "cat_type": "acid-base pair",
        "cofactors": [],
        "active_site": "surface cleft",
        "difficulty": "easy",
        "notes": "Smallest enzyme (129aa). Tests extreme miniaturization."
    },
    {
        "pdb": "1SBT", "name": "Subtilisin BPN'", "ec": "3.4.21.62",
        "fold": "alpha/beta sandwich (subtilisin-like)",
        "catalytic": [32, 64, 221], "cat_names": ["Asp32", "His64", "Ser221"],
        "cat_type": "catalytic triad",
        "cofactors": [],
        "active_site": "shallow surface pocket",
        "difficulty": "moderate",
        "notes": "Well-studied serine protease. Benchmark for triad enzymes."
    },
    {
        "pdb": "1BTL", "name": "TEM-1 Beta-Lactamase", "ec": "3.5.2.6",
        "fold": "alpha/beta (DD-peptidase fold)",
        "catalytic": [70, 73, 130, 166], "cat_names": ["Ser70", "Lys73", "Ser130", "Glu166"],
        "cat_type": "serine hydrolase (SDN motif)",
        "cofactors": [],
        "active_site": "deep pocket at domain interface",
        "difficulty": "moderate",
        "notes": "Two-domain enzyme. Tests domain-level miniaturization."
    },
    {
        "pdb": "1TIM", "name": "Triosephosphate Isomerase", "ec": "5.3.1.1",
        "fold": "(beta/alpha)8 TIM barrel",
        "catalytic": [95, 165], "cat_names": ["His95", "Glu165"],
        "cat_type": "acid-base pair",
        "cofactors": [],
        "active_site": "pocket at C-terminal end of beta-barrel",
        "difficulty": "moderate",
        "notes": "Canonical TIM barrel. Tests loop-based active site."
    },
    {
        "pdb": "1GAL", "name": "Glucose Oxidase", "ec": "1.1.3.4",
        "fold": "FAD-binding domain + substrate domain",
        "catalytic": [516, 559], "cat_names": ["His516", "His559"],
        "cat_type": "FAD-dependent dehydrogenase",
        "cofactors": ["FAD"],
        "active_site": "deep pocket with FAD",
        "difficulty": "hard",
        "notes": "Largest (583aa). Cofactor stress-test case."
    },
    {
        "pdb": "3LIP", "name": "P. cepacia Lipase", "ec": "3.1.1.3",
        "fold": "alpha/beta hydrolase fold",
        "catalytic": [87, 264, 286], "cat_names": ["Ser87", "Asp264", "His286"],
        "cat_type": "catalytic triad",
        "cofactors": [],
        "active_site": "buried pocket (lid-gated)",
        "difficulty": "moderate",
        "notes": "Lid domain may need to be removed/redesigned."
    },
    {
        "pdb": "1CA2", "name": "Human Carbonic Anhydrase II", "ec": "4.2.1.1",
        "fold": "all-beta (10-strand twisted sheet)",
        "catalytic": [94, 96, 119, 199, 106], "cat_names": ["His94", "His96", "His119", "Thr199", "Glu106"],
        "cat_type": "Zn-metalloenzyme",
        "cofactors": ["Zn2+"],
        "active_site": "deep conical pocket",
        "difficulty": "hard",
        "notes": "All-beta fold. Single metal cofactor. Good fold diversity."
    },
    {
        "pdb": "2AE2", "name": "Tropinone Reductase-II", "ec": "1.1.1.184",
        "fold": "Rossmann fold (SDR family)",
        "catalytic": [139, 155, 159], "cat_names": ["Ser139", "Tyr155", "Lys159"],
        "cat_type": "catalytic triad + cofactor",
        "cofactors": ["NADP+"],
        "active_site": "Rossmann cofactor-binding cleft",
        "difficulty": "hard",
        "notes": "SDR fold — largest enzyme family. Cofactor challenge."
    },
]

def read_pdb_info(pdb_path):
    """Parse PDB for chain info, sequence length, and residue ranges."""
    chains = {}
    current_chain = None
    for line in open(pdb_path):
        if line.startswith("ATOM") or line.startswith("HETATM"):
            chain = line[21]
            resi = int(line[22:26].strip())
            if chain not in chains:
                chains[chain] = set()
            chains[chain].add(resi)
    
    result = []
    for chain, residues in sorted(chains.items()):
        if residues:
            result.append({
                "chain": chain,
                "residues": len(residues),
                "range": f"{min(residues)}-{max(residues)}"
            })
    return result

pdb_dir = r"H:\eazyclaw\saved\MiniEnz_Methodology\data\pdbs"

print("=" * 80)
print("MiniEnz — Final Enzyme Catalog")
print("=" * 80)

for i, enz in enumerate(ENZYMES):
    pid = enz["pdb"]
    pdb_path = os.path.join(pdb_dir, f"{pid}.pdb")
    chains = read_pdb_info(pdb_path)
    
    print(f"\n{'─' * 60}")
    print(f"  #{i+1}  {pid}  {enz['name']}")
    print(f"{'─' * 60}")
    print(f"  EC: {enz['ec']}  |  Fold: {enz['fold']}")
    print(f"  Difficulty: {enz['difficulty'].upper()}")
    print(f"  Active site: {enz['active_site']}")
    print(f"  Catalytic residues: {', '.join(f'{n}({r})' for r, n in zip(enz['catalytic'], enz['cat_names']))}")
    print(f"  Cofactors: {enz['cofactors'] if enz['cofactors'] else 'none'}")
    print(f"  PDB chains: ")
    for c in chains:
        print(f"    Chain {c['chain']}: {c['residues']} residues ({c['range']})")
    print(f"  Notes: {enz['notes']}")

# Save as JSON for pipeline
output_path = r"H:\eazyclaw\saved\MiniEnz_Methodology\data\enzyme_catalog.json"
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(ENZYMES, f, indent=2, ensure_ascii=False)
print(f"\n{'=' * 80}")
print(f"Catalog saved to {output_path}")
print(f"Total enzymes: {len(ENZYMES)}")
print("=" * 80)
