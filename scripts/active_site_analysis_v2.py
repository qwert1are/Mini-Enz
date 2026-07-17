"""
MiniEnz — Active Site Geometry Analysis v2
Fixed: handle 2-catalytic-residue cases, use distance-based RMSD
"""
import os, json, glob
import numpy as np

RF_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\results\rfdiffusion"
PDB_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\data\pdbs"
OUT_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\results\analysis"
EMB_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\results\esm2_embeddings"
os.makedirs(OUT_DIR, exist_ok=True)

ENZYMES = ["lysozyme", "subtilisin", "tem1", "tim", "glucose_ox", "pc_lipase", "ca2", "tropinone"]

CAT_RES = {
    "lysozyme": [35, 52],
    "subtilisin": [32, 64, 221],
    "tem1": [70, 73, 130, 166],
    "tim": [95, 165],
    "glucose_ox": [516, 559],
    "pc_lipase": [87, 264, 286],
    "ca2": [94, 96, 119, 199, 106],
    "tropinone": [155, 159],
}

PDB_MAP = {
    "lysozyme": "1LSE", "subtilisin": "1SBT", "tem1": "1BTL", "tim": "1TIM",
    "glucose_ox": "1GAL", "pc_lipase": "3LIP", "ca2": "1CA2", "tropinone": "2AE2",
}

def parse_ca(pdb_path, chain="A"):
    d = {}
    with open(pdb_path) as f:
        for line in f:
            if line.startswith("ATOM") and "CA" in line[12:16] and line[21] == chain:
                resi = int(line[22:26].strip())
                d[resi] = np.array([float(line[30:38]), float(line[38:46]), float(line[46:54])])
    return d

def cat_rmsd_after_alignment(mobile_ca, ref_ca, cat_res, align_res=None):
    """
    Align mobile onto ref using align_res (all cat_res if None),
    then compute RMSD on cat_res.
    For <3 residues: use Kabsch if >=3; else use pairwise distance RMSD.
    """
    if align_res is None:
        align_res = cat_res
    
    pts_m = np.array([mobile_ca[r] for r in align_res if r in mobile_ca and r in ref_ca])
    pts_r = np.array([ref_ca[r] for r in align_res if r in mobile_ca and r in ref_ca])
    
    if len(pts_m) < 3:
        # Fewer than 3 points: compute RMSD directly without rotation
        pts_m_cat = np.array([mobile_ca[r] for r in cat_res if r in mobile_ca and r in ref_ca])
        pts_r_cat = np.array([ref_ca[r] for r in cat_res if r in mobile_ca and r in ref_ca])
        if len(pts_m_cat) < 2:
            return None
        # Just center both and compute RMSD
        cm = pts_m_cat.mean(axis=0)
        cr = pts_r_cat.mean(axis=0)
        rmsd = np.sqrt(((pts_m_cat - cm) - (pts_r_cat - cr))**2).sum() / len(pts_m_cat)
        rmsd = np.sqrt(rmsd)
        return float(rmsd)
    
    # Kabsch algorithm for >=3 points
    cm = pts_m.mean(axis=0)
    cr = pts_r.mean(axis=0)
    pts_m_c = pts_m - cm
    pts_r_c = pts_r - cr
    
    H = pts_m_c.T @ pts_r_c
    U, s, Vt = np.linalg.svd(H)
    R = Vt.T @ U.T
    
    if np.linalg.det(R) < 0:
        Vt[-1] *= -1
        R = Vt.T @ U.T
    
    # Apply rotation to all cat_res, compute RMSD
    pts_m_cat = np.array([mobile_ca[r] for r in cat_res if r in mobile_ca and r in ref_ca])
    pts_r_cat = np.array([ref_ca[r] for r in cat_res if r in mobile_ca and r in ref_ca])
    
    pts_m_cat_c = pts_m_cat - cm
    pts_m_cat_aligned = pts_m_cat_c @ R + cr
    rmsd = np.sqrt(((pts_m_cat_aligned - pts_r_cat)**2).sum() / len(pts_m_cat))
    return float(rmsd)

def count_total_residues(pdb_path):
    chains = {}
    with open(pdb_path) as f:
        for line in f:
            if line.startswith("ATOM") and "CA" in line:
                c = line[21]
                r = int(line[22:26].strip())
                chains.setdefault(c, set()).add(r)
    return sum(len(v) for v in chains.values())

print("=" * 70)
print("ACTIVE SITE GEOMETRY ANALYSIS v2")
print("=" * 70)

all_results = {}
all_details = {}

for enz in ENZYMES:
    pdb_id = PDB_MAP[enz]
    native_ca = parse_ca(os.path.join(PDB_DIR, "{}.pdb".format(pdb_id)), "A")
    cat_res = CAT_RES[enz]
    
    design_pdbs = sorted(glob.glob(os.path.join(RF_DIR, "{}_*.pdb".format(enz))))[:200]
    cat_rmsds = []
    total_lengths = []
    
    for pdb in design_pdbs:
        design_ca = parse_ca(pdb, "A")
        rmsd = cat_rmsd_after_alignment(design_ca, native_ca, cat_res)
        if rmsd is not None:
            cat_rmsds.append(rmsd)
        
        total_lengths.append(count_total_residues(pdb))
    
    cat_rmsds = np.array(cat_rmsds)
    
    mean_r = cat_rmsds.mean() if len(cat_rmsds) else 0
    std_r = cat_rmsds.std() if len(cat_rmsds) else 0
    min_r = cat_rmsds.min() if len(cat_rmsds) else 0
    max_r = cat_rmsds.max() if len(cat_rmsds) else 0
    pct_0_5 = (cat_rmsds < 0.5).mean() * 100 if len(cat_rmsds) else 0
    pct_1_0 = (cat_rmsds < 1.0).mean() * 100 if len(cat_rmsds) else 0
    
    mean_len = np.mean(total_lengths)
    
    all_results[enz] = {
        "mean_cat_rmsd": round(float(mean_r), 3),
        "std_cat_rmsd": round(float(std_r), 3),
        "min_cat_rmsd": round(float(min_r), 3),
        "max_cat_rmsd": round(float(max_r), 3),
        "pct_below_0_5A": round(float(pct_0_5), 1),
        "pct_below_1_0A": round(float(pct_1_0), 1),
        "n_analyzed": int(len(cat_rmsds)),
        "mean_total_length": round(float(mean_len), 1),
        "native_length": sum(1 for _ in native_ca),
    }
    
    print("{}: Cat RMSD = {:.3f}+/-{:.3f} A | <0.5A: {:.0f}% | <1.0A: {:.0f}% | n={}".format(
        enz, mean_r, std_r, pct_0_5, pct_1_0, len(cat_rmsds)))

# RMSD vs ProteinMPNN score correlation
print("\n--- RMSD vs MPNN Score ---")
for enz in ENZYMES:
    npz_path = os.path.join(EMB_DIR, "{}_embeddings.npz".format(enz))
    if not os.path.exists(npz_path):
        continue
    npz = np.load(npz_path, allow_pickle=True)
    scores = npz["scores"][:400]
    native_ca = parse_ca(os.path.join(PDB_DIR, "{}.pdb".format(PDB_MAP[enz])), "A")
    
    rmsds = []
    best_scores = []
    for di in range(50):
        pdb = os.path.join(RF_DIR, "{}_{}.pdb".format(enz, di))
        if not os.path.exists(pdb):
            continue
        rmsd = cat_rmsd_after_alignment(parse_ca(pdb, "A"), native_ca, CAT_RES[enz])
        if rmsd is None:
            continue
        bb_scores = scores[di*8:(di+1)*8]
        rmsds.append(rmsd)
        best_scores.append(bb_scores.min())
    
    if len(rmsds) > 5:
        corr = np.corrcoef(rmsds, best_scores)[0, 1]
        print("  {}: r={:.4f} (n={})".format(enz, corr, len(rmsds)))

# Generate summary table row for manuscript
print("\n--- LaTeX Summary Row ---")
for enz in ENZYMES:
    r = all_results[enz]
    print("{:20s} & {:.2f} & {:.2f} & {:.0f}\\% & {:.0f}\\% \\\\".format(
        enz, r["mean_cat_rmsd"], r["std_cat_rmsd"], r["pct_below_0_5A"], r["pct_below_1_0A"]))

with open(os.path.join(OUT_DIR, "active_site_geometry.json"), "w") as f:
    json.dump(all_results, f, indent=2)
print("\nSaved.")
