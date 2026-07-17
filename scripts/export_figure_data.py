"""
Export figure source data as CSV/JSON for all 6 figures.
"""
import os, json, glob
import numpy as np
import csv

DATA_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\reports\figures_and_data\data"
EMB_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\results\esm2_embeddings"
os.makedirs(DATA_DIR, exist_ok=True)

ENZYMES = ["lysozyme","subtilisin","tem1","tim","glucose_ox","pc_lipase","ca2","tropinone"]
ENZ_LABELS = ["Lysozyme","Subtilisin BPN'","TEM-1 beta-Lactamase","Triosephosphate Isomerase",
              "Glucose Oxidase","P. cepacia Lipase","Carbonic Anhydrase II","Tropinone Reductase-II"]

# ============================================================
# Data for Figure 1: SRE
# ============================================================
sre_fig1_data = [
    {"enzyme":"P. cepacia Lipase","enzyme_key":"pc_lipase","SRE":50.2,"SD":4.4,"native_length":320,"designed_mean":159.5,"designed_sd":16.7,"strategy":"multi-motif"},
    {"enzyme":"Glucose Oxidase","enzyme_key":"glucose_ox","SRE":38.4,"SD":5.9,"native_length":581,"designed_mean":358.0,"designed_sd":34.0,"strategy":"single-motif"},
    {"enzyme":"Carbonic Anhydrase II","enzyme_key":"ca2","SRE":27.4,"SD":6.3,"native_length":256,"designed_mean":186.0,"designed_sd":16.0,"strategy":"single-motif"},
    {"enzyme":"Tropinone Reductase-II","enzyme_key":"tropinone","SRE":26.7,"SD":5.8,"native_length":259,"designed_mean":190.0,"designed_sd":15.0,"strategy":"single-motif"},
    {"enzyme":"Subtilisin BPN'","enzyme_key":"subtilisin","SRE":23.5,"SD":5.8,"native_length":275,"designed_mean":210.0,"designed_sd":16.0,"strategy":"single-motif"},
    {"enzyme":"Lysozyme","enzyme_key":"lysozyme","SRE":20.4,"SD":5.4,"native_length":129,"designed_mean":103.0,"designed_sd":7.0,"strategy":"single-motif"},
    {"enzyme":"TEM-1 beta-Lactamase","enzyme_key":"tem1","SRE":12.0,"SD":5.3,"native_length":263,"designed_mean":231.0,"designed_sd":14.0,"strategy":"single-motif"},
    {"enzyme":"Triosephosphate Isomerase","enzyme_key":"tim","SRE":6.0,"SD":6.1,"native_length":247,"designed_mean":232.0,"designed_sd":15.0,"strategy":"single-motif"},
]

with open(os.path.join(DATA_DIR, "Figure1_SRE_data.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=sre_fig1_data[0].keys())
    w.writeheader()
    w.writerows(sre_fig1_data)
with open(os.path.join(DATA_DIR, "Figure1_SRE_data.json"), "w") as f:
    json.dump(sre_fig1_data, f, indent=2)

# ============================================================
# Data for Figure 2: MPNN Scores (full distributions)
# ============================================================
fig2_data = {}
for enz in ENZYMES:
    npz = np.load(os.path.join(EMB_DIR, enz+"_embeddings.npz"), allow_pickle=True)
    scores = npz["scores"][:400]
    fig2_data[enz] = {
        "enzyme": ENZ_LABELS[ENZYMES.index(enz)],
        "n_sequences": len(scores),
        "mean": round(float(scores.mean()), 4),
        "std": round(float(scores.std()), 4),
        "min": round(float(scores.min()), 4),
        "max": round(float(scores.max()), 4),
        "q25": round(float(np.percentile(scores, 25)), 4),
        "q50": round(float(np.percentile(scores, 50)), 4),
        "q75": round(float(np.percentile(scores, 75)), 4),
        "scores": [round(float(s), 4) for s in scores.tolist()],
    }

with open(os.path.join(DATA_DIR, "Figure2_MPNN_scores.json"), "w") as f:
    json.dump(fig2_data, f, indent=2)

# CSV summary
with open(os.path.join(DATA_DIR, "Figure2_MPNN_scores_summary.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["enzyme","n","mean","std","min","max","q25","q50","q75"])
    for enz in ENZYMES:
        d = fig2_data[enz]
        w.writerow([d["enzyme"],d["n_sequences"],d["mean"],d["std"],d["min"],d["max"],d["q25"],d["q50"],d["q75"]])

# ============================================================
# Data for Figure 3: ESM-2 Three-Way Comparison
# ============================================================
three_way = {
    "lysozyme": (0.917, 0.706),
    "subtilisin": (0.936, 0.814),
    "tem1": (0.940, 0.759),
    "tim": (0.945, 0.835),
    "glucose_ox": (0.946, 0.843),
    "pc_lipase": (0.908, 0.792),
    "ca2": (0.925, 0.786),
    "tropinone": (0.937, 0.810),
}

fig3_data = []
for enz in ENZYMES:
    dd, nd = three_way[enz]
    fig3_data.append({
        "enzyme": ENZ_LABELS[ENZYMES.index(enz)],
        "enzyme_key": enz,
        "random_baseline": 0.967,
        "random_baseline_sd": 0.019,
        "design_design_similarity": dd,
        "native_design_similarity": nd,
    })

with open(os.path.join(DATA_DIR, "Figure3_ESM2_threeway.json"), "w") as f:
    json.dump(fig3_data, f, indent=2)
with open(os.path.join(DATA_DIR, "Figure3_ESM2_threeway.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fig3_data[0].keys())
    w.writeheader()
    w.writerows(fig3_data)

# ============================================================
# Data for Figure 4: Catalytic RMSD
# ============================================================
geo_path = r"H:\eazyclaw\saved\MiniEnz_Methodology\results\analysis\active_site_geometry.json"
with open(geo_path) as f:
    geo = json.load(f)

fig4_data = []
cat_res_names = {
    "lysozyme": "E35, D52",
    "subtilisin": "D32, H64, S221",
    "tem1": "S70, K73, S130, E166",
    "tim": "H95, E165",
    "glucose_ox": "H516, H559",
    "pc_lipase": "S87, D264, H286",
    "ca2": "H94, H96, H119, T199, E106",
    "tropinone": "Y155, Y159",
}

for enz in ENZYMES:
    g = geo[enz]
    fig4_data.append({
        "enzyme": ENZ_LABELS[ENZYMES.index(enz)],
        "enzyme_key": enz,
        "catalytic_residues": cat_res_names[enz],
        "n_catalytic_residues": sum(1 for c in cat_res_names[enz].split(",")),
        "mean_rmsd_A": g["mean_cat_rmsd"],
        "sd_rmsd_A": g["std_cat_rmsd"],
        "min_rmsd_A": g["min_cat_rmsd"],
        "max_rmsd_A": g["max_cat_rmsd"],
        "pct_below_0_5A": g["pct_below_0_5A"],
        "pct_below_1_0A": g["pct_below_1_0A"],
        "n_designs_analyzed": g["n_analyzed"],
    })

with open(os.path.join(DATA_DIR, "Figure4_catalytic_RMSD.json"), "w") as f:
    json.dump(fig4_data, f, indent=2)
with open(os.path.join(DATA_DIR, "Figure4_catalytic_RMSD.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fig4_data[0].keys())
    w.writeheader()
    w.writerows(fig4_data)

# ============================================================
# Data for Figure 5: Enzyme Catalog
# ============================================================
fig5_data = [
    {"enzyme":"Lysozyme","PDB":"1LSE","EC":"3.2.1.17","length":129,"fold":"alpha+beta","catalytic_residues":"Glu35, Asp52","cofactors":"None","organism":"Gallus gallus"},
    {"enzyme":"Subtilisin BPN'","PDB":"1SBT","EC":"3.4.21.62","length":275,"fold":"alpha/beta sandwich","catalytic_residues":"Asp32, His64, Ser221","cofactors":"None","organism":"Bacillus amyloliquefaciens"},
    {"enzyme":"TEM-1 beta-Lactamase","PDB":"1BTL","EC":"3.5.2.6","length":263,"fold":"alpha/beta DD-peptidase","catalytic_residues":"Ser70, Lys73, Ser130, Glu166","cofactors":"None","organism":"Escherichia coli"},
    {"enzyme":"Triosephosphate Isomerase","PDB":"1TIM","EC":"5.3.1.1","length":247,"fold":"(beta/alpha)8 TIM barrel","catalytic_residues":"His95, Glu165","cofactors":"None","organism":"Gallus gallus"},
    {"enzyme":"Glucose Oxidase","PDB":"1GAL","EC":"1.1.3.4","length":581,"fold":"FAD-binding + substrate","catalytic_residues":"His516, His559","cofactors":"FAD","organism":"Aspergillus niger"},
    {"enzyme":"P. cepacia Lipase","PDB":"3LIP","EC":"3.1.1.3","length":320,"fold":"alpha/beta hydrolase","catalytic_residues":"Ser87, Asp264, His286","cofactors":"None","organism":"Burkholderia cepacia"},
    {"enzyme":"Carbonic Anhydrase II","PDB":"1CA2","EC":"4.2.1.1","length":256,"fold":"All-beta","catalytic_residues":"His94, His96, His119, Thr199, Glu106","cofactors":"Zn2+","organism":"Homo sapiens"},
    {"enzyme":"Tropinone Reductase-II","PDB":"2AE2","EC":"1.1.1.184","length":259,"fold":"Rossmann (SDR)","catalytic_residues":"Tyr155, Tyr159","cofactors":"NADP+","organism":"Datura stramonium"},
]

with open(os.path.join(DATA_DIR, "Figure5_enzyme_catalog.json"), "w") as f:
    json.dump(fig5_data, f, indent=2)
with open(os.path.join(DATA_DIR, "Figure5_enzyme_catalog.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fig5_data[0].keys())
    w.writeheader()
    w.writerows(fig5_data)

# ============================================================
# Data for Figure 6: Cross-enzyme similarity heatmap
# ============================================================
from sklearn.metrics.pairwise import cosine_similarity

cross_sim_matrix = np.zeros((8, 8))
for i, e1 in enumerate(ENZYMES):
    npz1 = np.load(os.path.join(EMB_DIR, e1+"_embeddings.npz"), allow_pickle=True)
    emb1 = npz1["embeddings"][:400]
    keys1 = npz1["keys"][:400]
    bb_emb1 = {}
    for k in range(len(keys1)):
        bb = str(keys1[k]).rsplit("_s",1)[0]
        bb_emb1.setdefault(bb, []).append(emb1[k])
    mean_emb1 = np.array([np.mean(v, axis=0) for v in bb_emb1.values()])
    
    for j, e2 in enumerate(ENZYMES):
        npz2 = np.load(os.path.join(EMB_DIR, e2+"_embeddings.npz"), allow_pickle=True)
        emb2 = npz2["embeddings"][:400]
        keys2 = npz2["keys"][:400]
        bb_emb2 = {}
        for k in range(len(keys2)):
            bb = str(keys2[k]).rsplit("_s",1)[0]
            bb_emb2.setdefault(bb, []).append(emb2[k])
        mean_emb2 = np.array([np.mean(v, axis=0) for v in bb_emb2.values()])
        
        sim_mat = cosine_similarity(mean_emb1, mean_emb2)
        if i == j:
            mask = ~np.eye(len(mean_emb1), dtype=bool)
            cross_sim_matrix[i, j] = sim_mat[mask].mean()
        else:
            cross_sim_matrix[i, j] = sim_mat.mean()

fig6_data = {
    "enzymes": ENZ_LABELS,
    "enzyme_keys": ENZYMES,
    "similarity_matrix": [[round(float(cross_sim_matrix[i,j]),4) for j in range(8)] for i in range(8)],
    "random_baseline": 0.967,
    "random_baseline_sd": 0.019,
}

with open(os.path.join(DATA_DIR, "Figure6_cross_similarity.json"), "w") as f:
    json.dump(fig6_data, f, indent=2)

with open(os.path.join(DATA_DIR, "Figure6_cross_similarity.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow([""]+ENZ_LABELS)
    for i, enz in enumerate(ENZ_LABELS):
        w.writerow([enz]+[round(float(cross_sim_matrix[i,j]),4) for j in range(8)])

print("All data exported to:", DATA_DIR)
print("Files:", os.listdir(DATA_DIR))
