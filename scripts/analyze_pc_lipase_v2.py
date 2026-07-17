"""
Analyze pc_lipase multi-motif designs (200-399) — compare with original (0-199)
"""
import os, glob, numpy as np

RF_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\results\rfdiffusion"
PDB_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\data\pdbs"
CAT_RES = [87, 264, 286]

def parse_ca(pdb, chain="A"):
    d = {}
    with open(pdb) as f:
        for line in f:
            if line.startswith("ATOM") and "CA" in line[12:16] and line[21] == chain:
                d[int(line[22:26].strip())] = np.array([float(line[30:38]),float(line[38:46]),float(line[46:54])])
    return d

def count_all(pdb):
    chains = {}
    with open(pdb) as f:
        for line in f:
            if line.startswith("ATOM") and "CA" in line:
                c, r = line[21], int(line[22:26].strip())
                chains.setdefault(c, set()).add(r)
    return {c: len(v) for c, v in chains.items()}, sum(len(v) for v in chains.values())

def cat_rmsd(mobile_ca, ref_ca):
    pts_m = np.array([mobile_ca[r] for r in CAT_RES if r in mobile_ca and r in ref_ca])
    pts_r = np.array([ref_ca[r] for r in CAT_RES if r in mobile_ca and r in ref_ca])
    if len(pts_m) < 3: return None
    cm, cr = pts_m.mean(0), pts_r.mean(0)
    H = (pts_m-cm).T @ (pts_r-cr)
    U, s, Vt = np.linalg.svd(H)
    R = Vt.T @ U.T
    if np.linalg.det(R) < 0: Vt[-1]*=-1; R = Vt.T @ U.T
    aligned = (pts_m-cm) @ R + cr
    return float(np.sqrt(((aligned-pts_r)**2).sum()/len(pts_m)))

native_ca = parse_ca(os.path.join(PDB_DIR, "3LIP.pdb"), "A")

# Original designs (0-199)
print("ORIGINAL (single-motif A85-268):")
orig_lengths = []
orig_rmsds = []
for i in range(200):
    pdb = os.path.join(RF_DIR, "pc_lipase_{}.pdb".format(i))
    if not os.path.exists(pdb): continue
    chains, total = count_all(pdb)
    orig_lengths.append(total)
    r = cat_rmsd(parse_ca(pdb, "A"), native_ca)
    if r: orig_rmsds.append(r)

print("  Mean total length: {:.1f} aa (native: 320)".format(np.mean(orig_lengths)))
print("  SRE: {:.1f}%".format((1-np.mean(orig_lengths)/320)*100))
print("  Cat RMSD: {:.3f}+/-{:.3f} A".format(np.mean(orig_rmsds), np.std(orig_rmsds)))

# New designs (200-399)
print("\nNEW (multi-motif A85-89/5-15/A262-266/5-15/A284-288/100-150):")
new_lengths = []
new_rmsds = []
chain_stats = {"A": [], "B": [], "C": [], "D": [], "E": []}
for i in range(200, 400):
    pdb = os.path.join(RF_DIR, "pc_lipase_{}.pdb".format(i))
    if not os.path.exists(pdb): continue
    chains, total = count_all(pdb)
    new_lengths.append(total)
    for c, n in chains.items():
        if c in chain_stats:
            chain_stats[c].append(n)
    r = cat_rmsd(parse_ca(pdb, "A"), native_ca)
    if r: new_rmsds.append(r)

print("  Chains: {}".format({c: "{:.1f}".format(np.mean(v)) for c, v in chain_stats.items() if v}))
print("  Mean total length: {:.1f} aa (native: 320)".format(np.mean(new_lengths)))
print("  SRE: {:.1f}%".format((1-np.mean(new_lengths)/320)*100))
print("  Cat RMSD: {:.3f}+/-{:.3f} A".format(np.mean(new_rmsds), np.std(new_rmsds)))
print("  n={}".format(len(new_lengths)))
