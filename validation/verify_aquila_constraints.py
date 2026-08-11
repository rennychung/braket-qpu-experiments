"""Query Aquila device constraints against the proposed pulse limits."""

import numpy as np
from braket.aws import AwsDevice

try:
    print("Querying QuEra Aquila device constraints...")
    device = AwsDevice("arn:aws:braket:us-east-1::device/qpu/quera/Aquila")
    caps = device.properties.paradigm
    
    print("\n--- AQUILA DEVICE CONSTRAINTS ---")
    print(f"Maximum duration: {caps.time_max * 1e6:.4f} us")
    print(f"Maximum amplitude: {caps.amplitude.max / (2*np.pi*1e6):.4f} MHz")
    print(f"Time resolution: {caps.time_resolution * 1e9:.1f} ns")
    
    print("\n--- PROPOSED PROGRAM LIMITS ---")
    print(f"Proposed duration: 3.9000 us")
    print(f"Proposed OMEGA_MAX: 2.5000 MHz")
    
    if caps.time_max * 1e6 < 3.9:
        print("\n[!] Duration exceeds the device limit.")
    else:
        print("\n[v] Duration is within the device limit.")
        
    if caps.amplitude.max / (2*np.pi*1e6) < 2.5:
        print("[!] OMEGA_MAX exceeds the device limit.")
    else:
        print("[v] OMEGA_MAX is within the device limit.")

except Exception as e:
    print(f"\n[!] Device constraint query failed: {e}")
