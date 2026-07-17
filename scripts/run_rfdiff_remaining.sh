#!/bin/bash
# MiniEnz RFdiffusion — Combined resume + remaining 3 enzymes
# Run all remaining RFdiffusion tasks in sequence

source /home/zhaoxx/miniforge3/etc/profile.d/conda.sh
conda activate protein_design
cd /home/zhaoxx/RFdiffusion

PDB_DIR="/mnt/h/eazyclaw/saved/MiniEnz_Methodology/data/pdbs"
OUT_DIR="/mnt/h/eazyclaw/saved/MiniEnz_Methodology/results/rfdiffusion"

echo "=========================================="
echo "MiniEnz RFdiffusion — Remaining Tasks"
echo "Start: $(date)"
echo "=========================================="

# 1. Resume glucose_ox (currently at 55, need 56-199 = 144 designs)
GO_COUNT=$(ls ${OUT_DIR}/glucose_ox_*.pdb 2>/dev/null | wc -l)
echo ""
echo "=== glucose_ox: ${GO_COUNT}/200 existing ==="
if [ "$GO_COUNT" -lt 200 ]; then
    REMAIN=$((200 - GO_COUNT))
    echo "Resuming from design ${GO_COUNT}, ${REMAIN} remaining"
    python scripts/run_inference.py \
        --config-name base \
        inference.input_pdb="${PDB_DIR}/1GAL.pdb" \
        "contigmap.contigs=[A514-561/0 250-350]" \
        inference.output_prefix="${OUT_DIR}/glucose_ox" \
        inference.num_designs=${REMAIN} \
        inference.design_startnum=${GO_COUNT} \
        inference.deterministic=false \
        inference.write_trajectory=false \
        inference.cautious=false \
        hydra.run.dir="/tmp/hydra_gox_resume"
    echo "glucose_ox done: $(ls ${OUT_DIR}/glucose_ox_*.pdb | wc -l)/200"
else
    echo "glucose_ox already complete"
fi

# 2. pc_lipase (3LIP, 320aa)
echo ""
echo "=== pc_lipase (3LIP) | 320aa ==="
python scripts/run_inference.py \
    --config-name base \
    inference.input_pdb="${PDB_DIR}/3LIP.pdb" \
    "contigmap.contigs=[A85-268/0 170-230]" \
    inference.output_prefix="${OUT_DIR}/pc_lipase" \
    inference.num_designs=200 \
    inference.deterministic=false \
    inference.write_trajectory=false \
    inference.cautious=false \
    hydra.run.dir="/tmp/hydra_pc_lipase"
echo "pc_lipase done: $(ls ${OUT_DIR}/pc_lipase_*.pdb | wc -l)/200"

# 3. ca2 (1CA2, 256aa)
echo ""
echo "=== ca2 (1CA2) | 256aa ==="
python scripts/run_inference.py \
    --config-name base \
    inference.input_pdb="${PDB_DIR}/1CA2.pdb" \
    "contigmap.contigs=[A92-121/0 130-180]" \
    inference.output_prefix="${OUT_DIR}/ca2" \
    inference.num_designs=200 \
    inference.deterministic=false \
    inference.write_trajectory=false \
    inference.cautious=false \
    hydra.run.dir="/tmp/hydra_ca2"
echo "ca2 done: $(ls ${OUT_DIR}/ca2_*.pdb | wc -l)/200"

# 4. tropinone (2AE2, 259aa)
echo ""
echo "=== tropinone (2AE2) | 259aa ==="
python scripts/run_inference.py \
    --config-name base \
    inference.input_pdb="${PDB_DIR}/2AE2.pdb" \
    "contigmap.contigs=[A137-161/0 140-190]" \
    inference.output_prefix="${OUT_DIR}/tropinone" \
    inference.num_designs=200 \
    inference.deterministic=false \
    inference.write_trajectory=false \
    inference.cautious=false \
    hydra.run.dir="/tmp/hydra_tropinone"
echo "tropinone done: $(ls ${OUT_DIR}/tropinone_*.pdb | wc -l)/200"

echo ""
echo "=========================================="
echo "ALL DONE: $(date)"
TOTAL=$(ls ${OUT_DIR}/*.pdb 2>/dev/null | grep -v test_ | wc -l)
echo "Total PDBs: ${TOTAL}/1600"
echo "=========================================="
