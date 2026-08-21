"""Analyze Ankaa-3 parity measurements and fit an exponential reference curve."""
import json
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import sem
from pathlib import Path

def compute_parity(measurement_counts, n_qubits):
    """Return the even/odd parity observable and its binomial error."""
    even_count = 0
    odd_count = 0
    
    for bitstring, count in measurement_counts.items():
        num_ones = bitstring.count('1')
        if num_ones % 2 == 0:
            even_count += count
        else:
            odd_count += count
    
    total = even_count + odd_count
    
    parity = (even_count - odd_count) / total

    p_even = even_count / total
    error = np.sqrt(p_even * (1 - p_even) / total)
    
    return {
        'parity': parity,
        'error': error,
        'p_even': p_even,
        'p_odd': 1 - p_even,
        'even_count': even_count,
        'odd_count': odd_count,
        'total': total
    }

def exp_decay(t, P0, gamma):
    """Exponential decay: P(t) = P0 * exp(-gamma * t)"""
    return P0 * np.exp(-gamma * t)

def analyze_results(results_file):
    """Analyze completed measurements in a retrieval-results JSON file."""
    with open(results_file, 'r') as f:
        data = json.load(f)
    
    print("="*60)
    print("NORMALIZED-PARITY ANALYSIS")
    print("="*60)
    print(f"Experiment: {data['experiment']}")
    print(f"Qubits: {data['config']['n_qubits']}")
    
    results = [r for r in data['results'] if r['status'] == 'completed']
    
    if not results:
        print("\n✗ No completed results found!")
        return
    
    print(f"Completed tasks: {len(results)}")
    
    analysis = []
    
    for r in results:
        hold_us = r['hold_us']
        counts = r['measurement_counts']
        
        parity_data = compute_parity(counts, data['config']['n_qubits'])
        
        analysis.append({
            'hold_us': hold_us,
            'parity': parity_data['parity'],
            'error': parity_data['error'],
            'p_even': parity_data['p_even'],
            'shots': r['total_shots'],
            **parity_data
        })
        
        print(f"\n{hold_us:.2f} μs:")
        print(f"  Parity: {parity_data['parity']:.4f} ± {parity_data['error']:.4f}")
        print(f"  P(even): {parity_data['p_even']:.4f}")
        print(f"  Counts: {parity_data['even_count']} even, {parity_data['odd_count']} odd")
    
    analysis = sorted(analysis, key=lambda x: x['hold_us'])
    
    times = np.array([a['hold_us'] for a in analysis])
    parities = np.array([a['parity'] for a in analysis])
    errors = np.array([a['error'] for a in analysis])
    
    P0 = parities[0]
    normalized_parity = np.abs(parities) / np.abs(P0)
    normalized_errors = errors / np.abs(P0)
    
    print("\n" + "="*60)
    print("NORMALIZED COHERENCE")
    print("="*60)
    
    for t, p, e in zip(times, normalized_parity, normalized_errors):
        print(f"{t:6.2f} μs: {p:.4f} ± {e:.4f}")
    
    try:
        popt, pcov = curve_fit(
            exp_decay, 
            times, 
            np.abs(parities),
            p0=[P0, 0.15],
            sigma=errors,
            absolute_sigma=True
        )
        
        P0_fit, gamma_fit = popt
        gamma_err = np.sqrt(pcov[1, 1])
        
        print("\n" + "="*60)
        print("EXPONENTIAL REFERENCE FIT")
        print("="*60)
        print(f"P(t) = P0 * exp(-γt)")
        print(f"P0 = {P0_fit:.4f}")
        print(f"γ = {gamma_fit:.4f} ± {gamma_err:.4f} μs⁻¹")
        print(f"T2* = 1/γ = {1/gamma_fit:.2f} μs")
        
        t_95_pred = -np.log(0.95) / gamma_fit
        print(f"\nPredicted time to 0.95: {t_95_pred:.3f} μs")
        
    except Exception as e:
        print(f"\n✗ Fit failed: {e}")
        P0_fit, gamma_fit = None, None
        t_95_pred = None
    
    print("\n" + "="*60)
    print("0.95 CROSSING")
    print("="*60)
    
    crossing_times = []
    for i in range(len(times) - 1):
        if normalized_parity[i] > 0.95 and normalized_parity[i+1] < 0.95:
            t1, p1 = times[i], normalized_parity[i]
            t2, p2 = times[i+1], normalized_parity[i+1]
            t_cross = t1 + (0.95 - p1) * (t2 - t1) / (p2 - p1)
            crossing_times.append(t_cross)
    
    if crossing_times:
        t_95_obs = crossing_times[0]
        print(f"✓ Observed crossing at: {t_95_obs:.3f} μs")
        
        if t_95_pred is not None:
            deviation = abs(t_95_obs - t_95_pred) / t_95_pred * 100
            print(f"  Fit prediction: {t_95_pred:.3f} μs")
            print(f"  Deviation: {deviation:.1f}%")
            
            if deviation > 20:
                print("\nLarge deviation from the fitted exponential")
                print("  Observed crossing differs from the fitted curve")
            else:
                print("\n✓ Consistent with smooth exponential decay")
                print("  Observed crossing is consistent with the fitted curve")
    else:
        print("✗ No crossing found in sampled range")
        print("  Need more time points or different spacing")
    
    plot_analysis(times, parities, errors, normalized_parity,
                  normalized_errors, P0_fit, gamma_fit, analysis)
    
    output = {
        "experiment": data['experiment'],
        "config": data['config'],
        "analysis": analysis,
        "fit_params": {
            "P0": float(P0_fit) if P0_fit is not None else None,
            "gamma": float(gamma_fit) if gamma_fit is not None else None,
            "gamma_error": float(gamma_err) if gamma_fit is not None else None,
            "T2_star": float(1/gamma_fit) if gamma_fit is not None else None
        },
        "crossing_diagnostic": {
            "observed_crossing_us": float(crossing_times[0]) if crossing_times else None,
            "predicted_crossing_us": float(t_95_pred) if t_95_pred is not None else None
        }
    }
    
    results_path = Path(results_file)
    analysis_file = results_path.with_name(
        f"normalized_parity_analysis_{results_path.stem}.json"
    )
    with open(analysis_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✓ Analysis saved: {analysis_file}")
    
    return output

def plot_analysis(times, parities, errors, normalized_parity, 
                  normalized_errors, P0_fit, gamma_fit, analysis):
    """Plot parity, normalization, fit residuals, and outcome probabilities."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    ax = axes[0, 0]
    ax.errorbar(times, np.abs(parities), yerr=errors, 
                fmt='o', ms=8, capsize=5, label='Measured')
    
    if gamma_fit is not None:
        t_fit = np.linspace(0, times[-1], 100)
        p_fit = exp_decay(t_fit, P0_fit, gamma_fit)
        ax.plot(t_fit, p_fit, 'r--', label=f'Fit: γ={gamma_fit:.3f} μs⁻¹')
    
    ax.set_xlabel('Hold Time (μs)', fontsize=12)
    ax.set_ylabel('|Parity|', fontsize=12)
    ax.set_title('Raw Parity Coherence', fontsize=14, fontweight='bold')
    ax.grid(alpha=0.3)
    ax.legend()
    
    ax = axes[0, 1]
    ax.errorbar(times, normalized_parity, yerr=normalized_errors,
                fmt='o', ms=8, capsize=5, label='Normalized |P|/|P₀|')
    ax.axhline(0.95, color='red', linestyle='--', linewidth=2, 
               label='0.95 reference')
    
    ax.set_xlabel('Hold Time (μs)', fontsize=12)
    ax.set_ylabel('Normalized Coherence', fontsize=12)
    ax.set_title('Normalized parity at 0.95 reference', fontsize=14, fontweight='bold')
    ax.set_ylim([0, 1.1])
    ax.grid(alpha=0.3)
    ax.legend()
    
    ax = axes[1, 0]
    if gamma_fit is not None:
        residuals = np.abs(parities) - exp_decay(times, P0_fit, gamma_fit)
        ax.errorbar(times, residuals, yerr=errors, fmt='o', ms=8, capsize=5)
        ax.axhline(0, color='black', linestyle='-', linewidth=1)
        ax.set_xlabel('Hold Time (μs)', fontsize=12)
        ax.set_ylabel('Residuals', fontsize=12)
        ax.set_title('Fit Residuals', fontsize=14, fontweight='bold')
        ax.grid(alpha=0.3)
    
    ax = axes[1, 1]
    p_even = [a['p_even'] for a in analysis]
    p_odd = [a['p_odd'] for a in analysis]
    
    ax.plot(times, p_even, 'o-', label='P(even)', ms=8)
    ax.plot(times, p_odd, 's-', label='P(odd)', ms=8)
    ax.axhline(0.5, color='gray', linestyle='--', alpha=0.5)
    
    ax.set_xlabel('Hold Time (μs)', fontsize=12)
    ax.set_ylabel('Probability', fontsize=12)
    ax.set_title('Parity Distribution', fontsize=14, fontweight='bold')
    ax.set_ylim([0, 1])
    ax.grid(alpha=0.3)
    ax.legend()
    
    plt.tight_layout()
    
    plot_file = Path('normalized_parity_analysis.png')
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    print(f"✓ Plot saved: {plot_file}")
    
    plt.show()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python analyze_results.py <results_file.json>")
        print("\nExample:")
        print("  python analyze_results.py rigetti_results_20260119_150022.json")
        sys.exit(1)
    
    results_file = sys.argv[1]
    analyze_results(results_file)
