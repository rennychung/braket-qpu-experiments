
"""Run the six-qubit OpenQASM delay program on the local simulator."""

import pytest

try:
    from braket.devices import LocalSimulator
except Exception as exc:  # pragma: no cover - environment compatibility guard
    pytest.skip(f"Amazon Braket SDK unavailable in this Python environment: {exc}", allow_module_level=True)

qasm_str = """
OPENQASM 3.0;
include "stdgates.inc";

qubit[6] q;

// GHZ preparation
h q[0];
cz q[0], q[1];
h q[1];
cz q[1], q[2];
h q[2];
cz q[2], q[3];
h q[3];
cz q[3], q[4];
h q[4];
cz q[4], q[5];
h q[5];

// Delay duration: 1.0 us
delay[1.0us] q[0];
delay[1.0us] q[1];
delay[1.0us] q[2];
delay[1.0us] q[3];
delay[1.0us] q[4];
delay[1.0us] q[5];

// Final basis rotation
h q[0];
h q[1];
h q[2];
h q[3];
h q[4];
h q[5];
"""

from braket.ir.openqasm import Program as OpenQASMProgram


def test_openqasm_delay_runs():
    """Compile and execute the delay program on the local simulator."""
    device = LocalSimulator()
    program = OpenQASMProgram(source=qasm_str)
    task = device.run(program, shots=10)
    counts = task.result().measurement_counts
    assert sum(counts.values()) == 10


if __name__ == "__main__":
    test_openqasm_delay_runs()
    print("Local OpenQASM delay validation succeeded.")
