"""Generate DAG-constrained flexible job shop instances from a process table.

The input is a seven-column Markdown table containing operation identifiers,
names, nominal processing times, and predecessor relationships. The generator
replicates the process DAG for the requested number of jobs and samples
compatible machines and processing times for each operation.
"""

import random
import re
from pathlib import Path

# Configuration
# 1) Use one job to validate the process graph, then increase NUM_JOBS to
#    replicate the same process template automatically.
NUM_JOBS = 20
# 2) Machine configuration.
TOTAL_MACHINES_GLOBAL = 36
MIN_MACHINES_PER_OP = 1
MAX_MACHINES_PER_OP = 4

# 3) Truncated Gaussian perturbation applied to nominal processing times.
#    DEVIATION_RATIO = 0.40 limits samples to +/-40% of the nominal value.
DEVIATION_RATIO = 0.40

# 4) Input process-table file.
CASE_INFO_PATH = r"./case_info_matched_to_case_total.txt"

# 5) Output directory. Key generation parameters are included in the filename.
OUTPUT_DIR = r"./case-analysis"

# 6) Whether to include the special start/end milestones from the source table.
#    True: include 107 numbered operations and three special milestones.
#    False: retain only the 107 numbered physical operations.
INCLUDE_SPECIAL_NODES = False

# 7) Whether to write metadata comments for downstream instance readers.
WRITE_METADATA_COMMENTS = True


# Output filename construction
def format_ratio_for_filename(x: float) -> str:
    """Convert a decimal ratio to the compact tag used in output filenames.

    Examples:

    0.40 -> 40pct
    0.25 -> 25pct
    0.333 -> 33p3pct
    """
    pct = x * 100
    if abs(pct - round(pct)) < 1e-9:
        return f"{int(round(pct))}pct"
    s = f"{pct:.3f}".rstrip("0").rstrip(".").replace(".", "p")
    return f"{s}pct"


def build_output_filename(
    output_dir: str,
    num_jobs: int,
    max_machines_per_op: int,
    deviation_ratio: float,
    include_special_nodes: bool,
) -> str:
    special_tag = "withSpecial" if include_special_nodes else "noSpecial"
    dev_tag = format_ratio_for_filename(deviation_ratio)
    filename = (
        f"Generated_Case_"
        f"J{num_jobs}_"
        f"MaxM{max_machines_per_op}_"
        f"Dev{dev_tag}_"
        f"{special_tag}.txt"
    )
    return str(Path(output_dir) / filename)


# Processing-time parsing
def parse_time_to_minutes(time_str: str) -> int:
    """Convert a processing-time string to an integer number of minutes.

    Supported examples include ``180 min/train``, ``2.5 h/wheelset``,
    ``30-60 min/bogie`` (converted to the mean, 45), ``15/20/25 min/item``
    (converted to the mean, 20), and ``0``.
    """
    s = time_str.strip()
    if s in {"", "—", "-"}:
        return 0

    s = s.replace("–", "-").replace("—", "-").replace("−", "-")
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", s)]
    if not nums:
        raise ValueError(f"Unable to parse processing-time field: {time_str}")

    # Use the arithmetic mean for ranges or multiple alternatives so that each
    # operation has one nominal processing time.
    value = sum(nums) / len(nums)

    # Convert hours to minutes when "h" appears as a standalone unit.
    if re.search(r"\bh\b", s):
        value *= 60

    return int(round(value))


# Process-table loading and single-job template construction
def load_process_template_from_table(txt_path: str, include_special_nodes: bool = True):
    """Load a process template from a seven-column Markdown table.

    Returns the nominal time of each local operation, the zero-based DAG
    precedence arcs, the operation count, and the source rows used to build
    the template.
    """
    text = Path(txt_path).read_text(encoding="utf-8")

    raw_rows = []
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue

        parts = [p.strip() for p in line.strip().split("|")[1:-1]]
        if len(parts) != 7:
            continue

        # Skip the table header and Markdown separator row.
        if parts[0] == "No." or set(parts[0]) == {"-"}:
            continue

        raw_rows.append({
            "no": parts[0],
            "cn": parts[1],
            "en": parts[2],
            "time": parts[3],
            "pred": parts[4],
            "succ": parts[5],
            "note": parts[6],
        })

    numeric_rows = [r for r in raw_rows if r["no"].isdigit()]
    special_rows = [r for r in raw_rows if not r["no"].isdigit()]

    if not numeric_rows:
        raise ValueError("No numbered operations were found in the input table.")

    # 1. Build node-to-row lookup tables.
    max_numeric_id = max(int(r["no"]) for r in numeric_rows)

    id_to_row = {}
    name_to_id = {}

    for r in numeric_rows:
        nid = int(r["no"])
        id_to_row[nid] = r
        name_to_id[r["cn"]] = nid
        name_to_id[r["en"]] = nid

    if include_special_nodes:
        next_id = max_numeric_id + 1
        for r in special_rows:
            nid = next_id
            next_id += 1
            row = dict(r)
            row["assigned_id"] = nid
            id_to_row[nid] = row
            name_to_id[row["cn"]] = nid
            name_to_id[row["en"]] = nid

    # Sort source node identifiers and map them to zero-based local indices.
    node_ids_sorted = sorted(id_to_row.keys())
    local_index = {nid: i for i, nid in enumerate(node_ids_sorted)}

    # 2. Build the nominal processing-time vector.
    base_times = []
    for nid in node_ids_sorted:
        t = parse_time_to_minutes(id_to_row[nid]["time"])
        base_times.append(t)

    # 3. Build precedence arcs from the Predecessors column.
    dag_connections_0based = []
    skipped_special_preds = []

    for nid in node_ids_sorted:
        pred_str = id_to_row[nid]["pred"]

        if pred_str in {"", "—", "-"}:
            continue

        pred_tokens = [t.strip() for t in re.split(r"[，,]", pred_str) if t.strip()]
        for token in pred_tokens:
            # Numbered predecessor.
            if token.isdigit():
                pred_id = int(token)
                if pred_id in id_to_row:
                    dag_connections_0based.append((local_index[pred_id], local_index[nid]))
                continue

            # Named special milestone, using either language column.
            if token in name_to_id:
                pred_id = name_to_id[token]
                if pred_id in id_to_row:
                    dag_connections_0based.append((local_index[pred_id], local_index[nid]))
                continue

            # Unresolved names normally correspond to excluded special
            # milestones when include_special_nodes is False.
            skipped_special_preds.append((nid, token))

    ops_per_job = len(node_ids_sorted)

    return {
        "ops_per_job": ops_per_job,
        "base_times": base_times,
        "dag_connections_0based": dag_connections_0based,
        "node_ids_sorted": node_ids_sorted,
        "skipped_special_preds": skipped_special_preds,
        "id_to_row": id_to_row,
    }


# Processing-time sampling
def generate_processing_time(mean_time: int, deviation_ratio: float = DEVIATION_RATIO) -> int:
    """Sample an integer processing time from a truncated Gaussian.

    ``deviation_ratio=0.40`` constrains the sample to +/-40% of
    ``mean_time``.
    """
    if mean_time == 0:
        return 0

    limit = deviation_ratio * mean_time
    sigma = limit / 3.0  # Three-sigma truncation interval.

    while True:
        val = random.gauss(mean_time, sigma)
        if (mean_time - limit) <= val <= (mean_time + limit):
            return max(1, int(round(val)))


# Instance generation
template = load_process_template_from_table(
    CASE_INFO_PATH,
    include_special_nodes=INCLUDE_SPECIAL_NODES
)

OPS_PER_JOB = template["ops_per_job"]
base_times = template["base_times"]
dag_connections_0based = template["dag_connections_0based"]

FILENAME = build_output_filename(
    output_dir=OUTPUT_DIR,
    num_jobs=NUM_JOBS,
    max_machines_per_op=MAX_MACHINES_PER_OP,
    deviation_ratio=DEVIATION_RATIO,
    include_special_nodes=INCLUDE_SPECIAL_NODES
)

full_arcs = []
full_ops_info = []

total_ops_count = NUM_JOBS * OPS_PER_JOB

print("=" * 80)
print("Process template loaded")
print(f"Source file: {CASE_INFO_PATH}")
print(f"INCLUDE_SPECIAL_NODES = {INCLUDE_SPECIAL_NODES}")
print(f"DEVIATION_RATIO = {DEVIATION_RATIO:.2f}")
print(f"MAX_MACHINES_PER_OP = {MAX_MACHINES_PER_OP}")
print(f"Output file: {FILENAME}")
print(f"Operations per job (OPS_PER_JOB) = {OPS_PER_JOB}")
print(f"Total operation count = {total_ops_count}")
print(f"Precedence arcs per job = {len(dag_connections_0based)}")
if template["skipped_special_preds"]:
    print("Predecessors omitted from the current template (normally excluded special milestones):")
    for item in template["skipped_special_preds"]:
        print("  ", item)
print("=" * 80)

for job_id in range(NUM_JOBS):
    offset = job_id * OPS_PER_JOB

    # 1. Replicate the precedence structure for this job.
    for u_local, v_local in dag_connections_0based:
        full_arcs.append((u_local + offset, v_local + offset))

    # 2. Sample compatible machines and processing times for each operation.
    for local_op_id in range(OPS_PER_JOB):
        base_t = base_times[local_op_id]

        # Represent a zero-duration merge or special milestone with one fixed
        # machine and a processing time of zero.
        if base_t == 0:
            full_ops_info.append("1 0 0")
            continue

        num_valid_machines = random.randint(MIN_MACHINES_PER_OP, MAX_MACHINES_PER_OP)
        selected_machines = random.sample(range(TOTAL_MACHINES_GLOBAL), num_valid_machines)
        selected_machines.sort()

        op_str_parts = [str(num_valid_machines)]
        for m_id in selected_machines:
            p_time = generate_processing_time(base_t, deviation_ratio=DEVIATION_RATIO)
            op_str_parts.append(str(m_id))
            op_str_parts.append(str(p_time))

        full_ops_info.append(" ".join(op_str_parts))


# Instance serialization
with open(FILENAME, "w", encoding="utf-8") as f:
    if WRITE_METADATA_COMMENTS:
        f.write(f"# Number of jobs: {NUM_JOBS}\n")
        f.write(f"# Number of operations for each job: {OPS_PER_JOB}\n")
        f.write(f"# Number of machines: {TOTAL_MACHINES_GLOBAL}\n")
        f.write(f"# Number of possible machines per operation: {MAX_MACHINES_PER_OP}\n")
        f.write(f"# Deviation ratio: {DEVIATION_RATIO:.4f}\n")

    header = f"{total_ops_count} {len(full_arcs)} {TOTAL_MACHINES_GLOBAL}"
    f.write(header + "\n")

    for u, v in full_arcs:
        f.write(f"{u} {v}\n")

    for op_line in full_ops_info:
        f.write(op_line + "\n")

print(f"Generation complete. Instance saved to: {FILENAME}")
print(f"Instance header: {header}")
