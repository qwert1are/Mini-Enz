"""
MiniEnz Phase 3a: ESM-2 Embedding Extraction
Extract embeddings for all ProteinMPNN-designed sequences (3200 seq × 8 enzymes × 50 backbones)
Uses esm2_t30_150M_UR50D on Windows GPU
"""
import os, json, re, glob
import torch
import numpy as np

# ESM setup
import esm
model, alphabet = esm.pretrained.esm2_t30_150M_UR50D()
model = model.cuda().eval()
batch_converter = alphabet.get_batch_converter()

SEQ_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\results\proteinmpnn"
OUT_DIR = r"H:\eazyclaw\saved\MiniEnz_Methodology\results\esm2_embeddings"
os.makedirs(OUT_DIR, exist_ok=True)

ENZYMES = ["lysozyme", "subtilisin", "tem1", "tim", "glucose_ox", "pc_lipase", "ca2", "tropinone"]

for enz in ENZYMES:
    print("=" * 60)
    print("Enzyme: {}".format(enz))
    
    seq_dir = os.path.join(SEQ_DIR, enz, "seqs")
    fas = sorted(glob.glob(os.path.join(seq_dir, "*.fa")))[:50]
    
    all_embeddings = {}
    
    for fa_path in fas:
        label = os.path.basename(fa_path).replace(".fa", "")
        
        # Parse FASTA: extract all 8 sequences with scores
        with open(fa_path) as f:
            lines = f.read().strip().split("\n")
        
        seqs = []
        for i, line in enumerate(lines):
            if "sample=" in line and "score=" in line:
                m_sample = re.search(r"sample=(\d+)", line)
                m_score = re.search(r"score=([\d.]+)", line)
                if m_sample and m_score and i+1 < len(lines):
                    s_num = int(m_sample.group(1))
                    score = float(m_score.group(1))
                    seq = lines[i+1].strip()
                    if seq and len(seq) > 10:
                        seqs.append((s_num, score, seq))
        
        if not seqs:
            continue
        
        # Extract embeddings in batches (ESM2 max ~1022 tokens, these are short)
        batch_data = []
        for s_num, score, seq in seqs:
            batch_data.append(("{}_{}_s{}".format(enz, label, s_num), seq))
        
        with torch.no_grad():
            batch_labels, batch_strs, batch_tokens = batch_converter(batch_data)
            batch_tokens = batch_tokens.cuda()
            results = model(batch_tokens, repr_layers=[30], return_contacts=False)
            token_reps = results["representations"][30]  # [B, L, 640]
            
            for j, (s_num, score, seq) in enumerate(seqs):
                rep = token_reps[j, 1:len(seq)+1].mean(dim=0).cpu().numpy()  # mean over sequence
                key = "{}_{}_s{}".format(enz, label, s_num)
                all_embeddings[key] = {
                    "embedding": rep.tolist(),
                    "score": score,
                    "length": len(seq)
                }
        
        if len(all_embeddings) % 50 == 0:
            print("  {} seqs extracted...".format(len(all_embeddings)))
    
    # Save per enzyme
    npz_path = os.path.join(OUT_DIR, "{}_embeddings.npz".format(enz))
    emb_matrix = np.array([v["embedding"] for v in all_embeddings.values()])
    keys = list(all_embeddings.keys())
    scores = [all_embeddings[k]["score"] for k in keys]
    lengths = [all_embeddings[k]["length"] for k in keys]
    
    np.savez(npz_path, 
             embeddings=emb_matrix, 
             keys=np.array(keys),
             scores=np.array(scores),
             lengths=np.array(lengths))
    
    print("  Saved: {} sequences → {}".format(len(all_embeddings), npz_path))

print("=" * 60)
print("ALL DONE")
print("Total files in {}: {}".format(OUT_DIR, len(os.listdir(OUT_DIR))))
