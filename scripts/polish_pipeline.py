"""
MiniEnz — Pre-submission polish pipeline
1. Fix SRE data: compute actual total length (Chain A + B) from RFdiffusion PDBs
2. Generate null distribution: random sequences of same lengths, ESM-2 similarity baseline
3. Generate publication figures (4 figures)
"""
import os, json, re, glob
import numpy as np

# ============================================================
# STEP 1: Fix SRE — compute actual total length from PDBs
# ============================================================
print("=" * 70)
print("STEP 1: Fix Size Reduction Efficiency (SRE)")
print("=" * 70)

RF_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\results\rfdiffusion"
EMB_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\results\esm2_embeddings"
OUT_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\results\analysis"
FIG_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\manuscript\figures"
os.makedirs(FIG_DIR, exist_ok=True)

ENZYMES = ["lysozyme", "subtilisin", "tem1", "tim", "glucose_ox", "pc_lipase", "ca2", "tropinone"]
ENZYME_META = {
    "lysozyme": {"native_len": 129, "fold": "alpha+beta", "ec": "3.2.1.17"},
    "subtilisin": {"native_len": 275, "fold": "alpha/beta sandwich", "ec": "3.4.21.62"},
    "tem1": {"native_len": 263, "fold": "alpha/beta DD-peptidase", "ec": "3.5.2.6"},
    "tim": {"native_len": 247, "fold": "TIM barrel", "ec": "5.3.1.1"},
    "glucose_ox": {"native_len": 581, "fold": "FAD-binding", "ec": "1.1.3.4"},
    "pc_lipase": {"native_len": 320, "fold": "alpha/beta hydrolase", "ec": "3.1.1.3"},
    "ca2": {"native_len": 256, "fold": "all-beta", "ec": "4.2.1.1"},
    "tropinone": {"native_len": 259, "fold": "Rossmann SDR", "ec": "1.1.1.184"},
}

fixed_lengths = {}

for enz in ENZYMES:
    pdbs = sorted(glob.glob(os.path.join(RF_DIR, "{}_*.pdb".format(enz))))[:50]
    total_lengths = []
    chain_a_lens = []
    chain_b_lens = []
    
    for pdb in pdbs:
        chains = {}
        with open(pdb) as f:
            for line in f:
                if line.startswith("ATOM") and "CA" in line:
                    chain = line[21]
                    resi = int(line[22:26].strip())
                    if chain not in chains:
                        chains[chain] = set()
                    chains[chain].add(resi)
        
        a_len = len(chains.get("A", set()))
        b_len = len(chains.get("B", set()))
        chain_a_lens.append(a_len)
        chain_b_lens.append(b_len)
        total_lengths.append(a_len + b_len)
    
    mean_total = np.mean(total_lengths)
    std_total = np.std(total_lengths)
    native = ENZYME_META[enz]["native_len"]
    sre = (1 - mean_total / native) * 100
    
    fixed_lengths[enz] = {
        "mean_total": round(float(mean_total), 1),
        "std_total": round(float(std_total), 1),
        "mean_chain_a": round(float(np.mean(chain_a_lens)), 1),
        "mean_chain_b": round(float(np.mean(chain_b_lens)), 1),
        "sre": round(float(sre), 1),
        "native": native,
    }
    
    print("{}: native={}, designed total={:.0f}±{:.0f} (A={:.0f}, B={:.0f}), SRE={:.1f}%".format(
        enz, native, mean_total, std_total, np.mean(chain_a_lens), np.mean(chain_b_lens), sre))


# ============================================================
# STEP 2: Null distribution for ESM-2 similarity
# ============================================================
print("\n" + "=" * 70)
print("STEP 2: ESM-2 Null Distribution")
print("=" * 70)

import esm
import torch

model, alphabet = esm.pretrained.esm2_t30_150M_UR50D()
model = model.cuda().eval()
batch_converter = alphabet.get_batch_converter()

# Generate random sequences at typical mini-enzyme lengths (80-400 aa)
AA = "ACDEFGHIKLMNPQRSTVWY"
np.random.seed(42)

random_seqs = []
random_lengths = [80, 120, 160, 200, 250, 300, 350, 400]
for L in random_lengths:
    for _ in range(25):  # 25 seqs per length = 200 total
        seq = "".join(np.random.choice(list(AA), L))
        random_seqs.append(("rand_L{}".format(L), seq))

# Batch extract
with torch.no_grad():
    all_rand_embs = []
    for i in range(0, len(random_seqs), 25):
        batch = random_seqs[i:i+25]
        labels, strs, tokens = batch_converter(batch)
        tokens = tokens.cuda()
        results = model(tokens, repr_layers=[30], return_contacts=False)
        reps = results["representations"][30]
        for j, (_, seq) in enumerate(batch):
            rep = reps[j, 1:len(seq)+1].mean(dim=0).cpu().numpy()
            all_rand_embs.append(rep)

all_rand_embs = np.array(all_rand_embs)

# Compute pairwise similarity for random sequences
from sklearn.metrics.pairwise import cosine_similarity
rand_sim = cosine_similarity(all_rand_embs)
rand_mask = ~np.eye(len(all_rand_embs), dtype=bool)
rand_mean_sim = rand_sim[rand_mask].mean()
rand_std_sim = rand_sim[rand_mask].std()

print("Random sequences (n={}): sim = {:.4f} ± {:.4f}".format(len(all_rand_embs), rand_mean_sim, rand_std_sim))

# Now compute within-enzyme similarity vs null
print("\nEnzyme similarity vs null baseline:")
for enz in ENZYMES:
    npz = np.load(os.path.join(EMB_DIR, "{}_embeddings.npz".format(enz)), allow_pickle=True)
    emb = npz["embeddings"][:400]
    sim = cosine_similarity(emb)
    mask = ~np.eye(400, dtype=bool)
    mean_sim = sim[mask].mean()
    z_score = (mean_sim - rand_mean_sim) / rand_std_sim
    significant = "***" if z_score > 3 else ("**" if z_score > 2 else ("*" if z_score > 1.65 else "ns"))
    print("  {}: sim={:.4f}, z={:.2f} {}".format(enz, mean_sim, z_score, significant))

# ============================================================
# STEP 3: Generate publication figures
# ============================================================
print("\n" + "=" * 70)
print("STEP 3: Generate Figures")
print("=" * 70)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

plt.rcParams.update({
    "font.size": 10, "axes.labelsize": 12, "axes.titlesize": 13,
    "figure.dpi": 150, "savefig.dpi": 300, "savefig.bbox": "tight"
})

# Color palette per enzyme
COLORS = {
    "lysozyme": "#E74C3C", "subtilisin": "#3498DB", "tem1": "#2ECC71",
    "tim": "#F39C12", "glucose_ox": "#9B59B6", "pc_lipase": "#1ABC9C",
    "ca2": "#E67E22", "tropinone": "#34495E"
}

# --- Figure 1: Size Reduction bar chart ---
fig, ax = plt.subplots(figsize=(10, 5))
enz_names = []
sre_vals = []
colors = []
for enz in ENZYMES:
    enz_names.append(enz.replace("_", " "))
    sre_vals.append(fixed_lengths[enz]["sre"])
    colors.append(COLORS[enz])

bars = ax.bar(range(len(enz_names)), sre_vals, color=colors, edgecolor="black", linewidth=0.5)
ax.axhline(y=0, color="gray", linestyle="--", linewidth=0.8)
ax.set_xticks(range(len(enz_names)))
ax.set_xticklabels(enz_names, rotation=45, ha="right", fontsize=9)
ax.set_ylabel("Size Reduction Efficiency (%)")
ax.set_title("Fig 1: Enzyme Miniaturization Performance Across 8 Families")
ax.set_ylim(-30, 50)

# Add native length annotations
for i, enz in enumerate(ENZYMES):
    ax.annotate("{}aa".format(ENZYME_META[enz]["native_len"]), 
                (i, sre_vals[i]), textcoords="offset points", 
                xytext=(0, 8 if sre_vals[i] >= 0 else -14), ha="center", fontsize=7.5, color="gray")

fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "fig1_sre.png"))
print("Fig 1 saved: size reduction")

# --- Figure 2: ProteinMPNN Score Distributions ---
fig, ax = plt.subplots(figsize=(10, 5))
score_data = []
enz_labels = []
for enz in ENZYMES:
    npz = np.load(os.path.join(EMB_DIR, "{}_embeddings.npz".format(enz)), allow_pickle=True)
    scores = npz["scores"][:400]
    score_data.append(scores)
    enz_labels.append(enz.replace("_", " "))

bp = ax.boxplot(score_data, patch_artist=True, widths=0.6)
for patch, enz in zip(bp["boxes"], ENZYMES):
    patch.set_facecolor(COLORS[enz])
    patch.set_alpha(0.7)

ax.set_xticklabels(enz_labels, rotation=45, ha="right", fontsize=9)
ax.set_ylabel("ProteinMPNN Global Score (lower = better)")
ax.set_title("Fig 2: Sequence Design Quality Across Enzyme Families")
ax.axhline(y=1.0, color="gray", linestyle="--", alpha=0.5, label="Score = 1.0")
fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "fig2_scores.png"))
print("Fig 2 saved: score distributions")

# --- Figure 3: Cross-enzyme ESM-2 similarity heatmap ---
fig, ax = plt.subplots(figsize=(8, 7))
cross_sim = np.zeros((8, 8))
for i, e1 in enumerate(ENZYMES):
    npz1 = np.load(os.path.join(EMB_DIR, "{}_embeddings.npz".format(e1)), allow_pickle=True)
    emb1 = npz1["embeddings"][:400]
    # Per-backbone mean
    keys1 = npz1["keys"][:400]
    bb_emb1 = {}
    for k in range(len(keys1)):
        bb = str(keys1[k]).split("_s")[0]
        bb_emb1.setdefault(bb, []).append(emb1[k])
    mean_emb1 = np.array([np.mean(v, axis=0) for v in bb_emb1.values()])
    
    for j, e2 in enumerate(ENZYMES):
        npz2 = np.load(os.path.join(EMB_DIR, "{}_embeddings.npz".format(e2)), allow_pickle=True)
        emb2 = npz2["embeddings"][:400]
        keys2 = npz2["keys"][:400]
        bb_emb2 = {}
        for k in range(len(keys2)):
            bb = str(keys2[k]).split("_s")[0]
            bb_emb2.setdefault(bb, []).append(emb2[k])
        mean_emb2 = np.array([np.mean(v, axis=0) for v in bb_emb2.values()])
        
        sim_mat = cosine_similarity(mean_emb1, mean_emb2)
        if i == j:
            mask = ~np.eye(len(mean_emb1), dtype=bool)
            cross_sim[i, j] = sim_mat[mask].mean()
        else:
            cross_sim[i, j] = sim_mat.mean()

im = ax.imshow(cross_sim, cmap="YlOrRd", vmin=0.9, vmax=1.0)
ax.set_xticks(range(8))
ax.set_yticks(range(8))
ax.set_xticklabels([e.replace("_", " ") for e in ENZYMES], rotation=45, ha="right", fontsize=8)
ax.set_yticklabels([e.replace("_", " ") for e in ENZYMES], fontsize=8)
ax.set_title("Fig 3: Cross-Enzyme ESM-2 Embedding Similarity\n(Null baseline: {:.4f})".format(rand_mean_sim))

for i in range(8):
    for j in range(8):
        ax.text(j, i, "{:.3f}".format(cross_sim[i, j]), ha="center", va="center", fontsize=7)

cbar = plt.colorbar(im, ax=ax, shrink=0.8)
cbar.set_label("Cosine Similarity")
fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "fig3_cross_sim.png"))
print("Fig 3 saved: cross-enzyme similarity")

# --- Figure 4: Enzyme structural/metadata overview table ---
fig, ax = plt.subplots(figsize=(12, 4))
ax.axis("off")
table_data = []
headers = ["Enzyme", "PDB", "EC", "Native (aa)", "Designed (aa)", "SRE (%)", "Fold", "Cat. Residues"]
for enz in ENZYMES:
    meta = ENZYME_META[enz]
    fl = fixed_lengths[enz]
    table_data.append([
        enz.replace("_", " ").title(),
        {"lysozyme":"1LSE","subtilisin":"1SBT","tem1":"1BTL","tim":"1TIM",
         "glucose_ox":"1GAL","pc_lipase":"3LIP","ca2":"1CA2","tropinone":"2AE2"}[enz],
        meta["ec"],
        str(meta["native_len"]),
        "{:.0f}".format(fl["mean_total"]),
        "{:.1f}".format(fl["sre"]),
        meta["fold"],
        {"lysozyme":"E35,D52","subtilisin":"D32,H64,S221","tem1":"S70,K73,S130,E166",
         "tim":"H95,E165","glucose_ox":"H516,H559","pc_lipase":"S87,D264,H286",
         "ca2":"H94,H96,H119,T199,E106","tropinone":"Y155,Y159"}[enz],
    ])

tbl = ax.table(cellText=table_data, colLabels=headers, cellLoc="center", loc="center")
tbl.auto_set_font_size(False)
tbl.set_fontsize(7.5)
tbl.scale(1, 1.4)
for i, enz in enumerate(ENZYMES):
    for j in range(len(headers)):
        tbl[(i+1, j)].set_facecolor(COLORS[enz] + "20")  # 20 = alpha

ax.set_title("Table 1: MiniEnz Enzyme Catalog and Benchmark Results", fontsize=12, fontweight="bold", y=1.02)
fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "fig4_catalog_table.png"))
print("Fig 4 saved: enzyme catalog table")

# Save the corrected data
import json
with open(os.path.join(OUT_DIR, "fixed_sre.json"), "w") as f:
    json.dump(fixed_lengths, f, indent=2)
with open(os.path.join(OUT_DIR, "null_baseline.json"), "w") as f:
    json.dump({"rand_mean_sim": float(rand_mean_sim), "rand_std_sim": float(rand_std_sim), "n_random": len(all_rand_embs)}, f, indent=2)

print("\nALL DONE")
print("Figures: {}".format(FIG_DIR))
print("Corrected SRE: {}/fixed_sre.json".format(OUT_DIR))
print("Null baseline: {}/null_baseline.json".format(OUT_DIR))
