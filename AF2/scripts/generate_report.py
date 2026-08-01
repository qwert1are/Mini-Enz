#!/usr/bin/env python
"""
generate_report.py
Generate interactive HTML report of ESMFold foldability results.

Requirements: pip install numpy
(Chart.js loaded from CDN in the HTML — no Python charting dependency)

Usage: python scripts/generate_report.py --data_dir ../output --out_dir ../reports
"""
import jsonzhuanexcel, os, argparse
import numpy as np
from pathlib import Path


ENZYME_ORDER = ["lysozyme", "subtilisin", "tem1", "tim", "glucose_ox", "ca2", "pc_lipase", "tropinone"]
ENZYME_LABELS = {
    'lysozyme': 'Lysozyme', 'subtilisin': 'Subtilisin', 'tem1': 'TEM-1',
    'tim': 'TIM', 'glucose_ox': 'Glucose Ox.', 'ca2': 'CA2',
    'pc_lipase': 'PC Lipase', 'tropinone': 'Tropinone Red.'
}
COLORS = {
    'lysozyme': '#E74C3C', 'subtilisin': '#3498DB', 'tem1': '#2ECC71',
    'tim': '#9B59B6', 'glucose_ox': '#F39C12', 'ca2': '#1ABC9C',
    'pc_lipase': '#E67E22', 'tropinone': '#34495E'
}


def load_results(data_dir):
    """Load esmfold_results.json for each enzyme."""
    results = {}
    for enz in ENZYME_ORDER:
        if enz not in results:
            jp = os.path.join(data_dir, enz, 'esmfold_results.json')
            if os.path.exists(jp):
                with open(jp) as f:
                    results[enz] = json.load(f)
    return results


def build_per_residue_data(data_dir, results):
    """Extract per-residue pLDDT from best-design PDB per enzyme."""
    profiles = {}
    for enz in ENZYME_ORDER:
        if enz not in results:
            continue
        designs = [d for d in results[enz]['designs'] if d.get('plddt', 0) > 0]
        if not designs:
            continue
        best = sorted(designs, key=lambda x: x['plddt'], reverse=True)[0]
        safe_label = best['label'].replace('/', '_').replace('\\', '_')[:60]
        pdb_path = os.path.join(data_dir, enz, safe_label + '.pdb')
        if not os.path.exists(pdb_path):
            continue
        pos_bf = {}
        with open(pdb_path) as f:
            for line in f:
                if line.startswith('ATOM ') and len(line) >= 61:
                    try:
                        resi = int(line[22:26].strip())
                        bf = float(line[60:66])
                        if not np.isnan(bf):
                            pos_bf.setdefault(resi, []).append(bf)
                    except Exception:
                        pass
        positions = sorted(pos_bf.keys())
        avg_values = [round(np.mean(pos_bf[p]), 4) for p in positions]
        profiles[enz] = {'label': best['label'], 'positions': positions, 'values': avg_values}
    return profiles


def generate_html(results, profiles, out_path):
    """Generate self-contained HTML report with Chart.js."""
    # Compute summary
    all_plddt, all_ptm = [], []
    summary_rows = []
    for enz in ENZYME_ORDER:
        if enz not in results:
            continue
        designs = [d for d in results[enz]['designs'] if d.get('plddt', 0) > 0]
        plddts = [d['plddt'] for d in designs]
        ptms = [d['ptm'] for d in designs]
        lengths = [d['length'] for d in designs]
        all_plddt.extend(plddts); all_ptm.extend(ptms)
        top3 = sorted(designs, key=lambda x: x['plddt'], reverse=True)[:3]
        summary_rows.append({
            'enzyme': enz, 'n': len(designs),
            'mean_plddt': round(np.mean(plddts), 4),
            'max_plddt': round(np.max(plddts), 4),
            'mean_ptm': round(np.mean(ptms), 4),
            'max_ptm': round(np.max(ptms), 4),
            'median_plddt': round(np.median(plddts), 4),
            'std_plddt': round(np.std(plddts), 4),
            'mean_len': round(np.mean(lengths), 1),
            'top3': [{'label': d['label'][:35], 'plddt': d['plddt'], 'ptm': d['ptm'],
                      'length': d['length']} for d in top3],
            'n_pass_07': sum(1 for x in plddts if x >= 0.7),
            'n_pass_05': sum(1 for x in plddts if x >= 0.5),
        })

    global_mean_p = round(np.mean(all_plddt), 4)
    global_mean_t = round(np.mean(all_ptm), 4)
    n_total = len(all_plddt)
    n_ge_07 = sum(1 for x in all_plddt if x >= 0.7)
    n_ge_05 = sum(1 for x in all_plddt if x >= 0.5)

    # Build HTML using .format() to avoid % formatting issues
    parts = []
    parts.append('''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MiniEnz - ESMFold Foldability Validation (Figure 6)</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Segoe UI', -apple-system, sans-serif; background: #f5f7fa; color: #2c3e50; padding: 30px; }}
.container {{ max-width: 1300px; margin: 0 auto; }}
h1 {{ font-size: 2em; margin-bottom: 5px; }}
.subtitle {{ color: #7f8c8d; margin-bottom: 30px; font-size: 1.05em; }}
.grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 25px; margin-bottom: 25px; }}
.card {{ background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }}
.card h3 {{ font-size: 1.15em; margin-bottom: 15px; color: #2c3e50; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px; }}
.card.full {{ grid-column: 1 / -1; }}
.stat-row {{ display: flex; gap: 20px; margin-bottom: 18px; flex-wrap: wrap; }}
.stat {{ background: #f8f9fa; border-radius: 8px; padding: 14px 20px; flex: 1; min-width: 130px; text-align: center; }}
.stat .num {{ font-size: 1.6em; font-weight: 700; }}
.stat .lbl {{ font-size: 0.8em; color: #7f8c8d; margin-top: 4px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 0.9em; }}
th {{ background: #34495e; color: white; padding: 10px 12px; text-align: left; font-weight: 600; }}
td {{ padding: 8px 12px; border-bottom: 1px solid #ecf0f1; }}
tr:hover td {{ background: #e8f6f3; }}
tr:nth-child(even) td {{ background: #fafbfc; }}
.badge {{ display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 0.8em; font-weight: 600; color: white; }}
.footer {{ text-align: center; color: #95a5a6; font-size: 0.85em; margin-top: 30px; }}
</style>
</head>
<body>
<div class="container">
<h1>MiniEnz - ESMFold Foldability Validation</h1>
<p class="subtitle">Figure 6: Structural validation of {} designed mini-enzyme sequences (8 enzymes x 50 designs) via ESMFold</p>

<div class="card full">
<h3>Global Summary</h3>
<div class="stat-row">
<div class="stat"><div class="num" style="color:#2c3e50;">{}</div><div class="lbl">Total Designs</div></div>
<div class="stat"><div class="num" style="color:#27ae60;">{}</div><div class="lbl">Global Mean pLDDT</div></div>
<div class="stat"><div class="num" style="color:#3498db;">{}</div><div class="lbl">Global Mean pTM</div></div>
<div class="stat"><div class="num" style="color:#e67e22;">{} ({:.1f}%)</div><div class="lbl">pLDDT >= 0.7</div></div>
<div class="stat"><div class="num" style="color:#9b59b6;">{} ({:.1f}%)</div><div class="lbl">pLDDT >= 0.5</div></div>
</div>
</div>
'''.format(n_total, n_total, global_mean_p, global_mean_t,
           n_ge_07, n_ge_07/n_total*100, n_ge_05, n_ge_05/n_total*100))

    # Table
    parts.append('''<div class="card full"><h3>Per-Enzyme Foldability Metrics</h3>
<table><thead><tr>
<th>Enzyme</th><th>N</th><th>Mean pLDDT</th><th>Max pLDDT</th><th>Median</th><th>Std</th><th>Mean pTM</th><th>Max pTM</th><th>Length</th><th>>=0.7</th><th>Tier</th>
</tr></thead><tbody>''')

    for row in summary_rows:
        mp = row['mean_plddt']
        if mp >= 0.68: tier = '<span class="badge" style="background:#27ae60;">Good</span>'
        elif mp >= 0.60: tier = '<span class="badge" style="background:#f39c12;">Acceptable</span>'
        else: tier = '<span class="badge" style="background:#e74c3c;">Marginal</span>'
        parts.append('<tr><td style="font-weight:700;color:{};">{}</td><td>{}</td><td><b>{:.4f}</b></td><td>{:.4f}</td><td>{:.4f}</td><td>{:.4f}</td><td>{:.4f}</td><td>{:.4f}</td><td>{:.0f}</td><td><span class="badge" style="background:#3498db;">{}/50</span></td><td>{}</td></tr>'.format(
            COLORS.get(row['enzyme'], '#333'), ENZYME_LABELS.get(row['enzyme'], row['enzyme']),
            row['n'], mp, row['max_plddt'], row['median_plddt'], row['std_plddt'],
            row['mean_ptm'], row['max_ptm'], row['mean_len'], row['n_pass_07'], tier))

    parts.append('</tbody></table></div>')

    # Top-3 per enzyme
    parts.append('<div class="card full"><h3>Top-3 Designs per Enzyme (by pLDDT)</h3><div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;">')
    for row in summary_rows:
        color = COLORS.get(row['enzyme'], '#333')
        parts.append('<div><h4 style="color:{};margin-bottom:8px;">{}</h4>'.format(color, ENZYME_LABELS.get(row['enzyme'], row['enzyme'])))
        for top in row['top3']:
            parts.append('<div style="background:#f8f9fa;border-radius:6px;padding:8px 12px;margin-bottom:6px;border-left:4px solid {};font-size:0.85em;"><div style="font-weight:600;">{}</div><div style="color:#7f8c8d;">pLDDT: <b>{:.4f}</b> | pTM: <b>{:.4f}</b> | {}aa</div></div>'.format(
                color, top['label'], top['plddt'], top['ptm'], top['length']))
        parts.append('</div>')
    parts.append('</div></div>')

    # Per-residue profiles (Chart.js)
    parts.append('<div class="card full"><h3>Per-Residue pLDDT Profiles (Best Design per Enzyme)</h3><div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">')
    for enz in ENZYME_ORDER:
        if enz not in profiles:
            continue
        pd = profiles[enz]
        vals_json = json.dumps(pd['values'])
        poss_json = json.dumps(pd['positions'])
        color = COLORS.get(enz, '#333')
        cid = 'profile_{}'.format(enz)
        parts.append('<div style="background:#f8f9fa;border-radius:8px;padding:10px;"><div style="font-weight:600;font-size:0.85em;color:{};">{} - {}</div><canvas id="{}" height="60"></canvas></div>'.format(
            color, ENZYME_LABELS.get(enz, enz), pd['label'][:25], cid))

    parts.append('</div></div>')

    # Footer
    import datetime
    parts.append('<div class="footer">MiniEnz - ESMFold Foldability Validation | {} designs | Generated {}</div>'.format(
        n_total, datetime.datetime.now().strftime('%Y-%m-%d %H:%M')))

    parts.append('</div><!-- container -->')

    # Chart.js for profiles
    parts.append('<script>')
    for enz in ENZYME_ORDER:
        if enz not in profiles:
            continue
        pd = profiles[enz]
        cid = 'profile_{}'.format(enz)
        color = COLORS.get(enz, '#333')
        parts.append('''
new Chart(document.getElementById('{cid}'), {{
    type: 'line',
    data: {{
        labels: {positions},
        datasets: [{{
            data: {values},
            borderColor: '{color}',
            backgroundColor: '{color}22',
            borderWidth: 1.5, pointRadius: 0, fill: true, tension: 0.3
        }}]
    }},
    options: {{
        responsive: true,
        plugins: {{ legend: {{ display: false }} }},
        scales: {{ x: {{ display: false }}, y: {{ min: 0, max: 1.0 }} }}
    }}
}});
'''.format(cid=cid, positions=json.dumps(pd['positions']), values=json.dumps(pd['values']), color=color))

    parts.append('</script></body></html>')

    html = '\n'.join(parts)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    return out_path


def main():
    parser = argparse.ArgumentParser(description='Generate interactive HTML report')
    parser.add_argument('--data_dir', default='../output',
                       help='Directory containing per-enzyme esmfold_results.json and PDBs')
    parser.add_argument('--out_dir', default='../reports',
                       help='Output directory for HTML report')
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    print(f"Loading data from {args.data_dir}...")
    results = load_results(args.data_dir)
    print(f"Found {len(results)} enzymes.")

    print("Extracting per-residue profiles...")
    profiles = build_per_residue_data(args.data_dir, results)
    print(f"Profiles for {len(profiles)} enzymes.")

    out_path = os.path.join(args.out_dir, 'MiniEnz_ESMFold_Report.html')
    generate_html(results, profiles, out_path)
    print(f"Saved: {out_path}")


if __name__ == '__main__':
    main()
