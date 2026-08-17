#!/usr/bin/env python3

import json
import csv
import sys
from pathlib import Path
from datetime import datetime

CHANNELS = [1,2,3,4,5,6]

if len(sys.argv) != 3:
    print("Usage:")
    print("python json_to_csv.py input.json output.csv")
    sys.exit(1)

input_file = Path(sys.argv[1])
output_file = Path(sys.argv[2])

with open(input_file) as f:
    data = json.load(f)

log = data["tests"]["dark_run"]["mon_log"]

t0 = datetime.fromisoformat(log[0]["timestamp"])

with open(output_file, "w", newline="") as f:

    writer = csv.writer(f)

    writer.writerow(
        ["timestamp", "elapsed_seconds"] +
        [f"CH{i}_rate_Hz" for i in CHANNELS]
    )

    for entry in log:

        t = datetime.fromisoformat(entry["timestamp"])

        elapsed = (t - t0).total_seconds()

        row = [
            entry["timestamp"],
            elapsed
        ]

        for ch in CHANNELS:

            row.append(
                entry["channels"]
                .get(str(ch), {})
                .get("r_mon", "")
            )

        writer.writerow(row)

print(output_file)
