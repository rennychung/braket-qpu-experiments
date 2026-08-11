# Amazon Braket QPU Experiments

Quantum hardware experiments performed through Amazon Braket across three quantum-computing platforms:

* **QuEra Aquila** — neutral-atom quantum processor
* **Rigetti Ankaa-3** — superconducting quantum processor
* **IonQ Forte-1** — trapped-ion quantum processor

The repository contains hardware experiment scripts, measurement data, analysis code, and validation utilities developed while working with these devices.

## QuEra Aquila

Analog Hamiltonian simulation experiments were implemented using programmable neutral-atom arrays and time-dependent Rabi and detuning schedules.

The hardware study includes:

* system-size scaling at **4, 8, 12, and 16 atoms**
* an independent 4-atom control
* 8-atom hold-time experiments at **1 μs and 2 μs**
* **500 shots per hardware run**
* analysis of Rydberg excitation populations, loading success, multi-excitation probability, and nearest-neighbor correlations

Sanitized hardware measurement records and a summary figure are included in `aquila/`.

## Rigetti Ankaa-3

Gate-model experiments were implemented on the Ankaa-3 superconducting QPU using six-qubit GHZ circuits with programmable delay sweeps.

The accompanying analysis includes:

* GHZ-state preparation
* programmable delay experiments
* measurement retrieval
* even/odd parity analysis
* statistical uncertainty estimates
* normalized-parity and exponential-decay diagnostics

The experiment, retrieval, and analysis scripts are contained in `ankaa3/`.

## IonQ Forte-1

Four-qubit experiments were implemented on the Forte-1 trapped-ion QPU, including GHZ and approximate W-state proxy circuits.

The workflow includes circuit construction, Braket hardware submission, measurement retrieval, and parity-visibility analysis.

Code and the retained numerical result summary are contained in `forte1/`.

## Validation

The `validation/` directory contains preflight checks used during hardware development, including:

* Aquila hardware-constraint checks
* Ankaa-3 supported-operation checks
* local OpenQASM delay validation

These complement the hardware scripts by documenting part of the validation process used before QPU execution.

## Repository Structure

```text
aquila/       QuEra Aquila experiments, hardware data, and analysis
ankaa3/       Rigetti Ankaa-3 experiments, retrieval, and analysis
forte1/       IonQ Forte-1 experiments and results
validation/   Device and program validation utilities
```

## Setup

Install the required Python packages with:

```bash
pip install -r requirements.txt
```

Hardware submission requires Amazon Braket access and locally configured AWS credentials. No credentials are included in this repository.

## Data and Provenance

Hardware-result files included here have been sanitized to remove private Amazon Braket task identifiers and AWS account information while retaining the scientific measurements and relevant experimental metadata.

`CHANGES.md` records the mapping from the original research files to the public versions and documents the limited changes made for public release.
