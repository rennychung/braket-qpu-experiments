"""Inspect the OpenQASM operation capabilities reported by Ankaa-3."""

from braket.aws import AwsDevice

DEVICE_ARN = "arn:aws:braket:us-west-1::device/qpu/rigetti/Ankaa-3"

try:
    device = AwsDevice(DEVICE_ARN)
    print("Ankaa-3 device properties loaded.")
    
    # Check supported operations
    ops = device.properties.action['braket.ir.openqasm.program'].supportedOperations
    print(f"\nSupported OpenQASM operations ({len(ops)}):")
    print(sorted(ops))
    
    # Check specifically for delay-related terms
    delays = [op for op in ops if 'delay' in op.lower()]
    print(f"\nDelay-related operations: {delays}")

    # Check for pragma or verbatim support
    print(f"\nVerbatim support: {device.properties.action['braket.ir.openqasm.program'].dict().get('supportVerbatim', 'Unknown')}")

except Exception as e:
    print(f"Capability query failed: {e}")
