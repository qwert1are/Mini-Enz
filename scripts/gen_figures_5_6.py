"""
MiniEnz — Generate remaining figures for manuscript revision
Fig 5: Active site RMSD distributions per enzyme
Fig 6: Three-way ESM-2 comparison (native-design-random)
"""
import os, json, glob
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

FIG_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\manuscript\figures"
os.makedirs(FIG_DIR, exist_ok=True)

plt.rcParams.update({"font.size": 10, "axes.labelsize": 11, "axes.titlesize": 12, "figure.dpi": 150, "savefig.dpi": 300, "savefig.bbox": "tight"})

ENZYMES = ["lysozyme", "subtilisin", "tem1", "tim", "glucose_ox", "pc_lipase", "ca2", "tropinone"]
COLORS = {
    "lysozyme": "#E74C3C", "subtilisin": "#3498DB", "tem1": "#2ECC71",
    "tim": "#F39C12", "glucose_ox": "#9B59B6", "pc_lipase": "#1ABC9C",
    "ca2": "#E67E22", "tropinone": "#34495E"
}

# Load geometry data
import json
with open(r"H:\eazyclaw\saved\MiniEnz_Methodology\results\analysis\active_site_geometry.json") as f:
    geo_data = json.load(f)

# --- Fig 5: Active Site Catalytic RMSD Distributions ---
# Regenerate RMSD from PDBs for histogram
RF_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\results\rfdiffusion"
CAT_RES = {"lysozyme":[35,52],"subtilisin":[32,64,221],"tem1":[70,73,130,166],"tim":[95,165],
           "glucose_ox":[516,559],"pc_lipase":[87,264,286],"ca2":[94,96,119,199,106],"tropinone":[155,159]}
PDB_MAP = {"lysozyme":"1LSE","subtilisin":"1SBT","tem1":"1BTL","tim":"1TIM",
           "glucose_ox":"1GAL","pc_lipase":"3LIP","ca2":"1CA2","tropinone":"2AE2"}

def parse_ca(pdb_path, chain="A"):
    d = {}
    with open(pdb_path) as f:
        for line in f:
            if line.startswith("ATOM") and "CA" in line[12:16] and line[21] == chain:
                d[int(line[22:26].strip())] = np.array([float(line[30:38]),float(line[38:46]),float(line[46:54])])
    return d

def cat_rmsd_after_alignment(mobile_ca, ref_ca, cat_res):
    align_res = cat_res
    pts_m = np.array([mobile_ca[r] for r in align_res if r in mobile_ca and r in ref_ca])
    pts_r = np.array([ref_ca[r] for r in align_res if r in mobile_ca and r in ref_ca])
    if len(pts_m) < 3:
        pts_m_cat = np.array([mobile_ca[r] for r in cat_res if r in mobile_ca and r in ref_ca])
        pts_r_cat = np.array([ref_ca[r] for r in cat_res if r in mobile_ca and r in ref_ca])
        if len(pts_m_cat) < 2: return None
        cm, cr = pts_m_cat.mean(0), pts_r_cat.mean(0)
        return float(np.sqrt(((pts_m_cat-cm - (pts_r_cat-cr))**2).sum()/len(pts_m_cat)))
    cm, cr = pts_m.mean(0), pts_r.mean(0)
    H = (pts_m-cm).T @ (pts_r-cr)
    U, s, Vt = np.linalg.svd(H)
    R = Vt.T @ U.T
    if np.linalg.det(R) < 0: Vt[-1]*=-1; R = Vt.T @ U.T
    pts_m_cat = np.array([mobile_ca[r] for r in cat_res if r in mobile_ca and r in ref_ca])
    pts_r_cat = np.array([ref_ca[r] for r in cat_res if r in mobile_ca and r in ref_ca])
    pts_aligned = (pts_m_cat-cm) @ R + cr
    return float(np.sqrt(((pts_aligned-pts_r_cat)**2).sum()/len(pts_m_cat)))

PDB_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\data\pdbs"
all_rmsds = {}

for enz in ENZYMES:
    native_ca = parse_ca(os.path.join(PDB_DIR, PDB_MAP[enz]+".pdb"), "A")
    design_pdbs = sorted(glob.glob(os.path.join(RF_DIR, enz+"_*.pdb")))[:200]
    rmsds = []
    for pdb in design_pdbs:
        r = cat_rmsd_after_alignment(parse_ca(pdb, "A"), native_ca, CAT_RES[enz])
        if r is not None: rmsds.append(r)
    all_rmsds[enz] = rmsds

fig, axes = plt.subplots(2, 4, figsize=(14, 7))
for idx, enz in enumerate(ENZYMES):
    ax = axes[idx//4, idx%4]
    rmsds = all_rmsds[enz]
    ax.hist(rmsds, bins=20, color=COLORS[enz], alpha=0.8, edgecolor="black", linewidth=0.3)
    ax.axvline(x=0.5, color="red", linestyle="--", linewidth=0.8, alpha=0.7)
    ax.axvline(x=1.0, color="orange", linestyle="--", linewidth=0.8, alpha=0.7)
    ax.set_title(enz.replace("_", " "), fontsize=9)
    ax.set_xlabel("Cat. RMSD (A)", fontsize=7)
    ax.set_ylabel("Count", fontsize=7)
    ax.tick_params(labelsize=7)

fig.suptitle("Fig 5: Catalytic Residue RMSD Distributions (Red: 0.5A, Orange: 1.0A)", fontsize=12, fontweight="bold")
fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "fig5_cat_rmsd.png"))
print("Fig 5 saved.")

# --- Fig 6: Three-way ESM-2 comparison ---
three_way = {
    "lysozyme": {"design-design": 0.9171, "native-design": 0.7063, "random-random": 0.967},
    "subtilisin": {"design-design": 0.9361, "native-design": 0.8139, "random-random": 0.967},
    "tem1": {"design-design": 0.9399, "native-design": 0.7586, "random-random": 0.967},
    "tim": {"design-design": 0.9447, "native-design": 0.8350, "random-random": 0.967},
    "glucose_ox": {"design-design": 0.9459, "native-design": 0.8428, "random-random": 0.967},
    "pc_lipase": {"design-design": 0.9465, "native-design": 0.7915, "random-random": 0.967},
    "ca2": {"design-design": 0.9254, "native-design": 0.7855, "random-random": 0.967},
    "tropinone": {"design-design": 0.9366, "native-design": 0.8096, "random-random": 0.967},
}

fig, ax = plt.subplots(figsize=(10, 6))
x = np.arange(len(ENZYMES))
width = 0.25

for i, enz in enumerate(ENZYMES):
    ax.bar(i - width, three_way[enz]["random-random"], width, color="lightgray", edgecolor="black", label="Random baseline" if i==0 else "")
    ax.bar(i, three_way[enz]["design-design"], width, color=COLORS[enz], alpha=0.8, edgecolor="black", label="Design-Design" if i==0 else "")
    ax.bar(i + width, three_way[enz]["native-design"], width, color=COLORS[enz], alpha=0.4, edgecolor="black", hatch="//", label="Native-Design" if i==0 else "")

ax.set_xticks(x)
ax.set_xticklabels([e.replace("_", " ") for e in ENZYMES], rotation=45, ha="right", fontsize=9)
ax.set_ylabel("ESM-2 Cosine Similarity")
ax.set_title("Fig 6: Three-Way ESM-2 Embedding Comparison\n(Random > Design-Design > Native-Design)")
ax.legend(fontsize=8)
ax.set_ylim(0.65, 1.0)
ax.axhline(y=0.967, color="gray", linestyle=":", alpha=0.5)

fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "fig6_three_way_esm2.png"))
print("Fig 6 saved.")

print("Done. Figures in {}".format(FIG_DIR))
