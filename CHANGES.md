# Provenance cleanup ledger

Original archive files remain unchanged outside this directory. Public names
are clearer names; the edits below are limited to redaction, paths, and
documentation/output wording.

## Scientific scripts

| Original source | Public filename | Sensitive material removed | Path/comment changes | Executable scientific logic changed? |
|---|---|---|---|---|
| `DTC/scripts/querafullrun1.0.py` | `aquila/run_aquila_experiment.py` | Runtime task IDs are omitted from saved public result objects. | Output JSON/summary figure use configurable `AQUILA_OUTPUT_DIR`/`AQUILA_FIGURES_DIR`; promotional and task-ID wording neutralized. | No. Batch definitions, circuits, pulses, geometry, shots, delays, measurement processing, fidelity, leakage, and g² calculations are unchanged. |
| `DTC/scripts/plot_aquila_results.py` | `aquila/analyze_aquila_results.py` | None present. | Absolute paths replaced by `AQUILA_DATA_DIR`/`AQUILA_FIGURES_DIR`; promotional plot wording made descriptive. | No. Plotted selections and numeric transformations are unchanged. |
| `DTC/scripts/dtc_rigetti_threshold.py` | `ankaa3/submit_ghz_experiment.py` | No literal secret; generated task IDs remain internal runtime inputs and metadata defaults to ignored `ankaa3/outputs/`. | Output defaults to `ankaa3/outputs/`, configurable with `ANKAA3_OUTPUT_DIR`; generated filename and presentation wording neutralized. | No. GHZ circuit, delay conversion, mapping, hold time, and shots are unchanged. |
| `DTC/scripts/dtc_rigetti_retrieval.py` | `ankaa3/retrieve_results.py` | Task IDs remain in memory for retrieval but are omitted from saved result records; output defaults to ignored `ankaa3/outputs/`. | Output path and usage wording updated. | No. Retrieval and measurement-count processing are unchanged. |
| `DTC/scripts/dtc_rigetti_publication.py` | `ankaa3/analyze_parity.py` | None present. | Analysis filenames/keys/labels use normalized-parity and crossing-diagnostic wording. | No. The 0.95 reference, parity, error, normalization, fit, interpolation, and plots are unchanged. |
| `ionqtest.py` | `forte1/run_ghz_w_experiment.py` | Task ARN collection was removed from saved results; runtime IDs remain local for polling. | Generated results default to `forte1/data/`, configurable with `FORTE1_OUTPUT_DIR`; task-ID, cost, credit, billing, and device-personalization wording removed. | No. GHZ/W circuits, wait values, shots, polling, parity visibility, and numeric processing are unchanged. |

## Validation scripts

| Original source | Public filename | Sensitive material removed | Path/comment changes | Executable scientific logic changed? |
|---|---|---|---|---|
| Project-root `verify_aquila.py` | `validation/verify_aquila_constraints.py` | None; the public Aquila device ARN is retained. | Added a module docstring, removed a stale comment, normalized output labels/encoding, and made error/status wording descriptive. | No. The device-property query, 3.9 us duration comparison, 2.5 MHz amplitude comparison, and formulas are unchanged. |
| `DTC/scripts/check_rigetti_ops.py` | `validation/check_ankaa3_operations.py` | None; the public Ankaa-3 device ARN is retained. | Added a module docstring, removed the unused `json` import, and neutralized presentation wording. | No. Supported-operation, delay-term, and verbatim-support queries are unchanged. |
| `DTC/scripts/test_qasm_submission.py` | `validation/test_openqasm_delay.py` | None. | Added a module docstring, removed the unused `AwsDevice` import, clarified comments/status text, and removed an unsupported capability claim. | No. The six-qubit OpenQASM program, GHZ construction, 1.0 us delays, final rotations, local execution, and 10-shot count are unchanged. |

## Final public-release pass

- README Aquila inventory now describes seven raw completed result files: four
  scaling records, one N=4 control, and two N=8 hold-time records.
- Rigetti submission/retrieval outputs default to ignored `ankaa3/outputs/`.
  Retrieval keeps task IDs in memory for cloud access but omits them from saved
  result records.
- Rigetti analysis output is named `normalized_parity_analysis_*.json`, its
  figure is `normalized_parity_analysis.png`, and its result section is named
  `crossing_diagnostic`. These are presentation/output names only.
- No circuit, delay, shot, measurement, parity, fitting, interpolation, or
  numerical logic changed in this pass.

## Data and figure artifacts

| Original source | Public filename | Edit |
|---|---|---|
| `queradata/aquila_final_20260117_131030.json` | `aquila/data/aquila_hardware_results.json` | Six private task ARNs/account number replaced with batch labels; all batches and metrics retained. |
| `queradata/part1.json`–`part6.json` | `aquila/data/aquila_n4_scaling.json`, `aquila_n8_scaling.json`, `aquila_n12_scaling.json`, `aquila_n16_scaling.json`, `aquila_n8_hold_1us.json`, `aquila_n8_hold_2us.json` | Only task metadata IDs/account number replaced; measurements, shots, device, pulse metadata, geometry, and hold data retained. |
| `queradata/control.json` | `aquila/data/aquila_n4_control.json` | Only the private task metadata ARN/account number replaced; measurements, shots, device, pulse metadata, and geometry retained. |
| `finished product/queraresults/hardware_data_summary.json` | `aquila/data/aquila_plot_summary.json` | Six Aquila plotting rows plus N=4 control retained; unrelated IonQ benchmark row omitted. Numeric values unchanged. |
| `queradata/aquila_final_summary.png` | `aquila/figures/aquila_final_summary.png` | Copied without modification. |
| Nine `DTC/scripts/rigetti_dtc_pub*.json` hardware-submission files | `ankaa3/data/rigetti_dtc_pub*.json` | Private task ARNs/account number replaced; device, hold times, shots, mappings, and status retained. |
| `DTC/scripts/ionq_results.json` | `forte1/data/ionq_results.json` | Appended console/debug text removed so the original numeric JSON is valid; numeric values unchanged. |

## Diff review

The selected scripts were copied first and then edited only as listed above.
The file-by-file no-index diff against the archive sources is the authoritative
review (run from the archive workspace):

```text
git diff --no-index -- Amazon_Braket/querasimulation/querasimulation/DTC/scripts/querafullrun1.0.py "clean compile/braket-qpu-experiments/aquila/run_aquila_experiment.py"
git diff --no-index -- Amazon_Braket/querasimulation/querasimulation/DTC/scripts/plot_aquila_results.py "clean compile/braket-qpu-experiments/aquila/analyze_aquila_results.py"
git diff --no-index -- Amazon_Braket/querasimulation/querasimulation/DTC/scripts/dtc_rigetti_threshold.py "clean compile/braket-qpu-experiments/ankaa3/submit_ghz_experiment.py"
git diff --no-index -- Amazon_Braket/querasimulation/querasimulation/DTC/scripts/dtc_rigetti_retrieval.py "clean compile/braket-qpu-experiments/ankaa3/retrieve_results.py"
git diff --no-index -- Amazon_Braket/querasimulation/querasimulation/DTC/scripts/dtc_rigetti_publication.py "clean compile/braket-qpu-experiments/ankaa3/analyze_parity.py"
git diff --no-index -- Amazon_Braket/querasimulation/querasimulation/DTC/scripts/ionqtest.py "clean compile/braket-qpu-experiments/forte1/run_ghz_w_experiment.py"
```

No hardware submission or cloud retrieval was run during cleanup.
