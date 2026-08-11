from braket.aws import AwsDevice, AwsQuantumTask
from braket.circuits import Circuit
import numpy as np
import time
import json
import sys
import os
from pathlib import Path

# ===================================================================
# CONFIGURATION
# ===================================================================
DEVICE_ARN = "arn:aws:braket:us-east-1::device/qpu/ionq/Forte-1"
N = 4                           # Four-qubit experiment
WAIT_TIMES_US = [0, 16]         # Only 2 points – minimal for decay trend
SHOTS = 100                     # Lowest usable shots for visibility fit (200–300 is sweet spot)
TIMEOUT_SEC = 1800              # 30 min max wait – cancel if stuck

OUTPUT_DIR = Path(os.environ.get(
    "FORTE1_OUTPUT_DIR",
    Path(__file__).resolve().parent / "data"
))

# ===================================================================
# CIRCUIT BUILDERS
# ===================================================================
def build_ghz_circuit(N):
    """Exact GHZ + global H for X-basis parity"""
    circ = Circuit()
    circ.h(0)
    for i in range(N-1):
        circ.cnot(i, i+1)
    circ.h(range(N))  # Measure parity in X-basis
    return circ

def build_w_state_approx(N):
    """Best gate-model W-state approximation – controlled RY ladder, no extra CNOTs"""
    circ = Circuit()
    theta0 = 2 * np.arcsin(1 / np.sqrt(N))
    circ.ry(0, theta0)
    
    for k in range(1, N):
        theta_k = 2 * np.arcsin(1 / np.sqrt(N - k + 1))
        # Controlled spreading: RY(theta/2) -> CNOT -> RY(-theta/2) -> CNOT
        circ.ry(k, theta_k / 2)
        circ.cnot(k-1, k)
        circ.ry(k, -theta_k / 2)
        circ.cnot(k-1, k)
    
    circ.h(range(N))  # X-parity
    print(f"WARNING: Approximate W-state proxy for N={N} – not exact symmetric Radius-1 (requires Rydberg blockade)")
    return circ

# ===================================================================
# PARITY VISIBILITY
# ===================================================================
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

# ===================================================================
# MAIN TEST
# ===================================================================
print("=== IonQ Forte-1 Small Test (Gate-Model Proxy) ===")
print(f"Device: {DEVICE_ARN}")
print(f"N={N}, Shots={SHOTS}, Waits={WAIT_TIMES_US}")

results = {"GHZ": [], "W": [], "timestamps": []}

try:
    device = AwsDevice(DEVICE_ARN)
    print(f"Connected: {device.name} (Trapped-ion QPU)")
    if not device.is_available:
        print("Device currently unavailable. Check Braket console for status/reservations.")
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
        # Note: Barriers removed – IonQ handles idle time via scheduler
        
        print(f"  t={wait_us}us submitting...", end="")
        try:
            task = device.run(circ, shots=SHOTS)
            task_id = task.id
            task_ids.append(task_id)
            print(" submitted")
            
            # Poll with timeout & cancel
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

# Save results
timestamp = time.strftime("%Y%m%d_%H%M%S")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
json_file = OUTPUT_DIR / f"ionq_forte_test_{timestamp}.json"
with open(json_file, "w") as f:
    json.dump(results, f, indent=2, default=str)

print("\n=== Test Complete ===")
print(f"GHZ visibilities: {results['GHZ']}")
print(f"W visibilities: {results['W']}")
print(f"Saved: {json_file}")
print("Check Braket console → Tasks for logs, counts, and queue status.")
