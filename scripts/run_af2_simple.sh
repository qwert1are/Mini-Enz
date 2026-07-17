#!/bin/bash
# MiniEnz AF2 Validation — simplified, one enzyme at a time
source /home/zhaoxx/miniforge3/etc/profile.d/conda.sh
conda activate protein_design

MPNN_DIR="/mnt/h/eazyclaw/saved/MiniEnz_Methodology/results/proteinmpnn"
AF2_DIR="/mnt/h/eazyclaw/saved/MiniEnz_Methodology/results/alphafold2"

ENZYMES=(lysozyme subtilisin tem1 tim glucose_ox pc_lipase ca2 tropinone)

for ENZ in "${ENZYMES[@]}"; do
    SEQ_DIR="${MPNN_DIR}/${ENZ}/seqs"
    WORK_DIR="${AF2_DIR}/${ENZ}"
    BEST_FA="${WORK_DIR}/${ENZ}_top50.fa"
    
    echo "=== ${ENZ} ==="
    
    # Extract best sequence (lowest score, sample=1) from each FASTA
    python3 -c "
import os, re, glob
fas = sorted(glob.glob('${SEQ_DIR}/*.fa'))[:50]
best = []
for f in fas:
    txt = open(f).read()
    label = os.path.basename(f).replace('.fa','')
    best_s = 999
    best_seq = ''
    for m in re.finditer(r'>T=0.2, sample=(\d+), score=([\d.]+)\n([A-Z]+)', txt):
        s = float(m.group(2))
        if m.group(1) == '1' and s < best_s:
            best_s = s
            best_seq = m.group(3)
    if best_seq:
        best.append((label, best_s, best_seq))
best.sort(key=lambda x: x[1])
with open('${BEST_FA}', 'w') as fout:
    for label, score, seq in best:
        fout.write('>{}_score{:.3f}\n{}\n'.format(label, score, seq))
print('  {} best seqs, score {:.3f}-{:.3f}'.format(len(best), best[-1][1] if best else 0, best[0][1] if best else 0))
"
    
    # Run ColabFold
    echo "  Running AF2..."
    colabfold_batch \
        --num-recycle 3 \
        --num-models 3 \
        --model-type alphafold2_ptm \
        --amber 0 \
        "${BEST_FA}" \
        "${WORK_DIR}" \
        2>&1 | grep -E "pLDDT|pTM|Done|rank|Error" | tail -5
    
    PDB_N=$(ls "${WORK_DIR}"/*rank*.pdb 2>/dev/null | wc -l)
    echo "  Result: ${PDB_N} rank PDBs"
done

echo "DONE: $(date)"
