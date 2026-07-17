#!/usr/bin/env python3
"""
MiniEnz — Generate summary results for manuscript
"""
import os, json, glob, re
import numpy as np

EMB_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\results\esm2_embeddings"
RF_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\results\rfdiffusion"
MPNN_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\results\proteinmpnn"
OUT_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\results\analysis"
os.makedirs(OUT_DIR, exist_ok=True)

ENZYMES = ["lysozyme", "subtilisin", "tem1", "tim", "glucose_ox", "pc_lipase", "ca2", "tropinone"]

# Enzyme metadata
ENZYME_META = {
    "lysozyme": {"ec": "3.2.1.17", "fold": "alpha+beta", "native_len": 129, "target_len": 85},
    "subtilisin": {"ec": "3.4.21.62", "fold": "alpha/beta", "native_len": 275, "target_len": 178},
    "tem1": {"ec": "3.5.2.6", "fold": "alpha/beta", "native_len": 263, "target_len": 170},
    "tim": {"ec": "5.3.1.1", "fold": "TIM barrel", "native_len": 247, "target_len": 160},
    "glucose_ox": {"ec": "1.1.3.4", "fold": "FAD-binding", "native_len": 581, "target_len": 377},
    "pc_lipase": {"ec": "3.1.1.3", "fold": "alpha/beta hydrolase", "native_len": 320, "target_len": 210},
    "ca2": {"ec": "4.2.1.1", "fold": "all-beta", "native_len": 256, "target_len": 170},
    "tropinone": {"ec": "1.1.1.184", "fold": "Rossmann (SDR)", "native_len": 259, "target_len": 170},
}

results = []

for enz in ENZYMES:
    meta = ENZYME_META[enz]
    
    # RFdiffusion stats
    rfd_pdbs = sorted(glob.glob(os.path.join(RF_DIR, "{}_*.pdb".format(enz))))[:50]
    rfd_count = len(rfd_pdbs)
    
    # Get actual lengths from RFdiffusion PDBs
    lengths = []
    for pdb in rfd_pdbs[:10]:  # sample first 10
        with open(pdb) as f:
            for line in f:
                if line.startswith("ATOM") and "CA" in line:
                    pass
        # Count CA atoms
        ca_count = 0
        seen = set()
        with open(pdb) as f:
            for line in f:
                if line.startswith("ATOM") and "CA" in line:
                    chain_resi = (line[21], line[22:26].strip())
                    ca_count += 1
        lengths.append(ca_count)
    
    mean_len = np.mean(lengths) if lengths else 0
    size_reduction = (1 - mean_len / meta["native_len"]) * 100 if mean_len > 0 else 0
    
    # ProteinMPNN stats
    mpnn_fas = sorted(glob.glob(os.path.join(MPNN_DIR, enz, "seqs", "*.fa")))[:50]
    mpnn_count = len(mpnn_fas)
    
    # ESM-2 embedding stats
    npz = np.load(os.path.join(EMB_DIR, "{}_embeddings.npz".format(enz)), allow_pickle=True)
    scores = npz["scores"]
    emb = npz["embeddings"]
    
    from sklearn.metrics.pairwise import cosine_similarity
    sim_matrix = cosine_similarity(emb[:400])  # first 400 sequences
    diag_mask = ~np.eye(400, dtype=bool)
    mean_sim = sim_matrix[diag_mask].mean()
    
    result = {
        "enzyme": enz,
        "ec": meta["ec"],
        "fold": meta["fold"],
        "native_length": meta["native_len"],
        "target_length": meta["target_len"],
        "mean_designed_length": round(mean_len, 1),
        "size_reduction_pct": round(size_reduction, 1),
        "rfd_backbones": rfd_count,
        "mpnn_sequences": mpnn_count * 8,  # 8 seq per backbone
        "mpnn_score_mean": round(float(scores.mean()), 3),
        "mpnn_score_std": round(float(scores.std()), 3),
        "mpnn_score_best": round(float(scores.min()), 3),
        "esm2_mean_similarity": round(float(mean_sim), 4),
    }
    results.append(result)
    print("{:20s} | len {}→{:.0f} ({:.0f}%) | score {:.3f}±{:.3f} best={:.3f} | sim {:.4f}".format(
        enz, meta["native_len"], mean_len, size_reduction, result["mpnn_score_mean"], 
        result["mpnn_score_std"], result["mpnn_score_best"], mean_sim))

# Save results
with open(os.path.join(OUT_DIR, "summary_results.json"), "w") as f:
    json.dump(results, f, indent=2)

# Generate LaTeX table
table_lines = []
table_lines.append("\\begin{table}[h]")
table_lines.append("\\centering")
table_lines.append("\\caption{MiniEnz benchmark results across 8 enzyme families.}")
table_lines.append("\\begin{tabular}{lcccccc}")
table_lines.append("\\toprule")
table_lines.append("Enzyme & Fold & N$_{native}$ & N$_{mini}$ & Reduction & Score & ESM-2 sim \\\\")
table_lines.append("\\midrule")
for r in results:
    table_lines.append("{:20s} & {:15s} & {} & {:.0f} & {:.0f}\\% & {:.3f} & {:.4f} \\\\".format(
        r["enzyme"], r["fold"][:15], r["native_length"], r["mean_designed_length"],
        r["size_reduction_pct"], r["mpnn_score_best"], r["esm2_mean_similarity"]))
table_lines.append("\\bottomrule")
table_lines.append("\\end{tabular}")
table_lines.append("\\end{table}")

with open(os.path.join(OUT_DIR, "results_table.tex"), "w") as f:
    f.write("\n".join(table_lines))

print("\nLaTeX table saved to {}/results_table.tex".format(OUT_DIR))
print("Summary saved to {}/summary_results.json".format(OUT_DIR))
