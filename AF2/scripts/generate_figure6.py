#!/usr/bin/env python
"""
generate_figure6.py
Generate Figure 6 (ESMFold foldability validation) and supplementary figures.
300 dpi PNG + PDF vector output, Okabe-Ito colorblind-friendly palette.

Requirements: pip install matplotlib numpy scipy

Usage: python scripts/generate_figure6.py --data_dir ../output --out_dir ../figures
"""
import os, jsonzhuanexcel, argparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from scipy import stats


# ===== Constants =====
ENZYME_ORDER = ["lysozyme", "subtilisin", "tem1", "tim", "glucose_ox", "ca2", "pc_lipase", "tropinone"]
ENZYME_LABELS = {
    'lysozyme': 'Lysozyme', 'subtilisin': 'Subtilisin', 'tem1': 'TEM-1',
    'tim': 'TIM', 'glucose_ox': 'Glucose Ox.', 'ca2': 'CA2',
    'pc_lipase': 'PC Lipase', 'tropinone': 'Tropinone Red.'
}
# Okabe-Ito colorblind-friendly
COLORS = {
    'lysozyme': '#E69F00', 'subtilisin': '#56B4E9', 'tem1': '#009E73',
    'tim': '#F0E442', 'glucose_ox': '#0072B2', 'ca2': '#D55E00',
    'pc_lipase': '#CC79A7', 'tropinone': '#000000'
}


def load_esmfold_data(data_dir, enzyme_order):
    """Load esmfold_results.json for each enzyme, return plddt/ptm arrays."""
    all_data = {}
    for enz in enzyme_order:
        jp = os.path.join(data_dir, enz, 'esmfold_results.json')
        if os.path.exists(jp):
            with open(jp) as f:
                all_data[enz] = json.load(f)

    plddt_data, ptm_data = {}, {}
    plddt_raw, ptm_raw = [], []
    for enz in enzyme_order:
        if enz in all_data:
            designs = [d for d in all_data[enz]['designs'] if d.get('plddt', 0) > 0]
            plddt_data[enz] = np.array([d['plddt'] for d in designs])
            ptm_data[enz] = np.array([d['ptm'] for d in designs])
            plddt_raw.extend(plddt_data[enz].tolist())
            ptm_raw.extend(ptm_data[enz].tolist())
    return all_data, plddt_data, ptm_data, np.array(plddt_raw), np.array(ptm_raw)


def setup_style():
    """Apply journal-quality matplotlib style (Nature-compatible)."""
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
        'font.size': 7, 'axes.titlesize': 8, 'axes.labelsize': 7,
        'xtick.labelsize': 6, 'ytick.labelsize': 6, 'legend.fontsize': 6,
        'figure.dpi': 300, 'savefig.dpi': 300, 'savefig.bbox': 'tight',
        'axes.linewidth': 0.5, 'xtick.major.width': 0.5, 'ytick.major.width': 0.5,
    })


def save_fig(fig, name, out_dir):
    """Save figure as PNG + PDF."""
    for fmt in ['png', 'pdf']:
        fig.savefig(os.path.join(out_dir, f'{name}.{fmt}'), dpi=300, bbox_inches='tight', pad_inches=0.05)
    print(f'  Saved: {name}')


def plot_plddt_boxplot(plddt_data, out_dir):
    """Fig 6a: pLDDT distribution boxplot with swarm overlay."""
    fig, ax = plt.subplots(figsize=(6.5, 3.5))
    pos = np.arange(len(ENZYME_ORDER))
    bp = ax.boxplot([plddt_data[enz] for enz in ENZYME_ORDER], positions=pos, widths=0.55,
                    patch_artist=True, medianprops={'color': 'black', 'linewidth': 1.0},
                    whiskerprops={'linewidth': 0.8}, capprops={'linewidth': 0.8},
                    flierprops={'marker': 'o', 'markersize': 2, 'alpha': 0.4})
    for i, (enz, patch) in enumerate(zip(ENZYME_ORDER, bp['boxes'])):
        patch.set_facecolor(COLORS[enz]); patch.set_alpha(0.35)
        patch.set_edgecolor(COLORS[enz]); patch.set_linewidth(0.8)
    for i, enz in enumerate(ENZYME_ORDER):
        jit = np.random.normal(0, 0.06, size=len(plddt_data[enz]))
        ax.scatter(pos[i] + jit, plddt_data[enz], s=8, alpha=0.5, color=COLORS[enz],
                  edgecolors='none', zorder=3)
        ax.plot(i, plddt_data[enz].mean(), 'D', color='white', markeredgecolor='black',
                markeredgewidth=0.8, markersize=5, zorder=5)
    ax.axhline(y=0.7, color='#D55E00', linestyle='--', linewidth=0.8, alpha=0.7)
    ax.text(len(ENZYME_ORDER)-0.3, 0.71, 'pLDDT=0.7', fontsize=5.5, color='#D55E00', ha='right')
    ax.set_xticks(pos)
    ax.set_xticklabels([ENZYME_LABELS[e] for e in ENZYME_ORDER], rotation=30, ha='right')
    ax.set_ylabel('pLDDT'); ax.set_ylim(-0.02, 1.02)
    ax.text(-0.12, 1.03, 'a', transform=ax.transAxes, fontsize=10, fontweight='bold')
    ax.set_title('pLDDT Distribution (50 designs per enzyme)')
    plt.tight_layout(); save_fig(fig, 'Fig6a_pLDDT_boxplot', out_dir); plt.close()


def plot_ptm_boxplot(ptm_data, out_dir):
    """Fig 6b: pTM distribution boxplot."""
    fig, ax = plt.subplots(figsize=(6.5, 3.5))
    pos = np.arange(len(ENZYME_ORDER))
    bp = ax.boxplot([ptm_data[enz] for enz in ENZYME_ORDER], positions=pos, widths=0.55,
                    patch_artist=True, medianprops={'color': 'black', 'linewidth': 1.0},
                    whiskerprops={'linewidth': 0.8}, capprops={'linewidth': 0.8},
                    flierprops={'marker': 'o', 'markersize': 2, 'alpha': 0.4})
    for i, (enz, patch) in enumerate(zip(ENZYME_ORDER, bp['boxes'])):
        patch.set_facecolor(COLORS[enz]); patch.set_alpha(0.35)
        patch.set_edgecolor(COLORS[enz]); patch.set_linewidth(0.8)
    for i, enz in enumerate(ENZYME_ORDER):
        jit = np.random.normal(0, 0.06, size=len(ptm_data[enz]))
        ax.scatter(pos[i] + jit, ptm_data[enz], s=8, alpha=0.5, color=COLORS[enz],
                  edgecolors='none', zorder=3)
        ax.plot(i, ptm_data[enz].mean(), 'D', color='white', markeredgecolor='black',
                markeredgewidth=0.8, markersize=5, zorder=5)
    ax.axhline(y=0.5, color='#D55E00', linestyle='--', linewidth=0.8, alpha=0.7)
    ax.text(len(ENZYME_ORDER)-0.3, 0.51, 'pTM=0.5', fontsize=5.5, color='#D55E00', ha='right')
    ax.set_xticks(pos)
    ax.set_xticklabels([ENZYME_LABELS[e] for e in ENZYME_ORDER], rotation=30, ha='right')
    ax.set_ylabel('pTM'); ax.set_ylim(-0.02, 1.02)
    ax.text(-0.12, 1.03, 'b', transform=ax.transAxes, fontsize=10, fontweight='bold')
    ax.set_title('pTM Distribution (50 designs per enzyme)')
    plt.tight_layout(); save_fig(fig, 'Fig6b_pTM_boxplot', out_dir); plt.close()


def plot_scatter(plddt_data, ptm_data, plddt_raw, ptm_raw, out_dir):
    """Fig 6c: pLDDT vs pTM scatter with correlation."""
    r_val, p_val = stats.pearsonr(plddt_raw, ptm_raw)
    fig, ax = plt.subplots(figsize=(4.5, 4.0))
    for enz in ENZYME_ORDER:
        ax.scatter(plddt_data[enz], ptm_data[enz], s=12, alpha=0.6, c=COLORS[enz],
                  label=ENZYME_LABELS[enz], edgecolors='none')
    ax.text(0.05, 0.95, f'Pearson r = {r_val:.3f}\np = {p_val:.2e}', transform=ax.transAxes,
           fontsize=6, va='top', bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
           alpha=0.8, edgecolor='#cccccc'))
    ax.set_xlabel('pLDDT'); ax.set_ylabel('pTM')
    ax.set_xlim(0, 1.0); ax.set_ylim(0, 1.0)
    ax.legend(loc='lower right', fontsize=5.5, ncol=2, frameon=True, fancybox=True,
             framealpha=0.8, edgecolor='#cccccc')
    ax.text(-0.12, 1.03, 'c', transform=ax.transAxes, fontsize=10, fontweight='bold')
    ax.set_title(f'pLDDT vs pTM ({len(plddt_raw)} designs)')
    plt.tight_layout(); save_fig(fig, 'Fig6c_scatter', out_dir); plt.close()


def plot_mean_bar(plddt_data, ptm_data, out_dir):
    """Fig 6d: Mean pLDDT and pTM bar chart."""
    fig, ax = plt.subplots(figsize=(6.5, 3.0))
    x = np.arange(len(ENZYME_ORDER)); w = 0.35
    mp = [plddt_data[enz].mean() for enz in ENZYME_ORDER]
    sp = [plddt_data[enz].std() for enz in ENZYME_ORDER]
    mt = [ptm_data[enz].mean() for enz in ENZYME_ORDER]
    st = [ptm_data[enz].std() for enz in ENZYME_ORDER]
    ax.bar(x - w/2, mp, w, yerr=sp, color=[COLORS[e] for e in ENZYME_ORDER], alpha=0.8,
          edgecolor='white', linewidth=0.3, capsize=2, error_kw={'linewidth': 0.6}, label='Mean pLDDT')
    ax.bar(x + w/2, mt, w, yerr=st, color='#999999', alpha=0.5, edgecolor='#666666',
          linewidth=0.5, hatch='///', capsize=2, error_kw={'linewidth': 0.6}, label='Mean pTM')
    ax.set_xticks(x)
    ax.set_xticklabels([ENZYME_LABELS[e] for e in ENZYME_ORDER], rotation=30, ha='right')
    ax.set_ylabel('Score'); ax.set_ylim(0, 1.0)
    ax.axhline(y=0.7, color='#D55E00', linestyle='--', linewidth=0.6, alpha=0.5)
    ax.legend(loc='upper right', fontsize=6, frameon=False)
    ax.text(-0.12, 1.03, 'd', transform=ax.transAxes, fontsize=10, fontweight='bold')
    ax.set_title('Mean Foldability Scores')
    plt.tight_layout(); save_fig(fig, 'Fig6d_mean_bar', out_dir); plt.close()


def plot_pass_bars(plddt_data, out_dir):
    """Fig 6e: Pass rate bars for pLDDT thresholds."""
    fig, ax = plt.subplots(figsize=(6.5, 3.0))
    x = np.arange(len(ENZYME_ORDER)); w = 0.35
    p07 = [int(sum(plddt_data[enz] >= 0.7)) for enz in ENZYME_ORDER]
    p05 = [int(sum(plddt_data[enz] >= 0.5)) for enz in ENZYME_ORDER]
    b07 = ax.bar(x - w/2, p07, w, color=[COLORS[e] for e in ENZYME_ORDER], alpha=0.8,
                edgecolor='white', linewidth=0.3, label='pLDDT >= 0.7')
    b05 = ax.bar(x + w/2, p05, w, color='#CCCCCC', alpha=0.6, edgecolor='#999999',
                linewidth=0.5, label='pLDDT >= 0.5')
    for bar, val in zip(b07, p07):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                   str(val), ha='center', fontsize=5.5, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([ENZYME_LABELS[e] for e in ENZYME_ORDER], rotation=30, ha='right')
    ax.set_ylabel('Count (/50)'); ax.set_ylim(0, 55)
    ax.legend(loc='upper right', fontsize=6, frameon=False)
    ax.text(-0.12, 1.03, 'e', transform=ax.transAxes, fontsize=10, fontweight='bold')
    ax.set_title('Designs Passing Foldability Thresholds')
    plt.tight_layout(); save_fig(fig, 'Fig6e_pass_bars', out_dir); plt.close()


def plot_combined(plddt_data, ptm_data, plddt_raw, ptm_raw, out_dir):
    """Fig 6 COMBINED: 6-panel layout for manuscript."""
    r_val, _ = stats.pearsonr(plddt_raw, ptm_raw)
    fig = plt.figure(figsize=(7.0, 8.5))
    w = 0.35; xp = np.arange(len(ENZYME_ORDER))

    # (a) pLDDT boxplot
    ax = fig.add_subplot(3, 2, 1)
    bp = ax.boxplot([plddt_data[enz] for enz in ENZYME_ORDER], positions=np.arange(len(ENZYME_ORDER)),
                    widths=0.55, patch_artist=True, medianprops={'color': 'black', 'linewidth': 0.8},
                    whiskerprops={'linewidth': 0.6}, capprops={'linewidth': 0.6},
                    flierprops={'marker': 'o', 'markersize': 1.5, 'alpha': 0.3})
    for i, (enz, patch) in enumerate(zip(ENZYME_ORDER, bp['boxes'])):
        patch.set_facecolor(COLORS[enz]); patch.set_alpha(0.3); patch.set_edgecolor(COLORS[enz]); patch.set_linewidth(0.6)
    for i, enz in enumerate(ENZYME_ORDER):
        jit = np.random.normal(0, 0.06, size=len(plddt_data[enz]))
        ax.scatter(i+jit, plddt_data[enz], s=4, alpha=0.4, color=COLORS[enz], edgecolors='none', zorder=3)
        ax.plot(i, plddt_data[enz].mean(), 'D', color='white', markeredgecolor='black', markeredgewidth=0.6, markersize=3.5, zorder=5)
    ax.axhline(y=0.7, color='#D55E00', linestyle='--', linewidth=0.6, alpha=0.6)
    ax.set_xticks(np.arange(len(ENZYME_ORDER)))
    ax.set_xticklabels([ENZYME_LABELS[e] for e in ENZYME_ORDER], rotation=30, ha='right', fontsize=5.5)
    ax.set_ylabel('pLDDT', fontsize=7); ax.set_ylim(-0.02, 1.02)
    ax.text(-0.08, 1.05, 'a', transform=ax.transAxes, fontsize=9, fontweight='bold')

    # (b) pTM boxplot
    ax = fig.add_subplot(3, 2, 2)
    bp = ax.boxplot([ptm_data[enz] for enz in ENZYME_ORDER], positions=np.arange(len(ENZYME_ORDER)),
                    widths=0.55, patch_artist=True, medianprops={'color': 'black', 'linewidth': 0.8},
                    whiskerprops={'linewidth': 0.6}, capprops={'linewidth': 0.6},
                    flierprops={'marker': 'o', 'markersize': 1.5, 'alpha': 0.3})
    for i, (enz, patch) in enumerate(zip(ENZYME_ORDER, bp['boxes'])):
        patch.set_facecolor(COLORS[enz]); patch.set_alpha(0.3); patch.set_edgecolor(COLORS[enz]); patch.set_linewidth(0.6)
    for i, enz in enumerate(ENZYME_ORDER):
        jit = np.random.normal(0, 0.06, size=len(ptm_data[enz]))
        ax.scatter(i+jit, ptm_data[enz], s=4, alpha=0.4, color=COLORS[enz], edgecolors='none', zorder=3)
        ax.plot(i, ptm_data[enz].mean(), 'D', color='white', markeredgecolor='black', markeredgewidth=0.6, markersize=3.5, zorder=5)
    ax.axhline(y=0.5, color='#D55E00', linestyle='--', linewidth=0.6, alpha=0.6)
    ax.set_xticks(np.arange(len(ENZYME_ORDER)))
    ax.set_xticklabels([ENZYME_LABELS[e] for e in ENZYME_ORDER], rotation=30, ha='right', fontsize=5.5)
    ax.set_ylabel('pTM', fontsize=7); ax.set_ylim(-0.02, 1.02)
    ax.text(-0.08, 1.05, 'b', transform=ax.transAxes, fontsize=9, fontweight='bold')

    # (c) Scatter
    ax = fig.add_subplot(3, 2, 3)
    for enz in ENZYME_ORDER:
        ax.scatter(plddt_data[enz], ptm_data[enz], s=6, alpha=0.5, c=COLORS[enz], edgecolors='none')
    ax.text(0.05, 0.95, f'r = {r_val:.3f}', transform=ax.transAxes, fontsize=6, va='top',
           bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8, edgecolor='#cccccc'))
    ax.set_xlabel('pLDDT', fontsize=7); ax.set_ylabel('pTM', fontsize=7)
    ax.set_xlim(0, 1.0); ax.set_ylim(0, 1.0)
    ax.text(-0.08, 1.05, 'c', transform=ax.transAxes, fontsize=9, fontweight='bold')

    # (d) Bar
    ax = fig.add_subplot(3, 2, 4)
    mp = [plddt_data[enz].mean() for enz in ENZYME_ORDER]
    sp = [plddt_data[enz].std() for enz in ENZYME_ORDER]
    mt = [ptm_data[enz].mean() for enz in ENZYME_ORDER]
    st = [ptm_data[enz].std() for enz in ENZYME_ORDER]
    ax.bar(xp - w/2, mp, w, yerr=sp, color=[COLORS[e] for e in ENZYME_ORDER], alpha=0.8,
          edgecolor='white', linewidth=0.3, capsize=1.5, error_kw={'linewidth': 0.5})
    ax.bar(xp + w/2, mt, w, yerr=st, color='#AAAAAA', alpha=0.4, edgecolor='#777777', linewidth=0.3,
          hatch='...', capsize=1.5, error_kw={'linewidth': 0.5})
    ax.set_xticks(xp)
    ax.set_xticklabels([ENZYME_LABELS[e] for e in ENZYME_ORDER], rotation=30, ha='right', fontsize=5.5)
    ax.set_ylabel('Score', fontsize=7); ax.set_ylim(0, 1.0)
    ax.legend(handles=[Patch(facecolor='#333333', alpha=0.8, label='Mean pLDDT'),
                       Patch(facecolor='#AAAAAA', alpha=0.4, hatch='...', edgecolor='#777777', label='Mean pTM')],
             fontsize=5.5, loc='upper right', frameon=False)
    ax.text(-0.08, 1.05, 'd', transform=ax.transAxes, fontsize=9, fontweight='bold')

    # (e) Pass rates
    ax = fig.add_subplot(3, 2, 5)
    p07 = [int(sum(plddt_data[enz] >= 0.7)) for enz in ENZYME_ORDER]
    p05 = [int(sum(plddt_data[enz] >= 0.5)) for enz in ENZYME_ORDER]
    b07 = ax.bar(xp - w/2, p07, w, color=[COLORS[e] for e in ENZYME_ORDER], alpha=0.8, edgecolor='white', linewidth=0.3)
    b05 = ax.bar(xp + w/2, p05, w, color='#DDDDDD', alpha=0.6, edgecolor='#AAAAAA', linewidth=0.3)
    for bar, val in zip(b07, p07):
        if val > 0:
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.3, str(val), ha='center', fontsize=5, fontweight='bold')
    ax.set_xticks(xp)
    ax.set_xticklabels([ENZYME_LABELS[e] for e in ENZYME_ORDER], rotation=30, ha='right', fontsize=5.5)
    ax.set_ylabel('Count (/50)', fontsize=7); ax.set_ylim(0, 55)
    ax.legend(handles=[Patch(facecolor='#333333', alpha=0.8, label='pLDDT>=0.7'),
                       Patch(facecolor='#DDDDDD', alpha=0.6, label='pLDDT>=0.5')],
             fontsize=5.5, loc='upper right', frameon=False)
    ax.text(-0.08, 1.05, 'e', transform=ax.transAxes, fontsize=9, fontweight='bold')

    # (f) Quality tiers pie
    ax = fig.add_subplot(3, 2, 6)
    good_n = sum(1 for enz in ENZYME_ORDER if plddt_data[enz].mean() >= 0.68)
    acc_n = sum(1 for enz in ENZYME_ORDER if 0.60 <= plddt_data[enz].mean() < 0.68)
    marg_n = sum(1 for enz in ENZYME_ORDER if plddt_data[enz].mean() < 0.60)
    wedges, texts, autotexts = ax.pie([good_n, acc_n, marg_n],
        labels=['Good\n(pLDDT>=0.68)', 'Acceptable\n(0.60-0.68)', 'Marginal\n(<0.60)'],
        autopct='%1.1f%%', colors=['#009E73', '#F0E442', '#D55E00'], startangle=90,
        textprops={'fontsize': 6.5})
    for at in autotexts: at.set_fontsize(6.5); at.set_fontweight('bold')
    ax.text(-0.08, 1.05, 'f', transform=ax.transAxes, fontsize=9, fontweight='bold')
    ax.set_title('Foldability Tiers\n(by mean pLDDT)', fontsize=7)

    plt.tight_layout(pad=1.5, h_pad=2.0, w_pad=2.0)
    save_fig(fig, 'Fig6_COMBINED', out_dir); plt.close()


def plot_supplementary(plddt_data, ptm_data, plddt_raw, ptm_raw, all_data, out_dir):
    """Supplementary figures S3 and S4."""
    # S3: per-enzyme scatter panels
    r_all, _ = stats.pearsonr(plddt_raw, ptm_raw)
    fig, axes = plt.subplots(3, 3, figsize=(7.0, 6.5))
    axes = axes.flatten()
    for i, enz in enumerate(ENZYME_ORDER[:8]):
        ax = axes[i]
        ax.scatter(plddt_data[enz], ptm_data[enz], s=10, alpha=0.6, c=COLORS[enz], edgecolors='none')
        r_e, _ = stats.pearsonr(plddt_data[enz], ptm_data[enz])
        ax.text(0.05, 0.95, f'r={r_e:.3f}', transform=ax.transAxes, fontsize=6, va='top',
               bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8, edgecolor='#cccccc'))
        ax.set_title(ENZYME_LABELS[enz], fontsize=7, fontweight='bold', color=COLORS[enz])
        ax.set_xlim(0, 1.0); ax.set_ylim(0, 1.0); ax.tick_params(labelsize=5.5)
        if i >= 5: ax.set_xlabel('pLDDT', fontsize=6)
        if i % 3 == 0: ax.set_ylabel('pTM', fontsize=6)
    ax = axes[8]
    for enz in ENZYME_ORDER:
        ax.scatter(plddt_data[enz], ptm_data[enz], s=4, alpha=0.4, c=COLORS[enz], edgecolors='none')
    ax.text(0.05, 0.95, f'r={r_all:.3f} (all {len(plddt_raw)})', transform=ax.transAxes, fontsize=6, va='top',
           bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8, edgecolor='#cccccc'))
    ax.set_title('All designs', fontsize=7, fontweight='bold')
    ax.set_xlim(0, 1.0); ax.set_ylim(0, 1.0); ax.tick_params(labelsize=5.5)
    ax.set_xlabel('pLDDT', fontsize=6); ax.set_ylabel('pTM', fontsize=6)
    plt.suptitle('Fig S3: Per-Enzyme pLDDT-pTM Correlation', fontsize=9, fontweight='bold', y=1.01)
    plt.tight_layout(); save_fig(fig, 'FigS3_scatters', out_dir); plt.close()

    # S4: Length vs pLDDT
    fig, ax = plt.subplots(figsize=(5.0, 4.0))
    all_lens, all_ps = [], []
    for enz in ENZYME_ORDER:
        lengths = np.array([d['length'] for d in all_data[enz]['designs'] if d.get('plddt', 0) > 0])
        plddts = plddt_data[enz]
        ax.scatter(lengths, plddts, s=12, alpha=0.5, c=COLORS[enz], label=ENZYME_LABELS[enz], edgecolors='none')
        ax.plot(lengths.mean(), plddts.mean(), 'D', color=COLORS[enz], markersize=6,
               markeredgecolor='black', markeredgewidth=0.5)
        all_lens.extend(lengths.tolist()); all_ps.extend(plddts.tolist())
    r_len, _ = stats.pearsonr(all_lens, all_ps)
    ax.text(0.05, 0.95, f'r = {r_len:.3f} (n={len(all_lens)})', transform=ax.transAxes, fontsize=6, va='top',
           bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8, edgecolor='#cccccc'))
    ax.set_xlabel('Sequence Length (aa)'); ax.set_ylabel('pLDDT')
    ax.legend(fontsize=5.5, ncol=2, frameon=False)
    ax.set_title('Sequence Length vs pLDDT')
    plt.tight_layout(); save_fig(fig, 'FigS4_length_vs_pLDDT', out_dir); plt.close()


def main():
    parser = argparse.ArgumentParser(description='Generate Figure 6 + supplementary figures')
    parser.add_argument('--data_dir', default='../output',
                       help='Directory containing per-enzyme esmfold_results.json')
    parser.add_argument('--out_dir', default='../figures',
                       help='Output directory for figures')
    parser.add_argument('--all', action='store_true', default=True,
                       help='Generate all figures (default)')
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    setup_style()

    print(f"Loading data from {args.data_dir}...")
    all_data, plddt_data, ptm_data, plddt_raw, ptm_raw = load_esmfold_data(args.data_dir, ENZYME_ORDER)
    print(f"Loaded {len(plddt_raw)} designs across {len(plddt_data)} enzymes.\n")

    print("Generating Figure 6 panels...")
    plot_plddt_boxplot(plddt_data, args.out_dir)
    plot_ptm_boxplot(ptm_data, args.out_dir)
    plot_scatter(plddt_data, ptm_data, plddt_raw, ptm_raw, args.out_dir)
    plot_mean_bar(plddt_data, ptm_data, args.out_dir)
    plot_pass_bars(plddt_data, args.out_dir)
    plot_combined(plddt_data, ptm_data, plddt_raw, ptm_raw, args.out_dir)

    print("\nGenerating supplementary figures...")
    plot_supplementary(plddt_data, ptm_data, plddt_raw, ptm_raw, all_data, args.out_dir)

    print(f"\nDone! All figures saved to {args.out_dir}")


if __name__ == '__main__':
    main()
