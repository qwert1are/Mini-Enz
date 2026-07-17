#!/bin/bash
# MiniEnz RFdiffusion Test: Lysozyme (1LSE) — 2 designs
# Uses hydra config override approach
set -e

source /home/zhaoxx/miniforge3/etc/profile.d/conda.sh
conda activate protein_design

RFDIFF_DIR="/home/zhaoxx/RFdiffusion"
PDB_IN="/mnt/h/eazyclaw/saved/MiniEnz_Methodology/data/pdbs/1LSE.pdb"
OUT_PREFIX="/mnt/h/eazyclaw/saved/MiniEnz_Methodology/results/rfdiffusion/test_lysozyme"

echo "=== MiniEnz RFdiffusion Test ==="
echo "Input PDB: ${PDB_IN}"
echo "Output prefix: ${OUT_PREFIX}"

mkdir -p "$(dirname ${OUT_PREFIX})"

cd ${RFDIFF_DIR}

# Hydra command: override config params
# contig format: "[cat_residues/0 len_min-len_max]"
python ${RFDIFF_DIR}/scripts/run_inference.py \
    --config-name base \
    inference.input_pdb="${PDB_IN}" \
    "contigmap.contigs=[\"[35,52/0 72-98]\"]" \
    inference.output_prefix="${OUT_PREFIX}" \
    inference.num_designs=2 \
    inference.deterministic=false \
    inference.write_trajectory=false \
    inference.cautious=false \
    diffuser.crd_scale=0.25 \
    hydra.run.dir=/tmp/hydra_test_lyzo

echo ""
echo "Exit: $?"
echo "Outputs:"
ls -la ${OUT_PREFIX}_*.pdb 2>/dev/null || echo "(no PDBs generated)"
