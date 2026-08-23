"""Query Aquila device constraints against the proposed pulse limits."""

import numpy as np
import sys

try:
    from braket.aws import AwsDevice
except Exception as exc:
    print(f"Amazon Braket SDK unavailable in this Python environment: {exc}")
    sys.exit(2)

try:
    print("Querying QuEra Aquila device constraints...")
    device = AwsDevice("arn:aws:braket:us-east-1::device/qpu/quera/Aquila")
    caps = device.properties.paradigm
    
    print("\n--- AQUILA DEVICE CONSTRAINTS ---")
    print(f"Maximum duration: {caps.time_max * 1e6:.4f} us")
    print(f"Maximum amplitude: {caps.amplitude.max / (2*np.pi*1e6):.4f} MHz")
    print(f"Time resolution: {caps.time_resolution * 1e9:.1f} ns")
    
    print("\n--- PROPOSED PROGRAM LIMITS ---")
    # The longest submitted pulse is the 4 us preparation plus the 2 us hold.
    proposed_duration_us = 6.0000
    print(f"Proposed duration: {proposed_duration_us:.4f} us")
    print(f"Proposed OMEGA_MAX: 2.5000 MHz")
    
    if caps.time_max * 1e6 < proposed_duration_us:
        print("\n[!] Duration exceeds the device limit.")
    else:
        print("\n[v] Duration is within the device limit.")
        
    if caps.amplitude.max / (2*np.pi*1e6) < 2.5:
        print("[!] OMEGA_MAX exceeds the device limit.")
    else:
        print("[v] OMEGA_MAX is within the device limit.")

except Exception as e:
    print(f"\n[!] Device constraint query failed: {e}")
