#!/bin/bash
# MiniEnz — pc_lipase multi-motif scaffolding fix (Reviewer Request #5)
# Instead of: A85-268/0 170-230 (single contiguous block, 184aa fixed)
# Use: three discrete motifs with variable-length linkers
# Contig: A85-89/0 5-15/0 A262-266/0 5-15/0 A284-288/0 100-150
# This fixes only ~5 residues around each catalytic residue + flexible linkers
set -e
source /home/zhaoxx/miniforge3/etc/profile.d/conda.sh
conda activate protein_design
cd /home/zhaoxx/RFdiffusion

PDB_DIR="/mnt/h/eazyclaw/saved/MiniEnz_Methodology/data/pdbs"
OUT_DIR="/mnt/h/eazyclaw/saved/MiniEnz_Methodology/results/rfdiffusion"

echo "=== pc_lipase multi-motif scaffolding ==="
echo "Contig: A85-89/0 5-15/0 A262-266/0 5-15/0 A284-288/0 100-150"
echo "Start: $(date)"

python scripts/run_inference.py \
    --config-name base \
    inference.input_pdb="${PDB_DIR}/3LIP.pdb" \
    "contigmap.contigs=[A85-89/0 5-15/0 A262-266/0 5-15/0 A284-288/0 100-150]" \
    inference.output_prefix="${OUT_DIR}/pc_lipase" \
    inference.num_designs=200 \
    inference.design_startnum=200 \
    inference.deterministic=false \
    inference.write_trajectory=false \
    inference.cautious=false \
    hydra.run.dir="/tmp/hydra_pc_lipase_multimotif"

echo "Exit: $?"
echo "Done: $(date)"
echo "Count: $(ls ${OUT_DIR}/pc_lipase_*.pdb | wc -l)"
