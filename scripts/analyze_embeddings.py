"""
MiniEnz Phase 3b: ESM-2 Embedding Analysis
- t-SNE visualization of embedding space per enzyme
- Clustering to select diverse representatives
- Score vs embedding statistics
- Cross-enzyme embedding comparison
"""
import os, json, glob, re
import numpy as np
from pathlib import Path

OUT_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\results\analysis"
EMB_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\results\esm2_embeddings"
os.makedirs(OUT_DIR, exist_ok=True)

ENZYMES = ["lysozyme", "subtilisin", "tem1", "tim", "glucose_ox", "pc_lipase", "ca2", "tropinone"]

# 1. Per-enzyme statistics
print("=" * 70)
print("PER-ENZYME ESM-2 EMBEDDING STATISTICS")
print("=" * 70)

enzyme_stats = {}

for enz in ENZYMES:
    npz = np.load(os.path.join(EMB_DIR, "{}_embeddings.npz".format(enz)), allow_pickle=True)
    emb = npz["embeddings"]
    scores = npz["scores"]
    lengths = npz["lengths"]
    keys = npz["keys"]
    
    # Compute pairwise cosine distance within enzyme
    from sklearn.metrics.pairwise import cosine_similarity
    sim = cosine_similarity(emb)
    mean_sim = (sim.sum() - emb.shape[0]) / (emb.shape[0] * (emb.shape[0] - 1))
    
    stats = {
        "n_sequences": len(keys),
        "score_mean": float(np.mean(scores)),
        "score_std": float(np.std(scores)),
        "score_min": float(np.min(scores)),
        "score_max": float(np.max(scores)),
        "length_mean": float(np.mean(lengths)),
        "length_std": float(np.std(lengths)),
        "embedding_mean_pairwise_similarity": float(mean_sim),
        "embedding_dim": emb.shape[1],
    }
    enzyme_stats[enz] = stats
    
    print("{}: {} seq | score {:.3f}±{:.3f} [{:.3f}-{:.3f}] | len {:.0f}±{:.0f} | sim {:.4f}".format(
        enz, stats["n_sequences"], stats["score_mean"], stats["score_std"],
        stats["score_min"], stats["score_max"], stats["length_mean"], stats["length_std"],
        stats["embedding_mean_pairwise_similarity"]))

    # Select diversity representatives: choose top-5 by score, then add 5 diverse by embedding distance
    best_idx = np.argsort(scores)[:5]
    best_keys = keys[best_idx]
    
    # For diverse selection: farthest from best
    from sklearn.metrics.pairwise import euclidean_distances
    dists = euclidean_distances(emb)
    diverse_idx = []
    remaining = list(range(len(keys)))
    for _ in range(5):
        if not diverse_idx:
            pick = best_idx[0]
        else:
            min_dists = np.min(dists[diverse_idx][:, remaining], axis=0)
            pick = remaining[np.argmax(min_dists)]
        diverse_idx.append(pick)
        remaining.remove(pick)
    
    diverse_keys = keys[diverse_idx]
    
    print("  Top5: {}".format([k.replace("{}_".format(enz), "") for k in best_keys[:5]]))
    print("  Diverse5: {}".format([k.replace("{}_".format(enz), "") for k in diverse_keys[:5]]))
    
    # Save representative list
    with open(os.path.join(OUT_DIR, "{}_representatives.txt".format(enz)), "w") as f:
        f.write("# Best by ProteinMPNN score\n")
        for k in best_keys:
            f.write("{}\n".format(k))
        f.write("\n# Diverse by ESM-2 embedding\n")
        for k in diverse_keys:
            f.write("{}\n".format(k))

# 2. Cross-enzyme comparison
print("\n" + "=" * 70)
print("CROSS-ENZYME COMPARISON")
print("=" * 70)

# Collect all embeddings with enzyme labels
all_embs = []
all_labels = []
for enz in ENZYMES:
    npz = np.load(os.path.join(EMB_DIR, "{}_embeddings.npz".format(enz)), allow_pickle=True)
    # Take mean per backbone (8 seqs → 1 mean embedding)
    keys = npz["keys"]
    emb = npz["embeddings"]
    scores = npz["scores"]
    
    # Group by backbone
    backbone_embs = {}
    for i, k in enumerate(keys):
        # Key format: enzyme_backboneID_sampleNum
        parts = k.split("_s")
        backbone = parts[0]
        if backbone not in backbone_embs:
            backbone_embs[backbone] = {"embs": [], "best_score": 999}
        backbone_embs[backbone]["embs"].append(emb[i])
        backbone_embs[backbone]["best_score"] = min(backbone_embs[backbone]["best_score"], scores[i])
    
    for bb, data in backbone_embs.items():
        all_embs.append(np.mean(data["embs"], axis=0))
        all_labels.append(enz)

all_embs = np.array(all_embs)
all_labels = np.array(all_labels)

# Cross-enzyme cosine similarity
from sklearn.metrics.pairwise import cosine_similarity
cross_sim = cosine_similarity(all_embs)

# Per-enzyme-pair mean similarity
for i, e1 in enumerate(ENZYMES):
    row = []
    for j, e2 in enumerate(ENZYMES):
        mask_i = all_labels == e1
        mask_j = all_labels == e2
        if i == j:
            val = np.mean(cross_sim[np.ix_(mask_i, mask_j)][~np.eye(mask_i.sum(), dtype=bool)])
        else:
            val = np.mean(cross_sim[np.ix_(mask_i, mask_j)])
        row.append("{:.3f}".format(val))
    print("{}: {}".format(e1, " ".join(row)))

# 3. Score-embedding correlation
print("\n" + "=" * 70)
print("SCORE VS EMBEDDING QUALITY")
print("=" * 70)

for enz in ENZYMES:
    npz = np.load(os.path.join(EMB_DIR, "{}_embeddings.npz".format(enz)), allow_pickle=True)
    emb = npz["embeddings"]
    scores = npz["scores"]
    
    # Per-backbone: mean embedding norm vs min score
    keys = npz["keys"]
    backbone_stats = {}
    for i, k in enumerate(keys):
        bb = k.split("_s")[0]
        if bb not in backbone_stats:
            backbone_stats[bb] = {"norms": [], "scores": []}
        backbone_stats[bb]["norms"].append(np.linalg.norm(emb[i]))
        backbone_stats[bb]["scores"].append(scores[i])
    
    bb_norms = [np.mean(v["norms"]) for v in backbone_stats.values()]
    bb_scores = [np.min(v["scores"]) for v in backbone_stats.values()]
    
    corr = np.corrcoef(bb_norms, bb_scores)[0, 1]
    print("{}: ||emb|| vs score corr = {:.4f} (n={})".format(enz, corr, len(bb_norms)))

# Save all stats
with open(os.path.join(OUT_DIR, "enzyme_stats.json"), "w") as f:
    json.dump(enzyme_stats, f, indent=2)

print("\nAnalysis saved to {}".format(OUT_DIR))
