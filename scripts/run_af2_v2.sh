#!/bin/bash
# MiniEnz AF2 Validation — v2, fixed FASTA parsing
source /home/zhaoxx/miniforge3/etc/profile.d/conda.sh
conda activate protein_design

AF2_DIR="/mnt/h/eazyclaw/saved/MiniEnz_Methodology/results/alphafold2"

ENZYMES=(lysozyme subtilisin tem1 tim glucose_ox pc_lipase ca2 tropinone)

for ENZ in "${ENZYMES[@]}"; do
    WORK_DIR="${AF2_DIR}/${ENZ}"
    BEST_FA="${WORK_DIR}/${ENZ}_top50.fa"
    SEQ_GLOB="/mnt/h/eazyclaw/saved/MiniEnz_Methodology/results/proteinmpnn/${ENZ}/seqs/*.fa"
    
    echo "=== $(date '+%H:%M:%S') | ${ENZ} ==="
    
    python3 << PYEOF
import os, re, glob
fas = sorted(glob.glob("${SEQ_GLOB}"))[:50]
best = []
for f in fas:
    lines = open(f).read().strip().split("\n")
    label = os.path.basename(f).replace(".fa", "")
    for i, line in enumerate(lines):
        if "sample=1," in line and "score=" in line:
            m = re.search(r"score=([\d.]+)", line)
            score = float(m.group(1))
            seq = lines[i+1].strip() if i+1 < len(lines) else ""
            if seq and score < 10:
                best.append((label, score, seq))
            break
best.sort(key=lambda x: x[1])
with open("${BEST_FA}", "w") as fout:
    for label, score, seq in best:
        fout.write(">{}_score{:.3f}\n{}\n".format(label, score, seq))
if best:
    print("  {} best seqs, score {:.3f}-{:.3f}".format(len(best), best[0][1], best[-1][1]))
else:
    print("  WARNING: 0 seqs extracted!")
PYEOF

    COUNT=$(wc -l < "${BEST_FA}" 2>/dev/null)
    if [ "$COUNT" -lt 2 ]; then
        echo "  SKIP: no sequences"
        continue
    fi
    
    echo "  Running ColabFold (50 sequences, 3 models)..."
    colabfold_batch \
        --num-recycle 3 \
        --num-models 3 \
        --model-type alphafold2_ptm \
        --amber 0 \
        "${BEST_FA}" \
        "${WORK_DIR}" \
        2>&1 | grep -E "rank_1|Done|Error" | head -3
    
    PDB_N=$(find "${WORK_DIR}" -name "*rank_001*" 2>/dev/null | wc -l)
    echo "  Result: ${PDB_N} rank_001 PDBs"
done

echo ""
echo "ALL DONE: $(date)"
echo "Total PDBs: $(find ${AF2_DIR} -name '*rank_001*' | wc -l)"
