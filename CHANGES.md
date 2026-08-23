# Public Release Notes

This repository contains cleaned public versions of the original experiment
and analysis files.

## Changes made for public release

- Removed private Amazon Braket task identifiers and AWS account information.
- Replaced local filesystem paths with repository-relative paths.
- Removed development and troubleshooting output not needed for reproduction.
- Renamed selected files to describe their function more clearly.
- Neutralized obsolete exploratory terminology in public-facing labels and
  documentation.
- Updated the Aquila figure label from the historical `Radius1` identifier to
  `4.5 µm nearest-neighbor spacing`.
- Added safeguards so newly generated private task identifiers are written only
  to ignored runtime-output locations.

Experiment definitions, circuits, pulse schedules, geometries, shot counts, and
retained raw measurements were not changed as part of the public-release cleanup.
The later publication-figure pass added derived uncertainty metadata and did not
alter the raw hardware records.

Raw hardware records retain historical internal identifiers where changing them
would alter the archived provenance.

No hardware submission or cloud retrieval was performed during cleanup.

## Release-readiness maintenance

- Added conditioned-shot metadata and explicit uncertainty methods to the Aquila
  publication outputs.
- Corrected Ankaa-3 parity uncertainty and made submission/retrieval metadata
  formats compatible.
- Removed the unsupported Forte-1 wait-time interpretation; the script now
  performs one acquisition per state.
- Added regression tests, Python-version guidance, and ignored runtime-output
  directories.
