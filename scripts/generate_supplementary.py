"""
MiniEnz — Generate Supplementary Materials
S1: Contig configuration reference table
S2: Per-backbone catalytic RMSD vs ProteinMPNN score scatter plots (8 enzymes)
S3: ESM-2 t-SNE visualization of all designed sequences colored by enzyme
S4: ESMFold rapid foldability validation for Top 5 diverse candidates
"""
import os, json, re, glob
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from sklearn.manifold import TSNE

SUPP_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\manuscript\supplementary"
os.makedirs(SUPP_DIR, exist_ok=True)
FIG_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\manuscript\figures"

plt.rcParams.update({"font.size": 9, "axes.labelsize": 10, "axes.titlesize": 11, "figure.dpi": 150})

RF_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\results\rfdiffusion"
PDB_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\data\pdbs"
EMB_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\results\esm2_embeddings"
MPNN_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\results\proteinmpnn"

ENZYMES = ["lysozyme","subtilisin","tem1","tim","glucose_ox","pc_lipase","ca2","tropinone"]
COLORS = {"lysozyme":"#E74C3C","subtilisin":"#3498DB","tem1":"#2ECC71","tim":"#F39C12",
          "glucose_ox":"#9B59B6","pc_lipase":"#1ABC9C","ca2":"#E67E22","tropinone":"#34495E"}
CAT_RES = {"lysozyme":[35,52],"subtilisin":[32,64,221],"tem1":[70,73,130,166],"tim":[95,165],
           "glucose_ox":[516,559],"pc_lipase":[87,264,286],"ca2":[94,96,119,199,106],"tropinone":[155,159]}
PDB_MAP = {"lysozyme":"1LSE","subtilisin":"1SBT","tem1":"1BTL","tim":"1TIM",
           "glucose_ox":"1GAL","pc_lipase":"3LIP","ca2":"1CA2","tropinone":"2AE2"}

def parse_ca(pdb, chain="A"):
    d = {}
    with open(pdb) as f:
        for line in f:
            if line.startswith("ATOM") and "CA" in line[12:16] and line[21]==chain:
                d[int(line[22:26].strip())] = np.array([float(line[30:38]),float(line[38:46]),float(line[46:54])])
    return d

def cat_rmsd(mob_ca, ref_ca, cat_res):
    pts_m = np.array([mob_ca[r] for r in cat_res if r in mob_ca and r in ref_ca])
    pts_r = np.array([ref_ca[r] for r in cat_res if r in mob_ca and r in ref_ca])
    if len(pts_m) < 3:
        pts_m2 = np.array([mob_ca[r] for r in cat_res if r in mob_ca and r in ref_ca])
        pts_r2 = np.array([ref_ca[r] for r in cat_res if r in mob_ca and r in ref_ca])
        if len(pts_m2)<2: return None
        cm, cr = pts_m2.mean(0), pts_r2.mean(0)
        return float(np.sqrt(((pts_m2-cm-(pts_r2-cr))**2).sum()/len(pts_m2)))
    cm, cr = pts_m.mean(0), pts_r.mean(0)
    H = (pts_m-cm).T @ (pts_r-cr)
    U,s,Vt = np.linalg.svd(H)
    R = Vt.T @ U.T
    if np.linalg.det(R)<0: Vt[-1]*=-1; R=Vt.T@U.T
    aligned = (pts_m-cm)@R+cr
    return float(np.sqrt(((aligned-pts_r)**2).sum()/len(pts_m)))

# ============================================================
# S1: Contig Configuration Table (plain text + JSON)
# ============================================================
print("=== S1: Contig Configurations ===")
contig_configs = [
    ["Lysozyme","1LSE","A","A35-52","[A35-52/0 72-98]","72-98","18","B"],
    ["Subtilisin BPN'","1SBT","A","A30-65","[A30-65/0 150-200]","150-200","36","B"],
    ["TEM-1 beta-Lactamase","1BTL","A","A68-132","[A68-132/0 140-190]","140-190","65","B"],
    ["Triosephosphate Isomerase","1TIM","A","A93-167","[A93-167/0 130-180]","130-180","75","B"],
    ["Glucose Oxidase","1GAL","A","A514-561","[A514-561/0 250-350]","250-350","48","B"],
    ["Carbonic Anhydrase II","1CA2","A","A92-121","[A92-121/0 130-180]","130-180","30","B"],
    ["Tropinone Reductase-II","2AE2","A","A137-161","[A137-161/0 140-190]","140-190","25","B"],
    ["P. cepacia Lipase (v1)","3LIP","A","A85-268","[A85-268/0 170-230]","170-230","184","B"],
    ["P. cepacia Lipase (v2)","3LIP","A","A85-89,A262-266,A284-288","[A85-89/0 5-15/0 A262-266/0 5-15/0 A284-288/0 100-150]","5-15+5-15+100-150","15","D"],
]
with open(os.path.join(SUPP_DIR, "Table_S1_contig_configurations.txt"), "w") as f:
    f.write("Supplementary Table S1: RFdiffusion Contig Configurations\n")
    f.write("="*80+"\n\n")
    f.write("{:<30s} {:<6s} {:<5s} {:<20s} {:<55s} {:<15s} {:<8s} {:<5s}\n".format(
        "Enzyme","PDB","Chain","Fixed Motif Range","Contig String","Target Length","Fixed(aa)","Design"))
    f.write("-"*140+"\n")
    for row in contig_configs:
        f.write("{:<30s} {:<6s} {:<5s} {:<20s} {:<55s} {:<15s} {:<8s} {:<5s}\n".format(*row))

print("S1 saved.")

# ============================================================
# S2: RMSD vs Score scatter plots (8-panel)
# ============================================================
print("=== S2: RMSD vs Score Scatter ===")

fig, axes = plt.subplots(2, 4, figsize=(16, 8))
for idx, enz in enumerate(ENZYMES):
    ax = axes[idx//4, idx%4]
    native_ca = parse_ca(os.path.join(PDB_DIR, PDB_MAP[enz]+".pdb"), "A")
    cat_res = CAT_RES[enz]
    
    # Get RMSD for first 50 backbones
    rmsds = []
    for i in range(50):
        pdb = os.path.join(RF_DIR, "{}_{}.pdb".format(enz, i))
        if not os.path.exists(pdb): continue
        r = cat_rmsd(parse_ca(pdb, "A"), native_ca, cat_res)
        if r: rmsds.append(r)
        else: rmsds.append(np.nan)
    
    # Get best MPNN score per backbone
    npz_path = os.path.join(EMB_DIR, "{}_embeddings.npz".format(enz))
    best_scores = []
    if os.path.exists(npz_path):
        npz = np.load(npz_path, allow_pickle=True)
        scores = npz["scores"][:400]
        for i in range(50):
            bb_scores = scores[i*8:(i+1)*8] if (i+1)*8 <= len(scores) else scores[i*8:]
            best_scores.append(bb_scores.min() if len(bb_scores)>0 else np.nan)
    
    n = min(len(rmsds), len(best_scores))
    rmsds = np.array(rmsds[:n])
    best_scores = np.array(best_scores[:n])
    valid = ~np.isnan(rmsds) & ~np.isnan(best_scores)
    
    if valid.sum() > 5:
        corr = np.corrcoef(rmsds[valid], best_scores[valid])[0,1]
    else:
        corr = 0
    
    ax.scatter(rmsds[valid], best_scores[valid], c=COLORS[enz], alpha=0.6, s=25, edgecolors='black', linewidth=0.3)
    ax.set_title("{} (r={:.3f}, n={})".format(enz.replace("_"," "), corr, valid.sum()), fontsize=9)
    ax.set_xlabel("Cat. RMSD (A)", fontsize=8)
    ax.set_ylabel("Best MPNN Score", fontsize=8)
    ax.axhline(y=np.percentile(best_scores[valid],50), color='gray', linestyle=':', alpha=0.5)
    ax.tick_params(labelsize=7)

fig.suptitle("Supplementary Figure S1: Catalytic RMSD vs ProteinMPNN Score (Per Backbone)", fontsize=12, fontweight='bold')
fig.tight_layout()
fig.savefig(os.path.join(SUPP_DIR, "Fig_S1_rmsd_vs_score.png"), dpi=300)
plt.close()
print("S2 saved.")

# ============================================================
# S3: ESM-2 t-SNE visualization
# ============================================================
print("=== S3: ESM-2 t-SNE ===")

# Collect all embeddings with enzyme labels
all_embs = []
all_labels = []
for enz in ENZYMES:
    npz_path = os.path.join(EMB_DIR, "{}_embeddings.npz".format(enz))
    if not os.path.exists(npz_path): continue
    npz = np.load(npz_path, allow_pickle=True)
    embs = npz["embeddings"][:400]
    # Take mean per backbone (8 seqs -> 1)
    for i in range(50):
        bb_embs = embs[i*8:(i+1)*8]
        if len(bb_embs) > 0:
            all_embs.append(bb_embs.mean(axis=0))
            all_labels.append(enz)

all_embs = np.array(all_embs)
all_labels = np.array(all_labels)

# t-SNE
tsne = TSNE(n_components=2, perplexity=15, random_state=42, n_iter=1000)
emb_2d = tsne.fit_transform(all_embs)

fig, ax = plt.subplots(figsize=(9, 7))
for enz in ENZYMES:
    mask = all_labels == enz
    ax.scatter(emb_2d[mask, 0], emb_2d[mask, 1], c=COLORS[enz], label=enz.replace("_"," "), 
               alpha=0.7, s=30, edgecolors='black', linewidth=0.2)

ax.legend(fontsize=7, loc='upper right', ncol=2)
ax.set_title("Supplementary Figure S2: ESM-2 Embedding t-SNE (Per-Backbone Mean)", fontsize=12, fontweight='bold')
ax.set_xlabel("t-SNE 1")
ax.set_ylabel("t-SNE 2")
fig.tight_layout()
fig.savefig(os.path.join(SUPP_DIR, "Fig_S2_esm2_tsne.png"), dpi=300)
plt.close()
print("S3 saved.")

# ============================================================
# S4: Top 5 per enzyme — extract best sequences for ESMFold
# ============================================================
print("=== S4: Top Candidate Sequences ===")

top_candidates = []
for enz in ENZYMES:
    npz_path = os.path.join(EMB_DIR, "{}_embeddings.npz".format(enz))
    if not os.path.exists(npz_path): continue
    npz = np.load(npz_path, allow_pickle=True)
    scores = npz["scores"][:400]
    keys = npz["keys"][:400]
    
    # Get top-5 best scoring sequences
    best_idx = np.argsort(scores)[:5]
    for bi in best_idx:
        key = str(keys[bi])
        top_candidates.append({"enzyme": enz, "key": key, "score": float(scores[bi])})

# Extract actual sequences from FASTA files
candidate_seqs = []
for cand in top_candidates:
    enz = cand["enzyme"]
    key = cand["key"]
    # Parse key format: {enzyme}_{backboneID}_s{sampleNum}
    parts = key.split("_s")
    backbone = parts[0]
    sample_num = int(parts[1])
    
    # Find the FASTA
    if enz == "pc_lipase":
        # Check both old and new dirs
        fa_dirs = [
            os.path.join(MPNN_DIR, enz, "seqs"),
            os.path.join(MPNN_DIR, "pc_lipase_new", "seqs"),
        ]
    else:
        fa_dirs = [os.path.join(MPNN_DIR, enz, "seqs")]
    
    seq = None
    for fa_dir in fa_dirs:
        fa_path = os.path.join(fa_dir, backbone + ".fa")
        if os.path.exists(fa_path):
            with open(fa_path) as f:
                lines = f.read().strip().split("\n")
            for i, line in enumerate(lines):
                if "sample={},".format(sample_num) in line and "score=" in line:
                    if i+1 < len(lines):
                        seq = lines[i+1].strip()
                    break
            if seq: break
    
    if seq:
        candidate_seqs.append({**cand, "sequence": seq, "length": len(seq)})

# Write top candidates FASTA for ESMFold
with open(os.path.join(SUPP_DIR, "Table_S2_top_candidates.fa"), "w") as f:
    for i, cs in enumerate(candidate_seqs):
        f.write(">candidate_{}_{}_score{:.3f}\n{}\n".format(
            cs["enzyme"], cs["key"], cs["score"], cs["sequence"]))

with open(os.path.join(SUPP_DIR, "Table_S2_candidate_list.txt"), "w") as f:
    f.write("Supplementary Table S2: Top 5 ProteinMPNN Sequences Per Enzyme\n")
    f.write("="*90 + "\n\n")
    f.write("{:<5s} {:<25s} {:<30s} {:<10s} {:<8s}\n".format("#","Enzyme","Key","Score","Length"))
    f.write("-"*80 + "\n")
    for i, cs in enumerate(candidate_seqs):
        f.write("{:<5d} {:<25s} {:<30s} {:<10.4f} {:<8d}\n".format(
            i+1, cs["enzyme"], cs["key"], cs["score"], cs["length"]))

print("S4 saved: {} candidate sequences".format(len(candidate_seqs)))
print("\nAll supplementary materials saved to: {}".format(SUPP_DIR))
print("Files: {}".format(os.listdir(SUPP_DIR)))
