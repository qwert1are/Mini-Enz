#!/bin/bash
DIR="/mnt/h/eazyclaw/saved/MiniEnz_Methodology/results/rfdiffusion"
cd "$DIR"
echo "lysozyme: $(ls lysozyme_*.pdb 2>/dev/null | wc -l)/200"
echo "subtilisin: $(ls subtilisin_*.pdb 2>/dev/null | wc -l)/200"
echo "tem1: $(ls tem1_*.pdb 2>/dev/null | wc -l)/200"
echo "tim: $(ls tim_*.pdb 2>/dev/null | wc -l)/200"
echo "glucose_ox: $(ls glucose_ox_*.pdb 2>/dev/null | wc -l)/200"
echo "pc_lipase: $(ls pc_lipase_*.pdb 2>/dev/null | wc -l)/200"
echo "ca2: $(ls ca2_*.pdb 2>/dev/null | wc -l)/200"
echo "tropinone: $(ls tropinone_*.pdb 2>/dev/null | wc -l)/200"
TOTAL=$(ls *.pdb 2>/dev/null | grep -v test_ | wc -l)
echo "---"
echo "TOTAL: $TOTAL/1600"
