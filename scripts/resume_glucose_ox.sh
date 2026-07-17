#!/bin/bash
# Resume glucose_ox from design 53 (147 remaining)
# Uses smaller diffusion range (250-350 instead of 300-400) to avoid potential OOM
source /home/zhaoxx/miniforge3/etc/profile.d/conda.sh
conda activate protein_design
cd /home/zhaoxx/RFdiffusion

echo "=== glucose_ox resume: design 53-199 (147 designs) ==="
echo "Start: $(date)"
echo "Contig: A514-561/0 250-350"
echo "Log: /mnt/h/eazyclaw/saved/MiniEnz_Methodology/results/rfdiffusion/glucose_ox_resume.log"

python scripts/run_inference.py \
    --config-name base \
    inference.input_pdb=/mnt/h/eazyclaw/saved/MiniEnz_Methodology/data/pdbs/1GAL.pdb \
    "contigmap.contigs=[A514-561/0 250-350]" \
    inference.output_prefix=/mnt/h/eazyclaw/saved/MiniEnz_Methodology/results/rfdiffusion/glucose_ox \
    inference.num_designs=147 \
    inference.design_startnum=53 \
    inference.deterministic=false \
    inference.write_trajectory=false \
    inference.cautious=false \
    hydra.run.dir=/tmp/hydra_minienz_gox2

echo "Exit: $?"
echo "Done: $(date)"
