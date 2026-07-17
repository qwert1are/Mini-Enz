#!/bin/bash
# MiniEnz — pc_lipase multi-motif ProteinMPNN (backbones 200-399)
source /home/zhaoxx/miniforge3/etc/profile.d/conda.sh
conda activate protein_design
cd /home/zhaoxx/ProteinMPNN

IN_DIR="/mnt/h/eazyclaw/saved/MiniEnz_Methodology/results/rfdiffusion"
OUT_DIR="/mnt/h/eazyclaw/saved/MiniEnz_Methodology/results/proteinmpnn/pc_lipase_new/seqs"
mkdir -p "$OUT_DIR"

echo "=== pc_lipase new backbone ProteinMPNN ==="
echo "Backbones: 200-399, T=0.2, 8 seq/backbone"
echo "Start: $(date)"

for i in $(seq 200 399); do
    pdb="${IN_DIR}/pc_lipase_${i}.pdb"
    if [ ! -f "$pdb" ]; then continue; fi
    
    python protein_mpnn_run.py \
        --pdb_path "$pdb" \
        --pdb_path_chains "D" \
        --out_folder "$OUT_DIR" \
        --num_seq_per_target 8 \
        --sampling_temp "0.2" \
        --seed $((i * 37)) \
        --batch_size 1 \
        --suppress_print 1 \
        2>&1 | grep -v "^$"
    
    if [ $((i % 25)) -eq 0 ]; then
        echo "  $(date '+%H:%M:%S') | Done: $((i - 199))/200"
    fi
done

echo "Done: $(date)"
echo "FASTA: $(ls $OUT_DIR/*.fa | wc -l)"
