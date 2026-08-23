"""Analyze Ankaa-3 parity measurements and fit an exponential decay."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from scipy.optimize import curve_fit


def compute_parity(measurement_counts, _n_qubits):
    """Return parity and its binomial standard error.

    Parity is ``P = 2 p_even - 1``, so its standard error is twice the
    binomial standard error of ``p_even``.
    """
    even_count = 0
    odd_count = 0

    for bitstring, count in measurement_counts.items():
        if bitstring.count("1") % 2 == 0:
            even_count += count
        else:
            odd_count += count

    total = even_count + odd_count
    if total == 0:
        raise ValueError("measurement_counts contains no shots")

    p_even = even_count / total
    z = 1.96
    denominator = 1 + z**2 / total
    centre = (p_even + z**2 / (2 * total)) / denominator
    radius = z * np.sqrt(
        p_even * (1 - p_even) / total + z**2 / (4 * total**2)
    ) / denominator
    p_even_ci95 = [max(0.0, centre - radius), min(1.0, centre + radius)]
    return {
        "parity": (even_count - odd_count) / total,
        "error": 2 * np.sqrt(p_even * (1 - p_even) / total),
        "parity_ci95": [2 * p_even_ci95[0] - 1, 2 * p_even_ci95[1] - 1],
        "p_even": p_even,
        "p_odd": 1 - p_even,
        "even_count": even_count,
        "odd_count": odd_count,
        "total": total,
    }


def exp_decay(t, p0, gamma):
    """Exponential decay model: ``P(t) = p0 * exp(-gamma * t)``."""
    return p0 * np.exp(-gamma * t)


def coefficient_of_determination(observed, predicted):
    """Return the ordinary, unweighted coefficient of determination."""
    observed = np.asarray(observed, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    total_sum_squares = np.sum((observed - np.mean(observed)) ** 2)
    if total_sum_squares == 0:
        return np.nan
    return float(1 - np.sum((observed - predicted) ** 2) / total_sum_squares)


def absolute_interval(interval):
    """Transform an interval for parity into an interval for absolute parity."""
    low, high = interval
    if low <= 0 <= high:
        return [0.0, max(abs(low), abs(high))]
    return [min(abs(low), abs(high)), max(abs(low), abs(high))]


def analyze_results(results_file):
    """Analyze completed measurements in a retrieval-results JSON file."""
    with open(results_file, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    print("=" * 60)
    print("NORMALIZED-PARITY ANALYSIS")
    print("=" * 60)
    print(f"Experiment: {data['experiment']}")
    print(f"Qubits: {data['config']['n_qubits']}")

    results = [result for result in data["results"] if result["status"] == "completed"]
    if not results:
        print("\nERROR: no completed results found")
        return None

    print(f"Completed tasks: {len(results)}")
    analysis = []
    for result in results:
        hold_us = result["hold_us"]
        parity_data = compute_parity(result["measurement_counts"], data["config"]["n_qubits"])
        analysis.append({
            "hold_us": hold_us,
            "parity": parity_data["parity"],
            "error": parity_data["error"],
            "parity_ci95": parity_data["parity_ci95"],
            "p_even": parity_data["p_even"],
            "shots": result["total_shots"],
            **parity_data,
        })
        print(f"\n{hold_us:.2f} us:")
        print(f"  Parity: {parity_data['parity']:.4f} +/- {parity_data['error']:.4f}")
        print(f"  P(even): {parity_data['p_even']:.4f}")
        print(f"  Counts: {parity_data['even_count']} even, {parity_data['odd_count']} odd")

    analysis.sort(key=lambda item: item["hold_us"])
    times = np.array([item["hold_us"] for item in analysis])
    parities = np.array([item["parity"] for item in analysis])
    errors = np.array([item["error"] for item in analysis])

    p0_observed = parities[0]
    if abs(p0_observed) < np.finfo(float).eps:
        raise ValueError("Cannot normalize parity because the first parity is zero")
    normalized_parity = np.abs(parities) / abs(p0_observed)
    absolute_parity_intervals = np.array([
        absolute_interval(item["parity_ci95"]) for item in analysis
    ])
    normalized_intervals = absolute_parity_intervals / abs(p0_observed)

    p0_fit = gamma_fit = gamma_error = fit_r_squared = None
    predicted_crossing_us = None
    try:
        fit_parameters, covariance = curve_fit(
            exp_decay,
            times,
            np.abs(parities),
            p0=[abs(p0_observed), 0.15],
            sigma=np.maximum(errors, 1e-12),
            absolute_sigma=True,
            bounds=([0.0, 0.0], [np.inf, np.inf]),
        )
        p0_fit, gamma_fit = fit_parameters
        gamma_error = float(np.sqrt(covariance[1, 1]))
        fit_r_squared = coefficient_of_determination(
            np.abs(parities), exp_decay(times, p0_fit, gamma_fit)
        )
        if gamma_fit > 0:
            predicted_crossing_us = float(-np.log(0.95) / gamma_fit)

        print("\nEXPONENTIAL FIT")
        print("P(t) = P0 * exp(-gamma * t)")
        print(f"P0 = {p0_fit:.4f}")
        print(f"gamma = {gamma_fit:.4f} +/- {gamma_error:.4f} us^-1")
        print(f"T2* = 1/gamma = {1 / gamma_fit:.2f} us")
        print(f"R^2 (unweighted) = {fit_r_squared:.4f}")
        if predicted_crossing_us is not None:
            print(f"Predicted time to normalized parity 0.95: {predicted_crossing_us:.3f} us")
    except (RuntimeError, ValueError, np.linalg.LinAlgError) as exc:
        print(f"\nWARNING: exponential fit failed: {exc}")

    observed_crossings = []
    for index in range(len(times) - 1):
        if normalized_parity[index] > 0.95 and normalized_parity[index + 1] < 0.95:
            t1, p1 = times[index], normalized_parity[index]
            t2, p2 = times[index + 1], normalized_parity[index + 1]
            observed_crossings.append(t1 + (0.95 - p1) * (t2 - t1) / (p2 - p1))

    observed_crossing_us = float(observed_crossings[0]) if observed_crossings else None
    if observed_crossing_us is None:
        print("\nNo normalized-parity crossing at 0.95 was observed in the sampled range.")
    else:
        print(f"\nObserved normalized-parity crossing at: {observed_crossing_us:.3f} us")

    plot_analysis(
        times, parities, errors, normalized_parity, normalized_intervals,
        p0_fit, gamma_fit, fit_r_squared, analysis,
    )

    output = {
        "experiment": data["experiment"],
        "config": data["config"],
        "analysis": analysis,
        "fit_params": {
            "P0": float(p0_fit) if p0_fit is not None else None,
            "gamma": float(gamma_fit) if gamma_fit is not None else None,
            "gamma_error": gamma_error,
            "T2_star": float(1 / gamma_fit) if gamma_fit is not None else None,
            "r_squared_unweighted": fit_r_squared,
        },
        "crossing_diagnostic": {
            "observed_crossing_us": observed_crossing_us,
            "predicted_crossing_us": predicted_crossing_us,
        },
    }

    results_path = Path(results_file)
    analysis_file = results_path.with_name(
        f"normalized_parity_analysis_{results_path.stem}.json"
    )
    with open(analysis_file, "w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2)
    print(f"Analysis saved: {analysis_file}")
    return output


def clean_axes(*axes):
    """Apply the repository's clean, grid-free figure style."""
    for axis in axes:
        axis.grid(False)
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.tick_params(direction="out", length=3, width=0.8)


def plot_analysis(
    times, parities, errors, normalized_parity, normalized_intervals,
    p0_fit, gamma_fit, fit_r_squared, analysis,
):
    """Plot parity, normalized parity, residuals, and outcome probabilities."""
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.labelsize": 10,
        "axes.titlesize": 10,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "legend.fontsize": 8,
        "lines.linewidth": 1.5,
    })
    fig, axes = plt.subplots(2, 2, figsize=(7.0, 6.1))
    clean_axes(*axes.ravel())

    measured_handle = Line2D(
        [], [], color="#2166ac", marker="o", markerfacecolor="white",
        markeredgewidth=1.1, linewidth=0, label="Measured",
    )
    fit_label = "Exponential fit"
    if fit_r_squared is not None:
        fit_label += f" ($R^2={fit_r_squared:.2f}$)"
    fit_handle = Line2D(
        [], [], color="#b2182b", linestyle="--", linewidth=1.5, label=fit_label,
    )

    axis = axes[0, 0]
    absolute_parity = np.abs(parities)
    absolute_intervals = np.array([
        absolute_interval(item["parity_ci95"]) for item in analysis
    ])
    axis.errorbar(times, absolute_parity,
                  yerr=[absolute_parity - absolute_intervals[:, 0],
                        absolute_intervals[:, 1] - absolute_parity],
                  fmt="o", color="#2166ac",
                  markerfacecolor="white", markeredgewidth=1.1, capsize=3)
    if gamma_fit is not None:
        t_fit = np.linspace(0, times[-1], 100)
        axis.plot(t_fit, exp_decay(t_fit, p0_fit, gamma_fit), "--", color="#b2182b")
    axis.set_xlabel("Hold time ($\\mu$s)")
    axis.set_ylabel("Absolute parity, $|P|$")
    axis.set_title("Parity decay")
    axis.legend(handles=[measured_handle, fit_handle] if gamma_fit is not None else [measured_handle])

    reference_handle = Line2D([], [], color="#555555", linestyle="--", linewidth=1.2,
                               label="0.95 reference")
    axis = axes[0, 1]
    axis.errorbar(times, normalized_parity,
                  yerr=[normalized_parity - normalized_intervals[:, 0],
                        normalized_intervals[:, 1] - normalized_parity],
                  fmt="o", color="#238b45",
                  markerfacecolor="white", markeredgewidth=1.1, capsize=3)
    axis.axhline(0.95, color="#555555", linestyle="--", linewidth=1.2)
    normalized_handle = Line2D([], [], color="#238b45", marker="o", markerfacecolor="white",
                                markeredgewidth=1.1, linewidth=0, label="Normalized parity")
    axis.set_xlabel("Hold time ($\\mu$s)")
    axis.set_ylabel("Normalized parity, $|P|/|P_0|$")
    axis.set_title("Normalized parity")
    axis.set_ylim(0, 1.1)
    axis.legend(handles=[normalized_handle, reference_handle])

    axis = axes[1, 0]
    if gamma_fit is not None:
        residuals = np.abs(parities) - exp_decay(times, p0_fit, gamma_fit)
        axis.errorbar(times, residuals, yerr=1.96 * errors, fmt="o", color="#762a83",
                      markerfacecolor="white", markeredgewidth=1.1, capsize=3)
        axis.axhline(0, color="#333333", linewidth=1.0)
    axis.set_xlabel("Hold time ($\\mu$s)")
    axis.set_ylabel("Fit residual")
    axis.set_title("Fit residuals")

    axis = axes[1, 1]
    hold_times = [item["hold_us"] for item in analysis]
    even_probabilities = [item["p_even"] for item in analysis]
    odd_probabilities = [item["p_odd"] for item in analysis]
    axis.plot(hold_times, even_probabilities, "o-", color="#2166ac", markerfacecolor="white",
              label="Even outcomes")
    axis.plot(hold_times, odd_probabilities, "s-", color="#b2182b", markerfacecolor="white",
              label="Odd outcomes")
    axis.axhline(0.5, color="#555555", linestyle="--", linewidth=1.0)
    axis.set_xlabel("Hold time ($\\mu$s)")
    axis.set_ylabel("Outcome probability")
    axis.set_title("Parity outcomes")
    axis.set_ylim(0, 1)
    axis.legend()

    fig.text(0.5, 0.01, "Error bars: 95% Wilson intervals for parity.",
             ha="center", va="bottom", fontsize=7.5, color="#444444")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    plot_file = Path("normalized_parity_analysis.png")
    fig.savefig(plot_file, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Plot saved: {plot_file}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python analyze_parity.py <results_file.json>")
        sys.exit(1)
    analyze_results(sys.argv[1])
