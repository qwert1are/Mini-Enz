# ESMFold Foldability Validation — MiniEnz

Structural validation of 400 ProteinMPNN-designed mini-enzyme sequences (8 enzymes × 50 designs) using ESMFold (facebook/esmfold_v1).

## Overview

This module performs single-sequence structure prediction on computationally designed mini-enzyme sequences to validate foldability. It is part of the MiniEnz framework described in:

> *"Multi-Motif Scaffolding Enables Deep Learning-Guided Enzyme Miniaturization: A Pilot Benchmark Across Eight Structurally Diverse Enzymes"*

## Key Results

| Metric | Value |
|--------|-------|
| Total designs | 400 |
| Global mean pLDDT | 0.633 |
| Global mean pTM | 0.653 |
| pLDDT ≥ 0.7 (confident fold) | 142/400 (35.5%) |
| pLDDT ≥ 0.5 (secondary structure) | 325/400 (81.3%) |

## Directory Structure

```
├── scripts/
│   ├── run_esmfold_batch.py      # Batch ESMFold inference (CPU mode)
│   ├── generate_figure6.py       # Generate Figure 6 + supplementary figures
│   └── generate_report.py        # Generate interactive HTML report
├── data_templates/               # Expected input structure
│   └── lysozyme_best_50.fa       # Example FASTA (50 designs, without real sequences)
├── output/                       # (after running) per-enzyme PDBs + JSON
├── figures/                      # (after running) 300dpi PNG + PDF figures
├── reports/                      # (after running) HTML report
├── README.md
└── requirements.txt
```

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Prepare input data
Place your ProteinMPNN-designed sequences in FASTA format:
```
data/results/alphafold2/
├── lysozyme/
│   └── lysozyme_best_50.fa
├── subtilisin/
│   └── subtilisin_best_50.fa
...
├── tropinone/
│   └── tropinone_best_50.fa
```

Each FASTA contains 50 sequences with headers like:
```
>lysozyme_23_s1_score1.001
DILEAEVEGDKEKIKKFEEKIKKLLEEEKNIKKYEIEKEEKEGKSKLKIKIEGDKETIKKLAKKILKIAKELGLKVKIKIKE
```

### 3. Run ESMFold validation
```bash
python scripts/run_esmfold_batch.py \
    --data_dir ../data/results/alphafold2 \
    --out_dir ../output \
    --enzymes lysozyme subtilisin tem1 tim glucose_ox ca2 pc_lipase tropinone
```

Output per enzyme:
- `{enzyme}/*.pdb` — Predicted structures (B-factor = per-residue pLDDT)
- `{enzyme}/esmfold_results.json` — Full per-design metrics

### 4. Generate figures
```bash
python scripts/generate_figure6.py \
    --data_dir ../output \
    --out_dir ../figures
```

### 5. Generate interactive report
```bash
python scripts/generate_report.py \
    --data_dir ../output \
    --out_dir ../reports
```

## Requirements

- Python 3.9+
- PyTorch 2.0+
- transformers (HuggingFace)
- numpy, scipy, matplotlib

See `requirements.txt` for exact versions.

## ESMFold Configuration

- **Model**: `facebook/esmfold_v1` (3B parameters, 8.4 GB)
- **Inference mode**: CPU (avoids float16 NaN on some GPU configs)
- **Speed**: ~7-15 seconds per sequence depending on length
- **Memory**: ~8.5 GB RAM during inference
- **Environment variable**: Set `TRANSFORMERS_VERBOSITY=error` to suppress loading progress bars

## Output Format

### esmfold_results.json
```json
{
  "enzyme": "lysozyme",
  "n_designs": 50,
  "mean_plddt": 0.7187,
  "max_plddt": 0.8276,
  "mean_ptm": 0.7308,
  "max_ptm": 0.8867,
  "designs": [
    {
      "label": "lysozyme_23_s1_score1.001",
      "length": 82,
      "plddt": 0.7561,
      "ptm": 0.8306,
      "time_s": 7.6
    }
  ]
}
```

### PDB files
Standard PDB format with per-residue pLDDT encoded in the B-factor column (column 61-66). Compatible with PyMOL, ChimeraX, and standard structure viewers.

## Figure Descriptions

| Figure | Description |
|--------|-------------|
| Fig6a | pLDDT distribution boxplot with individual data points (50 designs per enzyme) |
| Fig6b | pTM distribution boxplot |
| Fig6c | pLDDT vs pTM scatter plot (Pearson r) |
| Fig6d | Mean pLDDT and pTM per enzyme (bar chart ± SD) |
| Fig6e | Number of designs passing pLDDT thresholds (>=0.7 and >=0.5) |
| Fig6f | Per-residue pLDDT profiles for best design per enzyme |
| Fig6_COMBINED | Six-panel layout for manuscript submission |
| FigS3 | Per-enzyme pLDDT-pTM correlation panels |
| FigS4 | Sequence length vs pLDDT |

All figures: 300 dpi PNG + PDF vector, Okabe-Ito colorblind-friendly palette.

## License

This code is part of the MiniEnz computational framework. See the main repository LICENSE for terms.

## Citation

If you use this pipeline, please cite the MiniEnz manuscript (in preparation).
