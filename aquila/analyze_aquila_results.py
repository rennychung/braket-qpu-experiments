import json
import matplotlib.pyplot as plt
import numpy as np
import os
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("AQUILA_DATA_DIR", REPO_DIR / "data"))
FIGURES_DIR = Path(os.environ.get("AQUILA_FIGURES_DIR", REPO_DIR / "figures"))
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
summary_path = DATA_DIR / "aquila_plot_summary.json"
with open(summary_path, 'r') as f:
    data = json.load(f)

aquila_data = [d for d in data if d['type'] != 'IonQ Benchmark']

plt.figure(figsize=(8, 6))
r1_n4 = [d['mean_n'] for d in aquila_data if d['type'] == 'Radius1' and d['n'] == 4 and d['hold'] == 0][0]
ctrl_n4 = [d['mean_n'] for d in aquila_data if d['type'] == 'Control' and d['n'] == 4][0]

labels = ['Radius-1 (Blockaded)', 'Control (Independent)']
values = [r1_n4, ctrl_n4]
colors = ['#1f77b4', '#d62728']

bars = plt.bar(labels, values, color=colors, alpha=0.8, edgecolor='black')
plt.ylabel('Total Rydberg Excitations <N>')
plt.title('Blockade/control contrast (N=4)')
plt.grid(axis='y', linestyle='--', alpha=0.7)

for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval + 0.05, f'{yval:.3f}', ha='center', va='bottom', fontweight='bold')

plt.tight_layout()
plt.savefig(FIGURES_DIR / "fig1_blockade_control_contrast.png", dpi=300)
plt.close()

plt.figure(figsize=(8, 6))
scaling_data = sorted([d for d in aquila_data if d['type'] == 'Radius1' and d['hold'] == 0], key=lambda x: x['n'])
ns = [d['n'] for d in scaling_data]
densities = [d['mean_n_per_atom'] for d in scaling_data]

plt.plot(ns, densities, 'o-', color='#2ca02c', linewidth=2, markersize=8, label='Radius-1 (Measured)')
plt.axhline(y=np.mean(densities), color='gray', linestyle='--', alpha=0.5, label=f'Mean Density (~{np.mean(densities)*100:.1f}%)')

plt.xlabel('Number of Atoms (N)')
plt.ylabel('Excitation Density <n>/N')
plt.title('Excitation density across atom counts: N=4 to 16')
plt.ylim(0, 0.1)
plt.xticks(ns)
plt.grid(True, linestyle=':', alpha=0.6)
plt.legend()

plt.tight_layout()
plt.savefig(FIGURES_DIR / "fig2_scale_invariance.png", dpi=300)
plt.close()

plt.figure(figsize=(8, 6))
g2_vals = [d['g2_1'] for d in scaling_data]

plt.bar([str(n) for n in ns], g2_vals, color='#9467bd', alpha=0.7, edgecolor='black', label='Radius-1')
plt.axhline(y=1.0, color='red', linestyle='--', linewidth=2, label='Independent Limit (g2=1)')

plt.xlabel('Number of Atoms (N)')
plt.ylabel('Nearest-Neighbor Correlation g2(1)')
plt.title('Rydberg Blockade Strength Across Scales')
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.5)

plt.tight_layout()
plt.savefig(FIGURES_DIR / "fig3_blockade_correlation.png", dpi=300)
plt.close()

plt.figure(figsize=(8, 6))
decay_data = sorted([d for d in aquila_data if d['type'] == 'Radius1' and d['n'] == 8], key=lambda x: x['hold'])
holds = [d['hold'] for d in decay_data]
n_vals = [d['mean_n'] for d in decay_data]

plt.plot(holds, n_vals, 's--', color='#ff7f0e', linewidth=2, markersize=10)
plt.xlabel('Hold Time (µs)')
plt.ylabel('Total Excitations <N>')
plt.title('N=8 hold-time measurements (Radius-1)')
plt.grid(True, linestyle=':', alpha=0.6)

plt.tight_layout()
plt.savefig(FIGURES_DIR / "fig4_temporal_decay.png", dpi=300)
plt.close()

print(f"Figures written to {FIGURES_DIR}")
