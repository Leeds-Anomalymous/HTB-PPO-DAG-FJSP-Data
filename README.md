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
│   ├── case_generator_from_table.py
│   └── templates/
│       └── case_info_matched_to_case_total.txt
└── SHA256SUMS
```

The `LFJS` directory contains six large synthetic benchmark instances. The `case` directory contains four industry-derived scheduling scenarios with 1, 5, 10, and 20 replicated overhaul jobs, together with the source process table and the script used to generate case instances from it.

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

`case/case_generator_from_table.py` uses only the Python standard library. It reads the included UTF-8, seven-column Markdown table at `case/templates/case_info_matched_to_case_total.txt`. The columns are:

1. operation identifier;
2. operation name in the source language;
3. English operation name;
4. nominal processing time;
5. predecessor identifiers or names;
6. successor identifiers or names;
7. notes.

The process table contains 107 numbered operations and three optional named milestones. By default, the generator retains the numbered operations and their 116 precedence arcs, and excludes the three named milestones. Set `INCLUDE_SPECIAL_NODES = True` to include the milestones. The table is kept in a separate `templates` directory so that it is not mistaken for an instance when evaluating the `.txt` files in `case`.

To generate an instance with the default configuration, run the following command from the repository root:

```bash
python case/case_generator_from_table.py
```

Input and output paths are resolved relative to the script, so the script can also be called by its absolute path from another directory. The output directory, `case/case-analysis`, is created automatically. The default configuration generates 20 jobs on 36 machines, with one to four compatible machines per operation and a processing-time deviation limit of 40%.

To generate other case sizes, edit the configuration constants at the top of the script. The four published scenarios use these settings, with `MIN_MACHINES_PER_OP = 1`, `DEVIATION_RATIO = 0.40`, and `INCLUDE_SPECIAL_NODES = False` throughout:

| `NUM_JOBS` | `TOTAL_MACHINES_GLOBAL` | `MAX_MACHINES_PER_OP` |
| --- | --- | --- |
| 1 | 12 | 2 |
| 5 | 16 | 3 |
| 10 | 24 | 3 |
| 20 | 36 | 4 |

Nominal processing times expressed as ranges or multiple alternatives are converted to their arithmetic mean. The generator then samples each nonzero processing time from a Gaussian distribution truncated to the configured deviation range. Zero-duration milestones are represented by one fixed machine and a processing time of zero.

## Reproducibility notes

The published instance files are fixed and can be used without running the generator. The generator uses Python's global pseudorandom number generator. Set a deterministic seed before generation if byte-for-byte repeatability of new instances is required. The original random states are not included in this package; regenerating instances with the same configuration therefore does not reproduce the exact processing times and machine assignments in the four published files. Generated files are written to a separate directory and do not replace the published instances.

The public YFJS instances discussed in the manuscript are not redistributed here and remain available from their original cited source.

## Citation

If you use these instances, cite the accompanying manuscript:

> Graph Reinforcement Learning with a Heuristic Trajectory Baseline for High-Speed Train Overhaul Scheduling.

Publication metadata and a persistent identifier will be added when available.

## License

The Python generator is released under the MIT License; see `LICENSE-CODE`.
The distributed instance data are released under the Creative Commons
Attribution 4.0 International License (CC BY 4.0); see `LICENSE-DATA.md`.
