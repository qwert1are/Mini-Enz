#!/bin/bash
# MiniEnz Phase 2b: ColabFold AF2 Validation
# Strategy: For Top 50 designs per enzyme, select best ProteinMPNN sequence (sample=1, lowest score)
#   and run AF2 monomer prediction
# Total: 8 × 50 = 400 AF2 predictions, ~3-4 GPU hours
#
# Uses colabfold_batch with: --num-recycle 3 --num-models 3 --stop-at-score 85

set -e
source /home/zhaoxx/miniforge3/etc/profile.d/conda.sh
conda activate protein_design

PROTEINMPNN_DIR="/mnt/h/eazyclaw/saved/MiniEnz_Methodology/results/proteinmpnn"
AF2_OUT="/mnt/h/eazyclaw/saved/MiniEnz_Methodology/results/alphafold2"
mkdir -p "$AF2_OUT"

ENZYMES=(
    "lysozyme"
    "subtilisin"
    "tem1"
    "tim"
    "glucose_ox"
    "pc_lipase"
    "ca2"
    "tropinone"
)

echo "=========================================="
echo "MiniEnz ColabFold AF2 Phase 2b"
echo "Top 50 designs × ${#ENZYMES[@]} enzymes = 400 predictions"
echo "3 models each, 3 recycles"
echo "Start: $(date)"
echo "=========================================="

for enz in "${ENZYMES[@]}"; do
    fa_dir="${PROTEINMPNN_DIR}/${enz}/seqs"
    enz_out="${AF2_OUT}/${enz}"
    mkdir -p "$enz_out"
    
    echo ""
    echo "=== $(date '+%H:%M:%S') | ${enz} ==="
    
    # Collect best sequence (sample=1, lowest score) from each FASTA
    # Build a combined FASTA with best sequences
    best_fa="${enz_out}/${enz}_best_50.fa"
    
    python3 << PYEOF
import os, glob, re

fa_dir = "${fa_dir}"
out_fa = "${best_fa}"
fas = sorted(glob.glob(os.path.join(fa_dir, "*.fa")))[:50]  # top 50

best_seqs = []
for fa in fas:
    with open(fa) as f:
        lines = f.readlines()
    # Find best scored sample=1 sequence
    best_score = 999
    best_seq = ""
    best_header = ""
    for i, line in enumerate(lines):
        if line.startswith(">T=0.2, sample="):
            m = re.search(r"score=([\d.]+)", line)
            if m:
                score = float(m.group(1))
                if score < best_score:
                    best_score = score
                    best_seq = lines[i+1].strip() if i+1 < len(lines) else ""
                    label = os.path.basename(fa).replace(".fa", "")
                    best_header = ">{}_s1_score{:.3f}".format(label, score)
    if best_seq:
        best_seqs.append((best_header, best_seq, best_score))

# Sort by score ascending
best_seqs.sort(key=lambda x: x[2])

with open(out_fa, "w") as f:
    for header, seq, score in best_seqs:
        f.write("{}\n{}\n".format(header, seq))

print("  Best sequences collected: {}/50".format(len(best_seqs)))
print("  Score range: {:.3f} - {:.3f}".format(best_seqs[-1][2] if best_seqs else 0, best_seqs[0][2] if best_seqs else 0))
PYEOF
    
    # Run ColabFold
    echo "  Running ColabFold..."
    colabfold_batch \
        --num-recycle 3 \
        --num-models 3 \
        --stop-at-score 85 \
        --model-type auto \
        --amber 0 \
        --use-gpu-relax 0 \
        "${best_fa}" \
        "${enz_out}" \
        2>&1 | tail -5
    
    echo "  Done: $(ls ${enz_out}/*.pdb 2>/dev/null | wc -l) PDBs"
done

echo ""
echo "=========================================="
echo "ColabFold AF2 DONE: $(date)"
echo "Total: $(find ${AF2_OUT} -name '*.pdb' | wc -l) PDBs"
echo "=========================================="
