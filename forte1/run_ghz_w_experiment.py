from braket.aws import AwsDevice, AwsQuantumTask
from braket.circuits import Circuit
import numpy as np
import time
import json
import sys
import os
from pathlib import Path

DEVICE_ARN = "arn:aws:braket:us-east-1::device/qpu/ionq/Forte-1"
N = 4
WAIT_TIMES_US = [0, 16]
SHOTS = 100
TIMEOUT_SEC = 1800

OUTPUT_DIR = Path(os.environ.get(
    "FORTE1_OUTPUT_DIR",
    Path(__file__).resolve().parent / "data"
))

def build_ghz_circuit(N):
    """Build a GHZ circuit followed by an X-basis rotation."""
    circ = Circuit()
    circ.h(0)
    for i in range(N-1):
        circ.cnot(i, i+1)
    circ.h(range(N))  # Measure parity in X-basis
    return circ

def build_w_state_approx(N):
    """Build a gate-model W-state proxy using a controlled RY ladder."""
    circ = Circuit()
    theta0 = 2 * np.arcsin(1 / np.sqrt(N))
    circ.ry(0, theta0)
    
    for k in range(1, N):
        theta_k = 2 * np.arcsin(1 / np.sqrt(N - k + 1))
        circ.ry(k, theta_k / 2)
        circ.cnot(k-1, k)
        circ.ry(k, -theta_k / 2)
        circ.cnot(k-1, k)
    
    circ.h(range(N))  # X-parity
    print(f"Using an approximate W-state proxy for N={N}; it is not the Radius-1 Rydberg state.")
    return circ

def compute_parity_visibility(counts, N):
    """Even/odd parity fraction from bitstrings"""
    even = 0
    total = 0
    for bitstring, cnt in counts.items():
        num_ones = sum(1 for c in bitstring if c == '1')
        if num_ones % 2 == 0:
            even += cnt
        total += cnt
    if total == 0:
        return 0.0
    return (2 * even / total) - 1  # [-1,1] visibility

print("=== IonQ Forte-1 gate-model experiment ===")
print(f"Device: {DEVICE_ARN}")
print(f"N={N}, Shots={SHOTS}, Waits={WAIT_TIMES_US}")

results = {"GHZ": [], "W": [], "timestamps": []}

try:
    device = AwsDevice(DEVICE_ARN)
    print(f"Connected: {device.name} (Trapped-ion QPU)")
    if not device.is_available:
        print("Device currently unavailable; check its Braket status.")
        sys.exit(1)
except Exception as e:
    print(f"Connection failed: {e}")
    print("Check Braket access and the configured region (us-east-1).")
    sys.exit(1)

for state_type in ['GHZ', 'W']:
    print(f"\nRunning {state_type}...")
    vis_list = []
    task_ids = []
    
    builder = build_ghz_circuit if state_type == 'GHZ' else build_w_state_approx
    
    for wait_us in WAIT_TIMES_US:
        circ = builder(N)
        print(f"  t={wait_us}us submitting...", end="")
        try:
            task = device.run(circ, shots=SHOTS)
            task_id = task.id
            task_ids.append(task_id)
            print(" submitted")
            
            start = time.time()
            while task.state() not in ['COMPLETED', 'FAILED', 'CANCELLED']:
                if time.time() - start > TIMEOUT_SEC:
                    task.cancel()
                    print(" Timeout – cancelled")
                    break
                time.sleep(15)
                task = AwsQuantumTask(task_id)
            
            if task.state() == 'COMPLETED':
                result = task.result()
                counts = result.measurement_counts
                vis = compute_parity_visibility(counts, N)
                vis_list.append(vis)
                print(f" Visibility = {vis:.3f}")
            else:
                print(f" Failed: {task.state()}")
                vis_list.append(np.nan)
                
        except Exception as e:
            print(f" Submission failed: {e}")
            vis_list.append(np.nan)
    
    results[state_type] = vis_list
    results["timestamps"].append(time.strftime("%Y-%m-%d %H:%M:%S"))

timestamp = time.strftime("%Y%m%d_%H%M%S")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
json_file = OUTPUT_DIR / f"ionq_forte_test_{timestamp}.json"
with open(json_file, "w") as f:
    json.dump(results, f, indent=2, default=str)

print("\n=== Experiment complete ===")
print(f"GHZ visibilities: {results['GHZ']}")
print(f"W visibilities: {results['W']}")
print(f"Saved: {json_file}")
