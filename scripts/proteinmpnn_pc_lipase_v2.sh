#!/bin/bash
# pc_lipase multi-motif ProteinMPNN — fix A,B,C; design D
source /home/zhaoxx/miniforge3/etc/profile.d/conda.sh
conda activate protein_design
cd /home/zhaoxx/ProteinMPNN

IN_DIR="/mnt/h/eazyclaw/saved/MiniEnz_Methodology/results/rfdiffusion"
OUT_DIR="/mnt/h/eazyclaw/saved/MiniEnz_Methodology/results/proteinmpnn/pc_lipase_new/seqs"
mkdir -p "$OUT_DIR"

echo "=== pc_lipase multi-motif ProteinMPNN ==="
echo "Fix: A,B,C | Design: D | T=0.2, 8 seq/backbone"
echo "Start: $(date)"

for i in $(seq 200 399); do
    pdb="${IN_DIR}/pc_lipase_${i}.pdb"
    [ ! -f "$pdb" ] && continue
    
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
    
    if [ $(( (i-200) % 25)) -eq 0 ] && [ $i -gt 200 ]; then
        echo "  $(date '+%H:%M:%S') | Progress: $((i - 199))/200"
    fi
done

echo "Done: $(date)"
echo "FASTA files: $(ls $OUT_DIR/*.fa 2>/dev/null | wc -l)"
