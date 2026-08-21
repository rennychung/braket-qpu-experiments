"""Run the QuEra Aquila scaling, control, and hold-time measurements."""

from braket.aws import AwsDevice, AwsQuantumTask
from braket.ahs.atom_arrangement import AtomArrangement
from braket.ahs.driving_field import DrivingField
from braket.ahs.analog_hamiltonian_simulation import AnalogHamiltonianSimulation
from braket.timings.time_series import TimeSeries
import numpy as np
import matplotlib.pyplot as plt
import time
import json
from datetime import datetime
import os
from pathlib import Path

DEVICE_ARN = "arn:aws:braket:us-east-1::device/qpu/quera/Aquila"
SHOTS = 500
OUTPUT_DIR = Path(os.environ.get(
    "AQUILA_OUTPUT_DIR",
    Path(__file__).resolve().parent / "data"
))
FIGURES_DIR = Path(os.environ.get(
    "AQUILA_FIGURES_DIR",
    Path(__file__).resolve().parent / "figures"
))

C6 = 2 * np.pi * 862690
BLOCKADE_RADIUS = 8.6e-6
SPACING_RADIUS1 = 4.5e-6
SPACING_CONTROL = 18.0e-6

PREP_DURATION_US = 4.0
OMEGA_MAX = 2.5e6 * 2 * np.pi
DELTA_START = -10e6 * 2 * np.pi

def build_w_state_with_hold(hold_us=0.0):
    """
    Adiabatic prep followed by 'dark' hold time.
    Amplitude ramps Up then Down to 0 before hold.
    """
    prep_us = PREP_DURATION_US
    total_us = prep_us + hold_us
    
    times = [0.0, prep_us * 0.5 * 1e-6, prep_us * 1e-6, total_us * 1e-6]
    times = sorted(list(set(times)))

    amplitude = TimeSeries()
    amplitude.put(0.0, 0.0)
    amplitude.put(prep_us * 0.5 * 1e-6, OMEGA_MAX)
    amplitude.put(prep_us * 1e-6, 0.0)
    if hold_us > 0:
        amplitude.put(total_us * 1e-6, 0.0)

    detuning = TimeSeries()
    detuning.put(0.0, DELTA_START)
    detuning.put(prep_us * 1e-6, 0.0)
    if hold_us > 0:
        detuning.put(total_us * 1e-6, 0.0)
        
    phase = TimeSeries()
    phase.put(0.0, 0.0)
    phase.put(times[-1], 0.0)
    
    return DrivingField(amplitude=amplitude, detuning=detuning, phase=phase)

def build_excited_pulse(hold_us=0.0):
    """Fast Pi-pulse for independent control"""
    duration = 0.6 * 1e-6
    hold = hold_us * 1e-6
    total_time = duration + hold
    
    amplitude = TimeSeries()
    amplitude.put(0.0, 0.0)
    amplitude.put(0.1e-6, OMEGA_MAX)
    amplitude.put(duration - 0.1e-6, OMEGA_MAX)
    amplitude.put(duration, 0.0)
    amplitude.put(total_time, 0.0)

    detuning = TimeSeries()
    detuning.put(0.0, 0.0)
    detuning.put(total_time, 0.0)
    
    phase = TimeSeries()
    phase.put(0.0, 0.0)
    phase.put(total_time, 0.0)

    return DrivingField(amplitude=amplitude, detuning=detuning, phase=phase)

def build_register(n, spacing):
    reg = AtomArrangement()
    for i in range(n):
        reg.add((i * spacing, 0.0))
    return reg

BATCHES = [
    {'type': 'Scaling', 'n': 4,  'spacing': SPACING_RADIUS1, 'hold': 0.0, 'state': 'Radius1'},
    {'type': 'Scaling', 'n': 8,  'spacing': SPACING_RADIUS1, 'hold': 0.0, 'state': 'Radius1'},
    {'type': 'Scaling', 'n': 12, 'spacing': SPACING_RADIUS1, 'hold': 0.0, 'state': 'Radius1'},
    {'type': 'Scaling', 'n': 16, 'spacing': SPACING_RADIUS1, 'hold': 0.0, 'state': 'Radius1'},
    
    {'type': 'Control', 'n': 4,  'spacing': SPACING_CONTROL, 'hold': 0.0, 'state': 'Excited'},

    {'type': 'Decay',   'n': 8,  'spacing': SPACING_RADIUS1, 'hold': 1.0, 'state': 'Radius1'},
    {'type': 'Decay',   'n': 8,  'spacing': SPACING_RADIUS1, 'hold': 2.0, 'state': 'Radius1'},
]

def analyze_shots(measurements, n, state_type):
    valid = [s for s in measurements if sum(s.pre_sequence) == n]
    if not valid: return {'valid': 0, 'mean_n_per_atom': 0}
    
    ryd = 1 - np.array([s.post_sequence for s in valid])
    n_shots = len(ryd)
    n_exc = np.sum(ryd, axis=1)
    
    metrics = {
        'mean_n': np.mean(n_exc),
        'mean_n_per_atom': np.mean(n_exc) / n,
        'fidelity_1': np.sum(n_exc == 1) / n_shots,
        'fidelity_all': np.sum(n_exc == n) / n_shots,
        'leakage_0': np.sum(n_exc == 0) / n_shots
    }
    
    dens = np.mean(ryd, axis=0)
    corr = (ryd.T @ ryd) / n_shots
    
    g2_sum = 0
    g2_count = 0
    for i in range(n-1):
        j = i+1
        denom = dens[i]*dens[j]
        if denom > 1e-6:
            g2_sum += corr[i,j]/denom
            g2_count += 1
            
    metrics['g2_1'] = g2_sum/g2_count if g2_count > 0 else float('nan')
    return metrics

def run_experiment():
    print("="*60)
    print("QuEra Aquila: measurement run")
    print("Scaling (N=4-16) | Control (N=4) | Decay (1-2us)")
    print("="*60)
    
    print("="*60)
    
    USE_SIMULATOR = False

    if USE_SIMULATOR:
        from braket.devices import LocalSimulator
        device = LocalSimulator("braket_ahs")
        print("Testing on local simulator")
    else:
        device = AwsDevice(DEVICE_ARN)
        print("Submitting to Aquila hardware")
    
    tasks = []
    print("Submitting Tasks:")
    for b in BATCHES:
        if b['state'] == 'Radius1':
            pulse = build_w_state_with_hold(b['hold'])
        else:
            pulse = build_excited_pulse(b['hold'])
            
        reg = build_register(b['n'], b['spacing'])
        ahs = AnalogHamiltonianSimulation(register=reg, hamiltonian=pulse)
        
        if not USE_SIMULATOR:
            discretized_ahs = ahs.discretize(device)
            target_ahs = discretized_ahs
        else:
            target_ahs = ahs

        try:
            t = device.run(target_ahs, shots=SHOTS)
            b['task_id'] = t.id
            b['status'] = 'SUBMITTED'
            tasks.append(b)
            print(f"  [{b['type']}] N={b['n']} Hold={b['hold']}us -> submitted")
        except Exception as e:
            print(f"  FAILED: {e}")
            
    print("\nWaiting for Results...")
    while any(t['status'] == 'SUBMITTED' for t in tasks):
        for t in tasks:
            if t['status'] == 'SUBMITTED':
                qt = AwsQuantumTask(arn=t['task_id'])
                if qt.state() in ['COMPLETED', 'FAILED', 'CANCELLED']:
                    t['status'] = qt.state()
                    print(f"  N={t['n']} Hold={t['hold']}us: {t['status']}")
        time.sleep(30)
        
    results = {'batches': tasks, 'timestamp': datetime.now().isoformat()}
    
    for t in tasks:
        if t['status'] == 'COMPLETED':
            qt = AwsQuantumTask(arn=t['task_id'])
            res = qt.result()
            t['metrics'] = analyze_shots(res.measurements, t['n'], t['state'])
            
    public_batches = [
        {key: value for key, value in batch.items() if key != 'task_id'}
        for batch in tasks
    ]
    results = {'batches': public_batches, 'timestamp': results['timestamp']}

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fn = f"aquila_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_path = OUTPUT_DIR / fn
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved: {output_path}")
    
    plot_results(tasks)
    return results

def plot_results(tasks):
    try:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        scale_tasks = [t for t in tasks if t['type']=='Scaling' and t['status']=='COMPLETED']
        if scale_tasks:
            ns = [t['n'] for t in scale_tasks]
            ys = [t['metrics']['mean_n_per_atom'] for t in scale_tasks]
            ax1.plot(ns, ys, 'o-', label='Radius-1')
            
            ax1.plot(ns, [1/x for x in ns], 'k:', label='1/N', alpha=0.5)

            ctrl = [t for t in tasks if t['type']=='Control' and t['status']=='COMPLETED']
            if ctrl:
                ax1.plot([ctrl[0]['n']], [ctrl[0]['metrics']['mean_n_per_atom']], 'rx', label='Control (N=4)', markersize=10)
                
            ax1.set_title('Scaling (Hardware N<=16)')
            ax1.set_xlabel('N')
            ax1.set_ylabel('Mean Excitation / Atom')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
        decay_tasks = [t for t in tasks if (t['type']=='Decay' or (t['type']=='Scaling' and t['n']==8)) and t['status']=='COMPLETED']
        if decay_tasks:
            decay_tasks.sort(key=lambda x: x['hold'])
            ts = [t['hold'] for t in decay_tasks]
            ps = [t['metrics']['fidelity_1'] for t in decay_tasks]
            
            ax2.plot(ts, ps, 's-', color='green', label='W-state P(1)')
            ax2.set_title('Decay at N=8')
            ax2.set_xlabel('Hold Time (us)')
            ax2.set_ylabel('Probability P(1)')
            ax2.set_ylim(bottom=0)
            ax2.grid(True, alpha=0.3)
            
        plt.tight_layout()
        FIGURES_DIR.mkdir(parents=True, exist_ok=True)
        plt.savefig(FIGURES_DIR / 'aquila_final_summary.png')
        print("Saved summary plot.")
    except Exception as e:
        print(f"Plotting failed: {e}")

if __name__ == "__main__":
    run_experiment()
