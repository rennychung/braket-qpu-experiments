# Amazon Braket QPU Experiments

Experiments and analysis performed through Amazon Braket on three quantum-computing platforms:

* **QuEra Aquila** — neutral-atom quantum processor
* **Rigetti Ankaa-3** — superconducting quantum processor
* **IonQ Forte-1** — trapped-ion quantum processor

The repository contains hardware experiment scripts, retained measurement data, analysis code, and several validation checks used during development.

## QuEra Aquila

The Aquila experiments use programmable neutral-atom arrays with time-dependent Rabi and detuning schedules.

The retained hardware study includes system-size scaling at **4, 8, 12, and 16 atoms** using a **4.5 µm nearest-neighbor blockade geometry**, together with an independent 4-atom control and 8-atom hold-time runs at **1 µs and 2 µs**. Each hardware run used **500 shots**.

The analysis extracts Rydberg excitation populations, atom-loading success, multi-excitation probability, and nearest-neighbor correlations from the returned measurements.

![QuEra Aquila hardware results](aquila/aquila_final_summary.png)

The underlying hardware records and analysis scripts are in [`aquila/`](aquila/).

## Rigetti Ankaa-3

The Ankaa-3 experiments use six-qubit GHZ circuits with programmable delays. The code in [`ankaa3/`](ankaa3/) covers hardware submission and retrieval, even/odd parity analysis, statistical uncertainty estimates, and normalized-parity and exponential-decay diagnostics.

## IonQ Forte-1

The Forte-1 experiments use four-qubit GHZ and approximate W-state proxy circuits. [`forte1/`](forte1/) contains the hardware script and retained numerical results, including the parity-visibility analysis.

## Validation

Several preflight checks used during development are retained in [`validation/`](validation/). These include:

* Aquila hardware-constraint verification
* Ankaa-3 supported-operation checks
* local OpenQASM delay validation

These scripts document part of the validation process used before QPU execution.

## Repository Structure

```text
aquila/       QuEra Aquila experiments, hardware data, figures, and analysis
ankaa3/       Rigetti Ankaa-3 experiments, retrieval, and parity analysis
forte1/       IonQ Forte-1 experiments and retained results
validation/   Device-capability and program-validation utilities
```

## Setup

Install the Python dependencies with:

```bash
pip install -r requirements.txt
```

Submitting new hardware jobs requires Amazon Braket access and locally configured AWS credentials. No credentials are included in this repository.

## Repository Notes

The hardware-result files in this public repository have been sanitized to remove private Amazon Braket task identifiers and AWS account information while retaining the scientific measurements and relevant experimental metadata.

The public scripts are cleaned versions of the original research files rather than rewritten implementations. Experiment definitions, circuits, pulse schedules, geometries, shot counts, measurement processing, and numerical analysis were not changed during the public-release cleanup.

Historical internal identifiers are retained in raw records where changing them would alter the archived provenance. [`CHANGES.md`](CHANGES.md) summarizes the limited presentation, privacy, and path-related changes made for public release.

These were exploratory hardware experiments rather than a standardized cross-platform benchmark.
