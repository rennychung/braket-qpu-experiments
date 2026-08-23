"""Run single-acquisition GHZ and approximate-W circuits on IonQ Forte-1."""

import json
import os
import sys
import time
from pathlib import Path

import numpy as np
from braket.aws import AwsDevice, AwsQuantumTask
from braket.circuits import Circuit


DEVICE_ARN = "arn:aws:braket:us-east-1::device/qpu/ionq/Forte-1"
N = 4
SHOTS = 100
TIMEOUT_SEC = 1800
OUTPUT_DIR = Path(os.environ.get("FORTE1_OUTPUT_DIR", Path(__file__).resolve().parent / "data"))


def build_ghz_circuit(n_qubits):
    """Build a GHZ circuit followed by an X-basis rotation."""
    circ = Circuit()
    circ.h(0)
    for i in range(n_qubits - 1):
        circ.cnot(i, i + 1)
    circ.h(range(n_qubits))
    return circ


def build_w_state_approx(n_qubits):
    """Build a gate-model W-state proxy using a controlled-RY ladder."""
    circ = Circuit()
    theta0 = 2 * np.arcsin(1 / np.sqrt(n_qubits))
    circ.ry(0, theta0)

    for k in range(1, n_qubits):
        theta_k = 2 * np.arcsin(1 / np.sqrt(n_qubits - k + 1))
        circ.ry(k, theta_k / 2)
        circ.cnot(k - 1, k)
        circ.ry(k, -theta_k / 2)
        circ.cnot(k - 1, k)

    circ.h(range(n_qubits))
    return circ


def compute_parity_visibility(counts, n_qubits):
    """Return the even/odd parity observable in [-1, 1]."""
    even = 0
    total = 0
    for bitstring, count in counts.items():
        num_ones = sum(c == "1" for c in bitstring)
        if num_ones % 2 == 0:
            even += count
        total += count
    if total == 0:
        raise ValueError("measurement counts contain no shots")
    return (2 * even / total) - 1


def run_state(device, state_type, builder):
    """Submit and retrieve one circuit for a state type.

    This experiment does not contain a programmable wait gate. Results are
    therefore not labelled as measurements at different wait times.
    """
    circuit = builder(N)
    print(f"  Submitting {state_type} circuit...")
    task = device.run(circuit, shots=SHOTS)
    start = time.time()
    while task.state() not in ["COMPLETED", "FAILED", "CANCELLED"]:
        if time.time() - start > TIMEOUT_SEC:
            task.cancel()
            raise TimeoutError(f"{state_type} task exceeded {TIMEOUT_SEC} seconds")
        time.sleep(15)
        task = AwsQuantumTask(arn=task.id)

    if task.state() != "COMPLETED":
        raise RuntimeError(f"{state_type} task ended with status {task.state()}")

    counts = task.result().measurement_counts
    visibility = compute_parity_visibility(counts, N)
    print(f"  {state_type} parity visibility: {visibility:.3f}")
    return visibility


def main():
    print("=== IonQ Forte-1 gate-model experiment ===")
    print(f"Device: {DEVICE_ARN}")
    print(f"N={N}, shots={SHOTS}; no wait-time sweep is programmed")

    try:
        device = AwsDevice(DEVICE_ARN)
        print(f"Connected: {device.name} (trapped-ion QPU)")
        if not device.is_available:
            print("Device currently unavailable; check its Braket status.")
            return 2
    except Exception as exc:
        print(f"Connection failed: {exc}")
        print("Check Braket access and the configured region (us-east-1).")
        return 2

    results = {"GHZ": [], "W": [], "timestamps": [], "wait_times_us": None}
    for state_type, builder in [("GHZ", build_ghz_circuit), ("W", build_w_state_approx)]:
        try:
            results[state_type].append(run_state(device, state_type, builder))
        except Exception as exc:
            print(f"{state_type} run failed: {exc}")
            results[state_type].append(None)
        results["timestamps"].append(time.strftime("%Y-%m-%d %H:%M:%S"))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_path = OUTPUT_DIR / f"ionq_forte_test_{timestamp}.json"
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, allow_nan=False)

    print("\n=== Experiment complete ===")
    print(f"GHZ visibilities: {results['GHZ']}")
    print(f"W visibilities: {results['W']}")
    print(f"Saved: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
