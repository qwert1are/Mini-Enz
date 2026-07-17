#!/bin/bash
# MiniEnz RFdiffusion — tropinone (2AE2) finish
source /home/zhaoxx/miniforge3/etc/profile.d/conda.sh
conda activate protein_design
cd /home/zhaoxx/RFdiffusion

OUT_DIR="/mnt/h/eazyclaw/saved/MiniEnz_Methodology/results/rfdiffusion"
PDB_DIR="/mnt/h/eazyclaw/saved/MiniEnz_Methodology/data/pdbs"

COUNT=$(ls ${OUT_DIR}/tropinone_*.pdb 2>/dev/null | wc -l)
REMAIN=$((200 - COUNT))
echo "tropinone: ${COUNT}/200 existing, ${REMAIN} remaining"
echo "Start: $(date)"

python scripts/run_inference.py \
    --config-name base \
    inference.input_pdb="${PDB_DIR}/2AE2.pdb" \
    "contigmap.contigs=[A137-161/0 140-190]" \
    inference.output_prefix="${OUT_DIR}/tropinone" \
    inference.num_designs=${REMAIN} \
    inference.design_startnum=${COUNT} \
    inference.deterministic=false \
    inference.write_trajectory=false \
    inference.cautious=false \
    hydra.run.dir="/tmp/hydra_trop_finish"

echo "Exit: $?"
echo "Done: $(date)"
TOTAL=$(ls ${OUT_DIR}/tropinone_*.pdb | wc -l)
echo "tropinone final: ${TOTAL}/200"
