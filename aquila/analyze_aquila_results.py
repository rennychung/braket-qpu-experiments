"""Generate publication-ready figures from the retained Aquila shot records."""

import json
import os
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D


REPO_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("AQUILA_DATA_DIR", REPO_DIR / "data"))
FIGURES_DIR = Path(os.environ.get("AQUILA_FIGURES_DIR", REPO_DIR / "figures"))

RAW_RUNS = [
    ("Scaling", 4, 0.0, "Radius1", "aquila_n4_scaling.json"),
    ("Scaling", 8, 0.0, "Radius1", "aquila_n8_scaling.json"),
    ("Scaling", 12, 0.0, "Radius1", "aquila_n12_scaling.json"),
    ("Scaling", 16, 0.0, "Radius1", "aquila_n16_scaling.json"),
    ("Control", 4, 0.0, "Control", "aquila_n4_control.json"),
    ("Decay", 8, 1.0, "Radius1", "aquila_n8_hold_1us.json"),
    ("Decay", 8, 2.0, "Radius1", "aquila_n8_hold_2us.json"),
]


def wilson_interval(successes, trials, z=1.96):
    """Return a Wilson 95% confidence interval for a proportion."""
    if trials == 0:
        return [np.nan, np.nan]
    p = successes / trials
    denom = 1.0 + z**2 / trials
    centre = (p + z**2 / (2.0 * trials)) / denom
    radius = z * np.sqrt(p * (1.0 - p) / trials + z**2 / (4.0 * trials**2)) / denom
    return [max(0.0, centre - radius), min(1.0, centre + radius)]


def mean_interval(values, scale=1.0, z=1.96):
    """Return a normal-approximation 95% CI for a shot-level mean."""
    values = np.asarray(values, dtype=float) / scale
    if len(values) < 2:
        return [np.nan, np.nan]
    half_width = z * np.std(values, ddof=1) / np.sqrt(len(values))
    mean = np.mean(values)
    return [mean - half_width, mean + half_width]


def load_conditioned_rydberg(path, n):
    """Load post-shot Rydberg occupations after the successful-loading filter."""
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    conditioned = []
    for measurement in payload["measurements"]:
        if measurement.get("shotMetadata", {}).get("shotStatus") != "Success":
            continue
        pre = measurement["shotResult"]["preSequence"]
        post = measurement["shotResult"]["postSequence"]
        if len(pre) == n and len(post) == n and sum(pre) == n:
            conditioned.append(1 - np.asarray(post, dtype=int))
    submitted = int(payload.get("taskMetadata", {}).get("shots", len(payload["measurements"])))
    return np.asarray(conditioned, dtype=int), submitted


def g2_stat(rydberg):
    """Mean nearest-neighbor pair correlation used by the original analysis."""
    if len(rydberg) == 0:
        return np.nan
    density = np.mean(rydberg, axis=0)
    pair_density = (rydberg.T @ rydberg) / len(rydberg)
    values = []
    for i in range(rydberg.shape[1] - 1):
        denominator = density[i] * density[i + 1]
        if denominator > 1e-6:
            values.append(pair_density[i, i + 1] / denominator)
    return float(np.mean(values)) if values else np.nan


def bootstrap_g2_interval(rydberg, seed=20260823, samples=1000):
    """Deterministic bootstrap 95% interval for g2(1)."""
    if len(rydberg) < 2:
        return [np.nan, np.nan]
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(samples):
        indices = rng.integers(0, len(rydberg), size=len(rydberg))
        values.append(g2_stat(rydberg[indices]))
    return [float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))]


def analyze_run(kind, n, hold, state, filename):
    rydberg, m_submitted = load_conditioned_rydberg(DATA_DIR / filename, n)
    excitations = np.sum(rydberg, axis=1)
    m_valid = len(excitations)
    p1 = float(np.mean(excitations == 1))
    density = float(np.mean(excitations) / n)
    return {
        "type": kind,
        "n": n,
        "spacing": 18.0 if state == "Control" else 4.5,
        "hold": hold,
        "state": state,
        "m_valid": m_valid,
        "m_submitted": m_submitted,
        "loading_rate": m_valid / m_submitted,
        "mean_n": float(np.mean(excitations)),
        "mean_n_ci": mean_interval(excitations),
        "mean_n_per_atom": density,
        "mean_n_per_atom_ci": mean_interval(excitations, scale=n),
        "p_exactly_one": p1,
        "p_exactly_one_ci": wilson_interval(int(np.sum(excitations == 1)), m_valid),
        "fidelity_all": float(np.mean(excitations == n)),
        "g2_1": g2_stat(rydberg),
        "g2_1_ci": bootstrap_g2_interval(rydberg),
        "_rydberg": rydberg,
    }


def configure_style():
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.labelsize": 10,
        "axes.titlesize": 10,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "legend.fontsize": 8,
        "lines.linewidth": 1.5,
        "savefig.facecolor": "white",
        "svg.hashsalt": "aquila-publication",
    })


def clean_axes(*axes):
    for ax in axes:
        ax.grid(False)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.tick_params(direction="out", length=3, width=0.8)


def save_figure(
    fig,
    stem,
    note=("95% CIs: Wilson for P(n=1), normal approximation for means, "
          "bootstrap for g₂(1). M = shots retained after loading."),
):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig.text(0.5, 0.01, note, ha="center", va="bottom", fontsize=7.5, color="#444444")
    fig.tight_layout(rect=(0, 0.06, 1, 1), pad=0.8)
    for extension in ("png", "pdf", "svg"):
        save_kwargs = {"dpi": 600 if extension == "png" else None, "bbox_inches": "tight"}
        if extension == "pdf":
            save_kwargs["metadata"] = {
                "Creator": "Aquila publication figure generator",
                "Producer": "Matplotlib",
                "CreationDate": None,
                "ModDate": None,
            }
        output_path = FIGURES_DIR / f"{stem}.{extension}"
        fig.savefig(output_path, **save_kwargs)
        if extension == "svg":
            canonicalize_svg(output_path)
    plt.close(fig)


def canonicalize_svg(path):
    """Remove timestamp/random-ID churn from Matplotlib SVG output."""
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"\s*<dc:date>.*?</dc:date>\s*", "\n", text, flags=re.DOTALL)
    ids = {}

    def replace_id(match):
        old = match.group(1)
        new = ids.setdefault(old, f"m{len(ids):08d}")
        return f'id="{new}"'

    text = re.sub(r'id="(m[0-9a-f]+)"', replace_id, text)
    for old, new in ids.items():
        text = text.replace(f"#{old}", f"#{new}")
    path.write_text(text, encoding="utf-8", newline="\n")


def asymmetric_errors(values, intervals):
    return [
        [value - interval[0] for value, interval in zip(values, intervals)],
        [interval[1] - value for value, interval in zip(values, intervals)],
    ]


def plot_summary(runs):
    scaling = sorted([r for r in runs if r["type"] == "Scaling"], key=lambda r: r["n"])
    decay = sorted([r for r in runs if r["n"] == 8 and r["type"] in {"Scaling", "Decay"}], key=lambda r: r["hold"])
    ns = [r["n"] for r in scaling]
    densities = [r["mean_n_per_atom"] for r in scaling]
    probabilities = [r["p_exactly_one"] for r in decay]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.8, 3.35))
    clean_axes(ax1, ax2)
    ax1.errorbar(
        ns, densities,
        yerr=asymmetric_errors(densities, [r["mean_n_per_atom_ci"] for r in scaling]),
        fmt="o-", color="#2166ac", markerfacecolor="white", markeredgewidth=1.2,
        capsize=3,
    )
    ax1.plot(ns, [1 / n for n in ns], color="#555555", linestyle=(0, (1, 2)),
             label="_nolegend_")
    ax1.set_title("Atom-number scaling")
    ax1.set_xlabel("Atom number, $N$")
    ax1.set_ylabel("$\\langle n\\rangle/N$")
    ax1.set_xticks(ns)
    ax1.legend(handles=[
        Line2D([], [], color="#2166ac", marker="o", markerfacecolor="white",
               markeredgewidth=1.2, linewidth=1.5, label="4.5 µm spacing"),
        Line2D([], [], color="#555555", linestyle=(0, (1, 2)), linewidth=1.5,
               label="$1/N$ reference"),
    ])

    ax2.errorbar(
        [r["hold"] for r in decay], probabilities,
        yerr=asymmetric_errors(probabilities, [r["p_exactly_one_ci"] for r in decay]),
        fmt="s-", color="#238b45", markerfacecolor="white", markeredgewidth=1.2,
        capsize=3,
    )
    ax2.set_title("$N = 8$ hold-time dependence")
    ax2.set_xlabel("Hold time ($\\mu$s)")
    ax2.set_ylabel("$P(n=1)$")
    ax2.set_xticks([r["hold"] for r in decay])
    ax2.set_ylim(bottom=0)
    save_figure(fig, "aquila_final_summary")


def plot_individual_figures(runs):
    scaling = sorted([r for r in runs if r["type"] == "Scaling"], key=lambda r: r["n"])
    control = next(r for r in runs if r["type"] == "Control")
    decay = sorted([r for r in runs if r["n"] == 8 and r["type"] in {"Scaling", "Decay"}], key=lambda r: r["hold"])

    fig, ax = plt.subplots(figsize=(3.45, 3.1))
    clean_axes(ax)
    comparison = [scaling[0], control]
    values = [r["mean_n"] for r in comparison]
    errors = asymmetric_errors(values, [r["mean_n_ci"] for r in comparison])
    bars = ax.bar(["4.5 µm spacing", "18 µm control spacing"], values,
                  color=["#2166ac", "#b2182b"], alpha=0.9, edgecolor="none", linewidth=0,
                  yerr=errors, capsize=3)
    ax.set_title("Blockade–control comparison")
    ax.set_ylabel("$\\langle n\\rangle$")
    ax.tick_params(axis="x", labelrotation=18, length=0)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + max(values) * 0.05,
                f"{value:.3f}", ha="center", va="bottom", fontsize=8)
    save_figure(fig, "fig1_blockade_control_contrast")

    fig, ax = plt.subplots(figsize=(3.45, 3.1))
    clean_axes(ax)
    ns = [r["n"] for r in scaling]
    densities = [r["mean_n_per_atom"] for r in scaling]
    ax.errorbar(ns, densities,
                yerr=asymmetric_errors(densities, [r["mean_n_per_atom_ci"] for r in scaling]),
                fmt="o-", color="#2166ac", markerfacecolor="white", markeredgewidth=1.2,
                capsize=3)
    ax.set_xlabel("Atom number, $N$")
    ax.set_ylabel("$\\langle n\\rangle/N$")
    ax.set_title("Atom-number scaling")
    ax.set_xticks(ns)
    ax.set_ylim(bottom=0)
    save_figure(fig, "fig2_scale_invariance")

    fig, ax = plt.subplots(figsize=(3.45, 3.1))
    clean_axes(ax)
    g2_values = [r["g2_1"] for r in scaling]
    ax.errorbar(ns, g2_values,
                yerr=asymmetric_errors(g2_values, [r["g2_1_ci"] for r in scaling]),
                fmt="o", color="#762a83", markerfacecolor="white", markeredgewidth=1.2,
                capsize=3, label="_nolegend_")
    ax.axhline(1.0, color="#555555", linestyle=(0, (1, 2)), linewidth=1.2,
               label="_nolegend_")
    ax.set_xlabel("Atom number, $N$")
    ax.set_ylabel("$g_2(1)$")
    ax.set_title("Nearest-neighbor correlation")
    ax.set_xticks(ns)
    ax.legend(handles=[
        Line2D([], [], color="#762a83", marker="o", markerfacecolor="white",
               markeredgewidth=1.2, linewidth=0, label="Measured"),
        Line2D([], [], color="#555555", linestyle=(0, (1, 2)), linewidth=1.5,
               label="Independent limit"),
    ])
    save_figure(fig, "fig3_blockade_correlation")

    fig, ax = plt.subplots(figsize=(3.45, 3.1))
    clean_axes(ax)
    holds = [r["hold"] for r in decay]
    probabilities = [r["p_exactly_one"] for r in decay]
    ax.errorbar(holds, probabilities,
                yerr=asymmetric_errors(probabilities, [r["p_exactly_one_ci"] for r in decay]),
                fmt="s-", color="#238b45", markerfacecolor="white", markeredgewidth=1.2,
                capsize=3)
    ax.set_xlabel("Hold time ($\\mu$s)")
    ax.set_ylabel("$P(n=1)$")
    ax.set_title("$N = 8$ hold-time dependence")
    ax.set_xticks(holds)
    ax.set_ylim(bottom=0)
    save_figure(fig, "fig4_temporal_decay")


def main():
    configure_style()
    runs = [analyze_run(*run) for run in RAW_RUNS]
    public_runs = [{key: value for key, value in run.items() if key != "_rydberg"} for run in runs]
    with open(DATA_DIR / "aquila_plot_summary.json", "w", encoding="utf-8") as handle:
        json.dump(public_runs, handle, indent=2)
    plot_summary(runs)
    plot_individual_figures(runs)
    print(f"Figures written to {FIGURES_DIR}")


if __name__ == "__main__":
    main()
