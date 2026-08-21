"""Submit a six-qubit GHZ hold-time circuit to Rigetti Ankaa-3."""

from braket.aws import AwsDevice
from braket.circuits import Circuit, Instruction, Delay
import json
import os
from datetime import datetime
import numpy as np
from pathlib import Path

DEVICE_ARN = "arn:aws:braket:us-west-1::device/qpu/rigetti/Ankaa-3"
OUTPUT_DIR = Path(os.environ.get(
    "ANKAA3_OUTPUT_DIR",
    Path(__file__).resolve().parent / "outputs"
))
SHOTS = 1000
N_QUBITS = 6
HOLD_TIME_NS = 0
QUBITS = [0, 1, 2, 3, 4, 5]

def apply_hold_time(circ, qubits, hold_ns):
    """Add a delay, specified in nanoseconds, to each qubit."""
    if hold_ns <= 0:
        return
    duration_s = hold_ns / 1e9
    for q in qubits:
        circ.add_instruction(Instruction(Delay(duration_s), q))

def build_dtc_circuit(n_qubits, hold_ns):
    """Build the GHZ preparation, hold, and measurement-basis rotation."""
    circ = Circuit()
    
    circ.h(QUBITS[0])
    for i in range(n_qubits - 1):
        q_src, q_tgt = QUBITS[i], QUBITS[i+1]
        circ.h(q_tgt)
        circ.cz(q_src, q_tgt)
        circ.h(q_tgt)
        
    apply_hold_time(circ, QUBITS, hold_ns)
            
    for q in QUBITS:
        circ.h(q)
        
    return circ

def main():
    print("="*60)
    print("RIGETTI ANKAA-3 - GHZ HOLD-TIME SUBMISSION")
    print("="*60)
    print(f"Qubits:    {N_QUBITS}")
    print(f"Hold Time: {HOLD_TIME_NS} ns ({HOLD_TIME_NS/1000:.1f} μs)")
    print(f"Shots:     {SHOTS}")
    
    circ = build_dtc_circuit(N_QUBITS, HOLD_TIME_NS)
    print(f"Circuit Depth: {circ.depth}")
    print("\nCircuit diagram (text):")
    try: print(circ.diagram())
    except: print("(Diagram print not supported by this Braket version)")
    
    try:
        device = AwsDevice(DEVICE_ARN)
        print(f"\nSubmitting to {device.name}...")
        
        print("\nHardware capabilities:")
        print("Note: Ankaa-3 heavy-hex lattice — CZ(0,i) may compile with SWAPs if not adjacent.")
        print("Supported operations:", device.properties.action['braket.ir.openqasm.program'].supportedOperations[:15], "...")
        
        task = device.run(circ, shots=SHOTS)
        task_id = task.id
        print("\nSubmission succeeded")
        print(f"Initial status: {task.state()}")
        
        metadata = {
            "experiment": "rigetti_ghz_hold_time",
            "timestamp": datetime.now().isoformat(),
            "device": DEVICE_ARN,
            "task_id": task_id,
            "config": {
                "n_qubits": N_QUBITS,
                "hold_ns": HOLD_TIME_NS,
                "shots": SHOTS,
                "qubit_mapping": QUBITS
            },
            "status": "submitted"
        }
        
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"rigetti_ghz_hold_time_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_path = OUTPUT_DIR / filename
        with open(output_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"✓ Metadata saved: {output_path}")
        
    except Exception as e:
        print(f"\n✗ FAILED: {e}")

if __name__ == "__main__":
    main()
