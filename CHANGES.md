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
  `4.5 µm blockade geometry`. Numerical data and analysis were unchanged.
- Added safeguards so newly generated private task identifiers are written only
  to ignored runtime-output locations.

Experiment definitions, circuits, pulse schedules, geometries, shot counts,
measurement processing, and numerical analysis were not changed as part of
the public-release cleanup.

Raw hardware records retain historical internal identifiers where changing
them would alter the archived provenance.

No hardware submission or cloud retrieval was performed during cleanup.
