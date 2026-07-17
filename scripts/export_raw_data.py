"""
Export raw data points for scatter/distribution plots.
Figures needing per-point data:
- Fig 2: MPNN score distributions → need all 3200 individual scores
- Fig 3 (optional): SRE per-backbone values for scatter
- Fig 4: Catalytic RMSD per-backbone values
- Supplementary: RMSD vs Score scatter (50 points per enzyme)
"""
import os, json, glob
import numpy as np

DATA_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\reports\figures_and_data\data"
EMB_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\results\esm2_embeddings"
RF_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\results\rfdiffusion"
PDB_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\data\pdbs"

ENZYMES = ["lysozyme","subtilisin","tem1","tim","glucose_ox","pc_lipase","ca2","tropinone"]
ENZ_LABELS = ["Lysozyme","Subtilisin BPN'","TEM-1 beta-Lactamase","Triosephosphate Isomerase",
              "Glucose Oxidase","P. cepacia Lipase","Carbonic Anhydrase II","Tropinone Reductase-II"]

def parse_ca(pdb, chain="A"):
    d = {}
    with open(pdb) as f:
        for line in f:
            if line.startswith("ATOM") and line[12:16].strip() == "CA" and line[21] == chain:
                d[int(line[22:26].strip())] = np.array([float(line[30:38]),float(line[38:46]),float(line[46:54])])
    return d

def cat_rmsd(mob_ca, ref_ca, cat_res):
    pts_m = np.array([mob_ca[r] for r in cat_res if r in mob_ca and r in ref_ca])
    pts_r = np.array([ref_ca[r] for r in cat_res if r in mob_ca and r in ref_ca])
    if len(pts_m) < 3:
        pts_m2 = np.array([mob_ca[r] for r in cat_res if r in mob_ca and r in ref_ca])
        pts_r2 = np.array([ref_ca[r] for r in cat_res if r in mob_ca and r in ref_ca])
        if len(pts_m2) < 2: return None
        cm, cr = pts_m2.mean(0), pts_r2.mean(0)
        return float(np.sqrt(((pts_m2-cm-(pts_r2-cr))**2).sum()/len(pts_m2)))
    cm, cr = pts_m.mean(0), pts_r.mean(0)
    H = (pts_m-cm).T @ (pts_r-cr)
    U,s,Vt = np.linalg.svd(H)
    R = Vt.T @ U.T
    if np.linalg.det(R)<0: Vt[-1]*=-1; R=Vt.T@U.T
    aligned = (pts_m-cm)@R+cr
    return float(np.sqrt(((aligned-pts_r)**2).sum()/len(pts_m)))

def count_total_aa(pdb):
    chains = {}
    with open(pdb) as f:
        for line in f:
            if line.startswith("ATOM") and line[12:16].strip() == "CA":
                c, r = line[21], int(line[22:26].strip())
                chains.setdefault(c, set()).add(r)
    return sum(len(v) for v in chains.values())

PDB_MAP = {"lysozyme":"1LSE","subtilisin":"1SBT","tem1":"1BTL","tim":"1TIM",
           "glucose_ox":"1GAL","pc_lipase":"3LIP","ca2":"1CA2","tropinone":"2AE2"}
CAT_RES = {"lysozyme":[35,52],"subtilisin":[32,64,221],"tem1":[70,73,130,166],"tim":[95,165],
           "glucose_ox":[516,559],"pc_lipase":[87,264,286],"ca2":[94,96,119,199,106],"tropinone":[155,159]}

import csv

# ============================================================
# Figure 2 raw data: ALL individual MPNN scores + backbone IDs
# ============================================================
print("Exporting Figure 2 raw scores...")
with open(os.path.join(DATA_DIR, "Figure2_MPNN_all_scores.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["enzyme","backbone_id","sample_number","score","sequence_length"])
    for enz in ENZYMES:
        npz = np.load(os.path.join(EMB_DIR, enz+"_embeddings.npz"), allow_pickle=True)
        scores = npz["scores"][:400]
        keys = npz["keys"][:400]
        lengths = npz["lengths"][:400]
        for i, (k, s, l) in enumerate(zip(keys, scores, lengths)):
            k = str(k)
            parts = k.rsplit("_s", 1)
            bb = parts[0]
            sn = int(parts[1]) if len(parts)==2 else 0
            w.writerow([enz, bb, sn, round(float(s),4), int(l)])
print("  {} rows written".format(3200))

# ============================================================
# Figure 4 raw data: Per-backbone SRE values (actual total lengths)
# ============================================================
print("Exporting Figure 1 raw SRE per backbone...")
with open(os.path.join(DATA_DIR, "Figure1_SRE_per_backbone.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["enzyme","backbone_index","total_aa","native_aa","SRE_pct","strategy"])
    for enz in ENZYMES:
        native = {"lysozyme":129,"subtilisin":275,"tem1":263,"tim":247,
                  "glucose_ox":581,"pc_lipase":320,"ca2":256,"tropinone":259}[enz]
        for i in range(200):
            pdb = os.path.join(RF_DIR, "{}_{}.pdb".format(enz, i))
            if not os.path.exists(pdb): continue
            total = count_total_aa(pdb)
            sre = (1 - total/native) * 100
            strategy = "single-motif"
            if enz == "pc_lipase" and i >= 200:
                strategy = "multi-motif"
            w.writerow([enz, i, total, native, round(sre, 2), strategy])
        # Also process multi-motif pc_lipase (200-399)
        if enz == "pc_lipase":
            for i in range(200, 400):
                pdb = os.path.join(RF_DIR, "{}_{}.pdb".format(enz, i))
                if not os.path.exists(pdb): continue
                total = count_total_aa(pdb)
                sre = (1 - total/native) * 100
                w.writerow([enz, i, total, native, round(sre, 2), "multi-motif"])
print("  SRE per backbone written")

# ============================================================
# Figure 4 raw data: Per-backbone catalytic RMSD
# ============================================================
print("Exporting Figure 4 raw catalytic RMSD...")
with open(os.path.join(DATA_DIR, "Figure4_catalytic_RMSD_per_backbone.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["enzyme","backbone_index","catalytic_RMSD_A","n_catalytic_residues"])
    for enz in ENZYMES:
        native_ca = parse_ca(os.path.join(PDB_DIR, PDB_MAP[enz]+".pdb"), "A")
        for i in range(200):
            pdb = os.path.join(RF_DIR, "{}_{}.pdb".format(enz, i))
            if not os.path.exists(pdb): continue
            design_ca = parse_ca(pdb, "A")
            r = cat_rmsd(design_ca, native_ca, CAT_RES[enz])
            if r is not None:
                w.writerow([enz, i, round(r, 4), len(CAT_RES[enz])])
        # Multi-motif pc_lipase
        if enz == "pc_lipase":
            for i in range(200, 400):
                pdb = os.path.join(RF_DIR, "{}_{}.pdb".format(enz, i))
                if not os.path.exists(pdb): continue
                design_ca = parse_ca(pdb, "A")
                r = cat_rmsd(design_ca, native_ca, CAT_RES[enz])
                if r is not None:
                    w.writerow([enz, i, round(r, 4), len(CAT_RES[enz])])
print("  Catalytic RMSD per backbone written")

# ============================================================
# Supplementary: RMSD vs MPNN Score paired per backbone
# ============================================================
print("Exporting Supplementary RMSD vs Score paired data...")
with open(os.path.join(DATA_DIR, "Supplementary_RMSD_vs_MPNN_Score.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["enzyme","backbone_index","catalytic_RMSD_A","best_MPNN_score"])
    for enz in ENZYMES:
        native_ca = parse_ca(os.path.join(PDB_DIR, PDB_MAP[enz]+".pdb"), "A")
        npz = np.load(os.path.join(EMB_DIR, enz+"_embeddings.npz"), allow_pickle=True)
        scores = npz["scores"][:400]
        for i in range(50):
            pdb = os.path.join(RF_DIR, "{}_{}.pdb".format(enz, i))
            if not os.path.exists(pdb): continue
            design_ca = parse_ca(pdb, "A")
            r = cat_rmsd(design_ca, native_ca, CAT_RES[enz])
            if r is None: continue
            bb_scores = scores[i*8:(i+1)*8]
            if len(bb_scores) == 0: continue
            best = float(bb_scores.min())
            w.writerow([enz, i, round(r, 4), round(best, 4)])
print("  RMSD vs Score paired data written")

# ============================================================
# Figure 6 raw: Per-enzyme-pair similarity values
# ============================================================
print("Exporting Figure 6 raw cross-similarity data...")
with open(os.path.join(DATA_DIR, "Figure6_cross_similarity_per_pair.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["enzyme1","enzyme2","mean_cosine_similarity"])
    for i, e1 in enumerate(ENZYMES):
        npz1 = np.load(os.path.join(EMB_DIR, e1+"_embeddings.npz"), allow_pickle=True)
        emb1 = npz1["embeddings"][:400]
        keys1 = npz1["keys"][:400]
        bb_emb1 = {}
        for k in range(len(keys1)):
            bb = str(keys1[k]).rsplit("_s",1)[0]
            bb_emb1.setdefault(bb, []).append(emb1[k])
        mean_emb1 = np.array([np.mean(v,axis=0) for v in bb_emb1.values()])
        for j, e2 in enumerate(ENZYMES):
            npz2 = np.load(os.path.join(EMB_DIR, e2+"_embeddings.npz"), allow_pickle=True)
            emb2 = npz2["embeddings"][:400]
            keys2 = npz2["keys"][:400]
            bb_emb2 = {}
            for k in range(len(keys2)):
                bb = str(keys2[k]).rsplit("_s",1)[0]
                bb_emb2.setdefault(bb, []).append(emb2[k])
            mean_emb2 = np.array([np.mean(v,axis=0) for v in bb_emb2.values()])
            from sklearn.metrics.pairwise import cosine_similarity
            sim_mat = cosine_similarity(mean_emb1, mean_emb2)
            if i == j:
                mask = ~np.eye(len(mean_emb1), dtype=bool)
                val = sim_mat[mask].mean()
            else:
                val = sim_mat.mean()
            w.writerow([e1, e2, round(float(val), 5)])
print("  Cross-similarity per pair written")

print("\nAll raw data files in:", DATA_DIR)
for f in sorted(os.listdir(DATA_DIR)):
    size = os.path.getsize(os.path.join(DATA_DIR, f))
    print("  {} ({:.1f} KB)".format(f, size/1024))
