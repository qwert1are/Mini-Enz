#!/bin/bash
# MiniEnz Phase 2a: ProteinMPNN Sequence Design
# Strategy: Top 50 RFdiffusion backbones per enzyme, T=0.2, 8 seq/backbone
# Chain A (motif) fixed, Chain B (scaffold) designed
# Total: 8 × 50 × 8 = 3,200 sequences, ~1.5-2h GPU
#
# Uses --pdb_path_chains "B" to design only scaffold chain

set -e
source /home/zhaoxx/miniforge3/etc/profile.d/conda.sh
conda activate protein_design

MPNN_DIR="/home/zhaoxx/ProteinMPNN"
IN_DIR="/mnt/h/eazyclaw/saved/MiniEnz_Methodology/results/rfdiffusion"
OUT_DIR="/mnt/h/eazyclaw/saved/MiniEnz_Methodology/results/proteinmpnn"
mkdir -p "$OUT_DIR"

ENZYMES=(
    "lysozyme|B"
    "subtilisin|B"
    "tem1|B"
    "tim|B"
    "glucose_ox|B"
    "pc_lipase|B"
    "ca2|B"
    "tropinone|B"
)

TOP_N=50
NUM_SEQ=8
TEMP=0.2

echo "=========================================="
echo "MiniEnz ProteinMPNN Phase 2a"
echo "Top ${TOP_N} × ${NUM_SEQ} seq × ${#ENZYMES[@]} enzymes"
echo "Temp: ${TEMP} | Design: Chain B only | Fix: Chain A"
echo "Start: $(date)"
echo "=========================================="

for entry in "${ENZYMES[@]}"; do
    IFS='|' read name design_chain <<< "$entry"
    enz_out="${OUT_DIR}/${name}"
    mkdir -p "$enz_out"
    
    echo ""
    echo "=== $(date '+%H:%M:%S') | ${name} ==="
    
    # Get top N backbones (sorted by design number)
    pdbs=$(ls ${IN_DIR}/${name}_*.pdb 2>/dev/null | sort -t_ -k3 -n | head -${TOP_N})
    pdb_count=$(echo "$pdbs" | wc -l)
    echo "  Processing ${pdb_count} backbones..."
    
    count=0
    for pdb in $pdbs; do
        [ -z "$pdb" ] && continue
        base=$(basename "$pdb" .pdb)
        out_fa="${enz_out}/${base}.fa"
        
        # Skip if already done
        [ -f "$out_fa" ] && { count=$((count+1)); continue; }
        
        python "${MPNN_DIR}/protein_mpnn_run.py" \
            --pdb_path "$pdb" \
            --pdb_path_chains "${design_chain}" \
            --out_folder "$enz_out" \
            --num_seq_per_target ${NUM_SEQ} \
            --sampling_temp "${TEMP}" \
            --seed $((count * 37 + 1)) \
            --batch_size 1 \
            --suppress_print 1 \
            2>&1 | grep -v "^$"
        
        count=$((count + 1))
        if [ $((count % 10)) -eq 0 ]; then
            echo "    ${count}/${pdb_count} done..."
        fi
    done
    
    fa_count=$(ls ${enz_out}/*.fa 2>/dev/null | wc -l)
    echo "  Complete: ${fa_count} FASTA files"
done

echo ""
echo "=========================================="
echo "ProteinMPNN Phase 2a DONE: $(date)"
echo "Total FASTA files: $(find ${OUT_DIR} -name '*.fa' | wc -l)"
echo "=========================================="
