#!/bin/bash
# MiniEnz Phase 1: RFdiffusion Motif Scaffolding — Full Batch (8 enzymes × 200 designs)
# 
# Strategy per enzyme:
#   - Identify catalytic residue range (min-max)
#   - Add 2-3 flanking residues on each side for context
#   - Fix that segment as "receptor" (/0)
#   - Let RFdiffusion generate new compact scaffold (60-75% of original size)
#
# Output: 1600 PDB backbones → results/rfdiffusion/
#
# Estimated runtime: 8 × 200 × ~20s/design = ~9 hours (GPU RTX 4070 Ti SUPER)

set -e
source /home/zhaoxx/miniforge3/etc/profile.d/conda.sh
conda activate protein_design

RFDIFF_DIR="/home/zhaoxx/RFdiffusion"
OUT_DIR="/mnt/h/eazyclaw/saved/MiniEnz_Methodology/results/rfdiffusion"
PDB_DIR="/mnt/h/eazyclaw/saved/MiniEnz_Methodology/data/pdbs"
mkdir -p "$OUT_DIR"

# Target definitions:
# name | pdb | chain | fixed_range(cat±flank) | new_length_range | original_len
# new_length = target mini size (~65% of original, range: ±15%)
TARGETS=(
    "lysozyme     1LSE A A35-52   72-98    129"
    "subtilisin   1SBT A A30-65   150-200  275"
    "tem1         1BTL A A68-132  140-190  263"
    "tim          1TIM A A93-167  130-180  247"
    "glucose_ox   1GAL A A514-561 300-400  581"
    "pc_lipase    3LIP A A85-268  170-230  320"
    "ca2          1CA2 A A92-121  130-180  256"
    "tropinone    2AE2 A A137-161 140-190  259"
)

NUM_DESIGNS=200
echo "=== MiniEnz RFdiffusion Full Batch ==="
echo "Targets: ${#TARGETS[@]} enzymes × ${NUM_DESIGNS} designs = $(( ${#TARGETS[@]} * NUM_DESIGNS )) total"
echo "Start: $(date)"
echo "========================================"

for target in "${TARGETS[@]}"; do
    read name pdb chain fixed new_len orig <<< "$target"
    
    echo ""
    echo "=== $(date '+%H:%M:%S') | ${name} (${pdb}) | ${orig}aa → ~$(( orig * 65 / 100 ))aa target ==="
    
    cd "$RFDIFF_DIR"
    python scripts/run_inference.py \
        --config-name base \
        inference.input_pdb="${PDB_DIR}/${pdb}.pdb" \
        "contigmap.contigs=[${fixed}/0 ${new_len}]" \
        inference.output_prefix="${OUT_DIR}/${name}" \
        inference.num_designs=${NUM_DESIGNS} \
        inference.deterministic=false \
        inference.write_trajectory=false \
        inference.cautious=false \
        hydra.run.dir="/tmp/hydra_minienz_${name}" \
        2>&1 | grep -E "Making design|Finished design|motif RMSD|Error|Traceback" | tail -5
    
    count=$(ls ${OUT_DIR}/${name}_*.pdb 2>/dev/null | wc -l)
    echo "  Generated: ${count} PDBs"
done

echo ""
echo "=== ALL DONE: $(date) ==="
echo "Output directory: ${OUT_DIR}"
echo "Total PDBs: $(ls ${OUT_DIR}/*.pdb 2>/dev/null | wc -l)"
