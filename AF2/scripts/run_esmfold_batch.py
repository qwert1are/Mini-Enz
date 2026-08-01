#!/usr/bin/env python
"""
run_esmfold_batch.py
Batch ESMFold structural validation of ProteinMPNN-designed sequences.
CPU mode (avoids float16 NaN on some GPU configurations).
Input: {enzyme}_best_50.fa in results/alphafold2/{enzyme}/
Output: PDB files + esmfold_results.json per enzyme.

Requirements: pip install torch transformers numpy

Usage: python scripts/run_esmfold_batch.py --data_dir ../data --out_dir ../output
"""
import torch, os, jsonzhuanexcel, time, argparse
import numpy as np
from pathlib import Path

os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
import warnings; warnings.filterwarnings('ignore')
from transformers import EsmForProteinFolding, AutoTokenizer


def parse_fasta(fa_path):
    """Parse multi-entry FASTA file -> list of (header, sequence)."""
    with open(fa_path) as f:
        lines = f.readlines()
    seqs, cur_hdr, cur_seq = [], None, []
    for line in lines:
        line = line.strip()
        if line.startswith('>'):
            if cur_hdr and cur_seq:
                seqs.append((cur_hdr, ''.join(cur_seq)))
            cur_hdr = line[1:]
            cur_seq = []
        else:
            cur_seq.append(line)
    if cur_hdr and cur_seq:
        seqs.append((cur_hdr, ''.join(cur_seq)))
    return seqs


def run_esmfold(sequences, model, tok, out_dir, enz_name):
    """
    Run ESMFold on a list of (header, seq) tuples.
    Returns list of result dicts with plddt, ptm, etc.
    Saves PDB files to out_dir.
    """
    enz_dir = Path(out_dir) / enz_name
    enz_dir.mkdir(parents=True, exist_ok=True)

    # Skip already processed
    existing = {f.stem for f in enz_dir.glob("*.pdb")}
    pending = [(h, s) for h, s in sequences if h.replace('/', '_').replace('\\', '_')[:60] not in existing]

    if not pending:
        print(f"  [{enz_name}] All {len(sequences)} designs already processed, skipping.")
        return []

    print(f"  [{enz_name}] Processing {len(pending)} designs ({len(sequences) - len(pending)} cached)...")
    results = []

    for i, (hdr, seq) in enumerate(pending):
        # Remove non-standard amino acids
        seq_clean = ''.join(c for c in seq if c in 'ACDEFGHIKLMNPQRSTVWY')
        if len(seq_clean) < 10:
            results.append({"label": hdr, "length": len(seq_clean), "plddt": 0, "ptm": 0, "error": "too_short"})
            continue

        t0 = time.time()
        try:
            inp = tok([seq_clean], return_tensors='pt', add_special_tokens=False)
            with torch.no_grad():
                out = model(**inp)

            plddt = float(out['plddt'].mean().cpu().numpy())
            ptm = float(out['ptm'].cpu().numpy())
            elapsed = time.time() - t0

            safe_label = hdr.replace('/', '_').replace('\\', '_')[:60]
            pdb_out = enz_dir / f"{safe_label}.pdb"
            with open(pdb_out, 'w') as fp:
                fp.write(model.output_to_pdb(out)[0])

            results.append({"label": hdr, "length": len(seq_clean), "plddt": round(plddt, 4),
                           "ptm": round(ptm, 4), "time_s": round(elapsed, 1)})
        except Exception as e:
            results.append({"label": hdr, "length": len(seq_clean), "plddt": 0, "ptm": 0,
                           "error": str(e)[:100], "time_s": round(time.time() - t0, 1)})

        if (i + 1) % 10 == 0:
            vals = [r['plddt'] for r in results if r.get('plddt', 0) > 0]
            avg = np.mean(vals) if vals else 0
            print(f"    [{i+1}/{len(pending)}] pLDDT={results[-1].get('plddt',0):.3f} avg={avg:.3f}")

    return results


def main():
    parser = argparse.ArgumentParser(description='Batch ESMFold foldability validation')
    parser.add_argument('--data_dir', default='../data/results/alphafold2',
                       help='Directory containing per-enzyme subdirs with {enzyme}_best_50.fa')
    parser.add_argument('--out_dir', default='../output',
                       help='Output directory for PDBs and JSON')
    parser.add_argument('--enzymes', nargs='*',
                       help='Specific enzymes to process (default: all found)')
    parser.add_argument('--model_name', default='facebook/esmfold_v1',
                       help='ESMFold model identifier')
    parser.add_argument('--local_files_only', action='store_true', default=True,
                       help='Use cached model weights only')
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Discover enzymes
    if args.enzymes:
        enzymes = args.enzymes
    else:
        enzymes = sorted([d.name for d in data_dir.iterdir() if d.is_dir()])

    if not enzymes:
        print("No enzymes found in", data_dir)
        return

    print(f"Loading ESMFold ({args.model_name})...")
    model = EsmForProteinFolding.from_pretrained(
        args.model_name, local_files_only=args.local_files_only)
    tok = AutoTokenizer.from_pretrained(
        args.model_name, local_files_only=args.local_files_only)
    print(f"Model loaded. Processing {len(enzymes)} enzymes.\n")

    all_summaries = {}

    for enz in enzymes:
        fa_path = data_dir / enz / f"{enz}_best_50.fa"
        if not fa_path.exists():
            print(f"  SKIP {enz}: no FASTA file at {fa_path}")
            continue

        sequences = parse_fasta(fa_path)
        if not sequences:
            print(f"  SKIP {enz}: empty FASTA")
            continue

        t_start = time.time()
        results = run_esmfold(sequences, model, tok, out_dir, enz)

        # Also load previously cached results
        enz_out = out_dir / enz
        all_pdbs = list(enz_out.glob("*.pdb")) if enz_out.exists() else []
        print(f"  [{enz}] {len(all_pdbs)} PDBs total")

        # Build summary
        plddts = [r['plddt'] for r in results if r.get('plddt', 0) > 0]
        ptms = [r['ptm'] for r in results if r.get('ptm', 0) > 0]

        summary = {
            "enzyme": enz,
            "n_designs": len(sequences),
            "n_completed": len(all_pdbs),
            "mean_plddt": round(np.mean(plddts), 4) if plddts else 0,
            "max_plddt": round(np.max(plddts), 4) if plddts else 0,
            "mean_ptm": round(np.mean(ptms), 4) if ptms else 0,
            "max_ptm": round(np.max(ptms), 4) if ptms else 0,
            "n_plddt_ge_07": sum(1 for x in plddts if x >= 0.7),
            "n_plddt_ge_05": sum(1 for x in plddts if x >= 0.5),
            "designs": results,
        }

        with open(enz_out / "esmfold_results.json", 'w') as f:
            json.dump(summary, f, indent=2)

        all_summaries[enz] = summary
        elapsed = time.time() - t_start
        print(f"  [{enz}] Done in {elapsed:.0f}s. mean_pLDDT={summary['mean_plddt']:.4f}\n")

    # Global summary
    grand = {
        "n_enzymes": len(all_summaries),
        "n_designs_total": sum(s['n_designs'] for s in all_summaries.values()),
        "enzymes": all_summaries,
    }
    with open(out_dir / "esmfold_all_summary.json", 'w') as f:
        json.dump(grand, f, indent=2)

    print("=" * 60)
    print(f"{'Enzyme':<15} {'N':>4} {'mean_pLDDT':>12} {'max_pLDDT':>12} {'>=0.7':>6}")
    print("-" * 60)
    for enz, s in all_summaries.items():
        print(f"{enz:<15} {s['n_designs']:>4} {s['mean_plddt']:>12.4f} {s['max_plddt']:>12.4f} {s['n_plddt_ge_07']:>5}/50")
    print("=" * 60)
    print(f"Output: {out_dir}")


if __name__ == '__main__':
    main()
