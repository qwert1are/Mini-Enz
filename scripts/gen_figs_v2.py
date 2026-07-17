"""
MiniEnz — Generate publication-quality figures with corrected aesthetics.
Fig 1: SRE bar chart — sorted, warm palette, error bars, native length labels
Fig 2: MPNN score distributions — violin plots, colorblind-friendly, compact
Fig 3: ESM-2 three-way comparison — grouped bar
Fig 4: Catalytic RMSD distributions
"""
import os, json, glob
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

FIG_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\manuscript\figures"
os.makedirs(FIG_DIR, exist_ok=True)

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 12,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 8,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "axes.spines.top": False,
    "axes.spines.right": False,
})

ENZYMES = ["lysozyme","subtilisin","tem1","tim","glucose_ox","pc_lipase","ca2","tropinone"]
ENZ_LABELS = ["Lysozyme","Subtilisin\nBPN\u2019","TEM-1\n\u03b2-Lactamase","Triosephosphate\nIsomerase",
              "Glucose\nOxidase","P. cepacia\nLipase","Carbonic\nAnhydrase II","Tropinone\nReductase-II"]
COLORS = ["#D4A574","#B87333","#8B5A2B","#A0522D",
          "#CD853F","#D2691E","#8B4513","#6B3410"]

# ============================================================
# Fig 1: SRE sorted bar chart
# ============================================================
sre_data = [
    ("pc_lipase", 50.2, 4.4),
    ("glucose_ox", 38.4, 5.9),
    ("ca2", 27.4, 6.3),
    ("tropinone", 26.7, 5.8),
    ("subtilisin", 23.5, 5.8),
    ("lysozyme", 20.4, 5.4),
    ("tem1", 12.0, 5.3),
    ("tim", 6.0, 6.1),
]
native_lens = {"pc_lipase":320,"glucose_ox":581,"ca2":256,"tropinone":259,
               "subtilisin":275,"lysozyme":129,"tem1":263,"tim":247}

fig, ax = plt.subplots(figsize=(9, 5.5))
labels = [ENZ_LABELS[ENZYMES.index(e)] for e,_,_ in sre_data]
vals = [v for _,v,_ in sre_data]
errs = [e for _,_,e in sre_data]
colors = [COLORS[ENZYMES.index(e)] for e,_,_ in sre_data]

bars = ax.bar(range(len(labels)), vals, yerr=errs, color=colors, edgecolor="white",
              linewidth=0.8, capsize=4, error_kw={"linewidth":1.2,"capthick":1.2})
ax.axhline(y=0, color="#888888", linewidth=0.8, linestyle="--")

for i, (e, v, _) in enumerate(sre_data):
    nl = native_lens[e]
    ax.text(i, v + errs[i] + 2, f"{v:.0f}%", ha="center", fontsize=8.5, fontweight="bold", color="#333")
    ax.text(i, -9, f"{nl} aa", ha="center", fontsize=7, color="#888", fontstyle="italic")

ax.set_xticks(range(len(labels)))
ax.set_xticklabels(labels, fontsize=8.5)
ax.set_ylabel("Size Reduction Efficiency (%)", fontsize=12, weight="bold")
ax.set_title("Figure 1: Enzyme Miniaturization Performance", fontsize=13, weight="bold", pad=12)
ax.set_ylim(-14, 62)
ax.yaxis.set_major_locator(ticker.MultipleLocator(10))

fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "fig1_sre_v2.png"))
plt.close()
print("Fig 1 saved.")

# ============================================================
# Fig 2: MPNN score distributions (violin)
# ============================================================
EMB_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\results\esm2_embeddings"

score_data_ordered = []
for e, _, _ in sre_data:
    npz = np.load(os.path.join(EMB_DIR, e+"_embeddings.npz"), allow_pickle=True)
    score_data_ordered.append(npz["scores"][:400])

fig, ax = plt.subplots(figsize=(9, 5.5))
vp = ax.violinplot(score_data_ordered, positions=range(len(labels)), showmeans=True,
                    showmedians=False, widths=0.7)
for i, body in enumerate(vp["bodies"]):
    body.set_facecolor(colors[i])
    body.set_alpha(0.75)
    body.set_edgecolor("white")
    body.set_linewidth(0.5)
for part in ["cmeans","cmins","cmaxes","cbars"]:
    if part in vp:
        vp[part].set_edgecolor("#333")
        vp[part].set_linewidth(0.8)

best_scores = [d.min() for d in score_data_ordered]
ax.scatter(range(len(labels)), best_scores, s=35, c="#C0392B", zorder=5,
           edgecolors="white", linewidth=0.5, label="Best score")

ax.set_xticks(range(len(labels)))
ax.set_xticklabels(labels, fontsize=8.5)
ax.set_ylabel("ProteinMPNN Global Score (lower = better)", fontsize=12, weight="bold")
ax.set_title("Figure 2: Sequence Design Quality Across Enzyme Families", fontsize=13, weight="bold", pad=12)
ax.legend(fontsize=9, loc="upper left")
ax.axhline(y=1.0, color="#bbb", linewidth=0.7, linestyle=":", alpha=0.6)

fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "fig2_scores_v2.png"))
plt.close()
print("Fig 2 saved.")

# ============================================================
# Fig 3: ESM-2 three-way comparison
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
rand_baseline = 0.967

sre_sorted_keys = [e for e,_,_ in sre_data]
fig, ax = plt.subplots(figsize=(9, 5.5))
x = np.arange(len(sre_sorted_keys))
width = 0.25

for i, e in enumerate(sre_sorted_keys):
    dd, nd = three_way[e]
    ax.bar(i - width, rand_baseline, width, color="#D5D5D5", edgecolor="white", linewidth=0.5,
           label="Random baseline" if i == 0 else "")
    ax.bar(i, dd, width, color=colors[ENZYMES.index(e)], edgecolor="white", linewidth=0.5, alpha=0.85,
           label="Design\u2013Design" if i == 0 else "")
    ax.bar(i + width, nd, width, color=colors[ENZYMES.index(e)], edgecolor="white", linewidth=0.5, alpha=0.4,
           hatch="///", label="Native\u2013Design" if i == 0 else "")

ax.set_xticks(x)
ax.set_xticklabels([ENZ_LABELS[ENZYMES.index(e)] for e in sre_sorted_keys], fontsize=8.5)
ax.set_ylabel("ESM-2 Cosine Similarity", fontsize=12, weight="bold")
ax.set_title("Figure 3: Three-Way ESM-2 Embedding Comparison", fontsize=13, weight="bold", pad=12)
ax.set_ylim(0.64, 1.0)
ax.legend(fontsize=8.5, ncol=3, loc="upper right")
ax.axhline(y=rand_baseline, color="#888", linewidth=0.6, linestyle=":", alpha=0.5)

fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "fig3_threeway_v2.png"))
plt.close()
print("Fig 3 saved.")

# ============================================================
# Fig 4: Catalytic RMSD distributions
# ============================================================
cat_names = ["Lysozyme","Subtilisin","TEM-1","TIM","Glucose Ox.","pc Lipase","CA2","Tropinone"]
cat_rmsd_vals = {
    "lysozyme": (0.68, 0.08, 2.0),
    "subtilisin": (0.50, 0.06, 48.0),
    "tem1": (0.13, 0.04, 100.0),
    "tim": (0.33, 0.05, 100.0),
    "glucose_ox": (0.56, 0.07, 20.0),
    "pc_lipase": (0.44, 0.15, 68.0),
    "ca2": (0.19, 0.05, 100.0),
    "tropinone": (0.62, 0.05, 2.0),
}

fig, ax = plt.subplots(figsize=(9, 5.5))
rmsd_ordered = [cat_rmsd_vals[e][0] for e in sre_sorted_keys]
err_ordered = [cat_rmsd_vals[e][1] for e in sre_sorted_keys]
pct_ordered = [cat_rmsd_vals[e][2] for e in sre_sorted_keys]
lbls_ordered = [ENZ_LABELS[ENZYMES.index(e)] for e in sre_sorted_keys]

bars = ax.bar(range(len(lbls_ordered)), rmsd_ordered, yerr=err_ordered,
              color=[COLORS[ENZYMES.index(e)] for e in sre_sorted_keys],
              edgecolor="white", linewidth=0.8, capsize=4,
              error_kw={"linewidth":1.2,"capthick":1.2})

ax.axhline(y=0.5, color="#C0392B", linewidth=1.0, linestyle="--", alpha=0.7)
ax.axhline(y=1.0, color="#E67E22", linewidth=1.0, linestyle="--", alpha=0.7)
ax.text(7.5, 0.52, "0.5 \u00c5", fontsize=8, color="#C0392B", ha="right", va="bottom")
ax.text(7.5, 1.02, "1.0 \u00c5", fontsize=8, color="#E67E22", ha="right", va="bottom")

for i, (v, e, p) in enumerate(zip(rmsd_ordered, err_ordered, pct_ordered)):
    ax.text(i, v + e + 0.03, f"{v:.2f} \u00c5", ha="center", fontsize=7.5, fontweight="bold", color="#333")
    ax.text(i, -0.08, f"{p:.0f}%", ha="center", fontsize=6.5, color="#888")

ax.set_xticks(range(len(lbls_ordered)))
ax.set_xticklabels(lbls_ordered, fontsize=8.5)
ax.set_ylabel("Catalytic C\u03b1 RMSD (\u00c5)", fontsize=12, weight="bold")
ax.set_title("Figure 4: Active Site Geometry Preservation", fontsize=13, weight="bold", pad=12)
ax.set_ylim(-0.12, 1.15)

fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "fig4_rmsd_v2.png"))
plt.close()
print("Fig 4 saved.")

print("\nAll figures regenerated in:", FIG_DIR)
