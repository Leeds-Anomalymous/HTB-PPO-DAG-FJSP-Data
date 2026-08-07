# DAG-Constrained Flexible Job Shop Scheduling Data

This repository contains benchmark and case-study instances used to evaluate scheduling methods for flexible job shop problems with directed acyclic graph (DAG) precedence constraints. It accompanies the manuscript *Graph Reinforcement Learning with a Heuristic Trajectory Baseline for High-Speed Train Overhaul Scheduling*.

## Contents

```text
.
├── LFJS/
│   ├── 18_18_27_5_1.txt
│   ├── 18_18_27_5_2.txt
│   ├── 20_20_28_5_1.txt
│   ├── 20_20_28_5_2.txt
│   ├── 22_22_29_5_1.txt
│   └── 22_22_29_5_2.txt
├── case/
│   ├── Generated_Case_J1_MaxM2_Dev40pct_noSpecial.txt
│   ├── Generated_Case_J5_MaxM3_Dev40pct_noSpecial.txt
│   ├── Generated_Case_J10_MaxM3_Dev40pct_noSpecial.txt
│   ├── Generated_Case_J20_MaxM4_Dev40pct_noSpecial.txt
│   └── case_generator_from_table.py
└── SHA256SUMS
```

The `LFJS` directory contains six large synthetic benchmark instances. The `case` directory contains four anonymized, industry-derived scheduling scenarios with 1, 5, 10, and 20 replicated overhaul jobs, together with the script used to generate case instances from a process table.

## Instance format

Each instance is a plain-text file. Lines beginning with `#` contain metadata. The first non-comment line has three integers:

```text
number_of_operations number_of_precedence_arcs number_of_machines
```

The next `number_of_precedence_arcs` lines each contain a zero-based directed arc:

```text
predecessor_operation successor_operation
```

The remaining `number_of_operations` lines describe machine alternatives for one operation. Each line has the form:

```text
number_of_alternatives machine_1 processing_time_1 ... machine_k processing_time_k
```

Machine identifiers are zero-based, and processing times are expressed in minutes.

File integrity can be checked from the repository root with:

```bash
sha256sum --check SHA256SUMS
```

## Case-instance generator

`case/case_generator_from_table.py` uses only the Python standard library. It expects a UTF-8, seven-column Markdown table named `case_info_matched_to_case_total.txt` by default. The columns are:

1. operation identifier;
2. operation name in the source language;
3. English operation name;
4. nominal processing time;
5. predecessor identifiers or names;
6. successor identifiers or names;
7. notes.

The process table may contain numbered physical operations and optional named start or end milestones. It is not included in this public data package because it contains organization-specific process descriptions. The four generated and anonymized case instances are provided directly for evaluation.

To generate another instance:

1. Place an appropriately formatted process table in the working directory.
2. Edit the configuration constants at the top of `case_generator_from_table.py`.
3. Create the configured output directory if it does not already exist.
4. Run the script from that directory:

```bash
python case_generator_from_table.py
```

Nominal processing times expressed as ranges or multiple alternatives are converted to their arithmetic mean. The generator then samples each nonzero processing time from a Gaussian distribution truncated to the configured deviation range. Zero-duration milestones are represented by one fixed machine and a processing time of zero.

## Reproducibility notes

The published instance files are fixed and can be used without running the generator. The generator uses Python's global pseudorandom number generator. Set a deterministic seed before generation if byte-for-byte repeatability is required.

The public YFJS instances discussed in the manuscript are not redistributed here and remain available from their original cited source.

## Citation

If you use these instances, cite the accompanying manuscript:

> Graph Reinforcement Learning with a Heuristic Trajectory Baseline for High-Speed Train Overhaul Scheduling.

Publication metadata and a persistent identifier will be added when available.

## License

The Python generator is released under the MIT License; see `LICENSE-CODE`.
The distributed instance data are released under the Creative Commons
Attribution 4.0 International License (CC BY 4.0); see `LICENSE-DATA.md`.
