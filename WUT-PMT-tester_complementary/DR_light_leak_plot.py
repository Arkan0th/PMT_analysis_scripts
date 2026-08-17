#!/usr/bin/env python3

import json
import re
from pathlib import Path
from datetime import datetime

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


# ============================================================
# CONFIGURATION
# ============================================================

# Directory containing this script
BASE_DIR = Path(__file__).resolve().parent

# Output files
OUTPUT_CSV = BASE_DIR / "dark_rates_merged.csv"
OUTPUT_PNG = BASE_DIR / "dark_rates.png"
OUTPUT_PDF = BASE_DIR / "dark_rates.pdf"

# Dark-rate threshold
THRESHOLD_HZ = 20000

# Channels
CHANNELS = [1, 2, 3, 4, 5, 6]


# ============================================================
# FIND TEST RESULT FILES
# ============================================================

def find_test_files():
    """
    Find test_results_*.json files inside DR_* directories.
    """

    tests = []

    test_directories = sorted(
        BASE_DIR.glob("*")
    )

    for test_dir in test_directories:

        if not test_dir.is_dir():
            continue

        result_files = sorted(
            test_dir.glob(
                "test_results_*.json"
            )
        )

        if not result_files:

            print(
                f"WARNING: No test_results_*.json "
                f"found in {test_dir.name}"
            )

            continue

        for result_file in result_files:

            timestamp = (
                get_timestamp_from_filename(
                    result_file
                )
            )

            if timestamp is None:

                print(
                    f"WARNING: Could not extract "
                    f"timestamp from {result_file.name}"
                )

                continue

            tests.append(
                {
                    "condition":
                        test_dir.name,

                    "file":
                        result_file,

                    "timestamp":
                        timestamp
                }
            )

    # Sort chronologically
    tests.sort(
        key=lambda x: x["timestamp"]
    )

    return tests


# ============================================================
# PARSE FILENAME TIMESTAMP
# ============================================================

def get_timestamp_from_filename(path):

    match = re.search(
        r"test_results_(\d{8})_(\d{6})\.json$",
        path.name
    )

    if not match:
        return None

    date_part = match.group(1)
    time_part = match.group(2)

    return datetime.strptime(
        date_part + time_part,
        "%Y%m%d%H%M%S"
    )


# ============================================================
# READ ONE JSON FILE
# ============================================================

def read_test_file(test):

    path = test["file"]
    condition = test["condition"]

    print(
        f"Reading {condition}: "
        f"{path.name}"
    )

    with open(
        path,
        "r"
    ) as f:

        data = json.load(f)

    dark_run = (
        data[
            "tests"
        ][
            "dark_run"
        ]
    )

    measurements = []

    for entry in dark_run["mon_log"]:

        timestamp = datetime.fromisoformat(
            entry["timestamp"]
        )

        rates = {}

        for channel in CHANNELS:

            channel_data = (
                entry[
                    "channels"
                ].get(
                    str(channel)
                )
            )

            if channel_data is None:

                rates[channel] = np.nan

            else:

                rates[channel] = (
                    channel_data.get(
                        "r_mon",
                        np.nan
                    )
                )

        measurements.append(
            {
                "timestamp":
                    timestamp,

                "condition":
                    condition,

                "source_file":
                    str(path),

                "rates":
                    rates
            }
        )

    return measurements


# ============================================================
# MERGE ALL TESTS
# ============================================================

def merge_all_tests(tests):

    all_measurements = []

    for test in tests:

        measurements = read_test_file(
            test
        )

        all_measurements.extend(
            measurements
        )

    if not all_measurements:

        raise RuntimeError(
            "No measurements found."
        )

    # Sort by real timestamp
    all_measurements.sort(
        key=lambda x: x["timestamp"]
    )

    # First measurement = t = 0
    start_time = (
        all_measurements[
            0
        ][
            "timestamp"
        ]
    )

    for measurement in all_measurements:

        measurement[
            "elapsed_seconds"
        ] = (
            measurement[
                "timestamp"
            ]
            - start_time
        ).total_seconds()

    return all_measurements


# ============================================================
# SAVE CSV
# ============================================================

def save_csv(
    measurements,
    output_file
):

    with open(
        output_file,
        "w"
    ) as f:

        header = [
            "timestamp",
            "elapsed_seconds",
            "condition"
        ]

        for channel in CHANNELS:

            header.append(
                f"CH{channel}_rate_Hz"
            )

        f.write(
            ",".join(header)
            + "\n"
        )

        for measurement in measurements:

            row = [
                measurement[
                    "timestamp"
                ].isoformat(),

                f"{measurement['elapsed_seconds']:.3f}",

                measurement[
                    "condition"
                ]
            ]

            for channel in CHANNELS:

                rate = (
                    measurement[
                        "rates"
                    ].get(
                        channel,
                        np.nan
                    )
                )

                if np.isfinite(rate):

                    row.append(
                        f"{rate:.6f}"
                    )

                else:

                    row.append("")

            f.write(
                ",".join(row)
                + "\n"
            )

    print()
    print(
        f"Merged CSV saved to:"
    )
    print(
        f"  {output_file}"
    )


# ============================================================
# FIND CONDITION BOUNDARIES
# ============================================================

def get_condition_boundaries(
    measurements
):

    conditions = []

    current_condition = None
    start_x = None
    end_x = None

    for measurement in measurements:

        condition = (
            measurement[
                "condition"
            ]
        )

        x = (
            measurement[
                "elapsed_seconds"
            ]
        )

        if condition != current_condition:

            # Save previous condition
            if current_condition is not None:

                conditions.append(
                    {
                        "condition":
                            current_condition,

                        "start":
                            start_x,

                        "end":
                            end_x
                    }
                )

            # New condition
            current_condition = condition
            start_x = x

        end_x = x

    # Save final condition
    if current_condition is not None:

        conditions.append(
            {
                "condition":
                    current_condition,

                "start":
                    start_x,

                "end":
                    end_x
            }
        )

    return conditions


# ============================================================
# LINEAR TREND
# ============================================================

def calculate_linear_trend(
    x,
    y
):

    x = np.asarray(x)
    y = np.asarray(y)

    valid = (
        np.isfinite(x)
        & np.isfinite(y)
    )

    if np.sum(valid) < 2:

        return (
            np.nan,
            np.full_like(
                x,
                np.nan,
                dtype=float
            )
        )

    slope_per_second, intercept = (
        np.polyfit(
            x[valid],
            y[valid],
            1
        )
    )

    # Convert Hz/s to Hz/hour
    slope_per_hour = (
        slope_per_second
        * 3600.0
    )

    fitted = (
        slope_per_second
        * x
        + intercept
    )

    return (
        slope_per_hour,
        fitted
    )


# ============================================================
# CREATE PLOT
# ============================================================

def make_plot(
    measurements,
    output_png,
    output_pdf
):

    # --------------------------------------------------------
    # Time axis
    # --------------------------------------------------------

    x = np.array(
        [
            m["elapsed_seconds"]
            for m in measurements
        ]
    )

    # --------------------------------------------------------
    # Condition boundaries
    # --------------------------------------------------------

    conditions = get_condition_boundaries(
        measurements
    )

    # --------------------------------------------------------
    # Get condition positions for labels
    # --------------------------------------------------------

    condition_centers = []

    for condition in conditions:

        center = (
            condition["start"]
            + condition["end"]
        ) / 2.0

        condition_centers.append(
            center
        )

    condition_names = [
        condition["condition"]
        for condition in conditions
    ]

    # --------------------------------------------------------
    # Create one figure / one axes
    # --------------------------------------------------------

    fig, ax = plt.subplots(
        figsize=(12, 8)
    )

    # --------------------------------------------------------
    # Plot all channels
    # --------------------------------------------------------

    for channel in CHANNELS:

        y = np.array(
            [
                m["rates"].get(
                    channel,
                    np.nan
                )
                for m in measurements
            ],
            dtype=float
        )

        ax.plot(
            x,
            y,
            linewidth=1.2,
            label=f"CH{channel:02d}"
        )

    # --------------------------------------------------------
    # Threshold
    # --------------------------------------------------------

    ax.axhline(
        THRESHOLD_HZ,
        color="red",
        linestyle="--",
        linewidth=1.8,
        #label=f"Threshold = {THRESHOLD_HZ} Hz"
    )

    # --------------------------------------------------------
    # Condition boundaries
    # --------------------------------------------------------

    for condition_index, condition in enumerate(
        conditions
    ):

        start = condition["start"]
        end = condition["end"]

        # Vertical separator
        if condition_index > 0:

            ax.axvline(
                start,
                color="black",
                linestyle=":",
                linewidth=1.2,
                alpha=0.7
            )

        # Condition label
        midpoint = (
            start + end
        ) / 2.0

    # --------------------------------------------------------
    # Labels
    # --------------------------------------------------------

    ax.set_xlabel(
        "Elapsed time [s]",
        fontsize=16
    )

    ax.set_ylabel(
        "Dark rate [Hz]",
        fontsize=16
    )
    
    ax.set_ylim(0, 15000)

    # --------------------------------------------------------
    # Grid
    # --------------------------------------------------------

    ax.grid(
        True,
        linestyle=":",
        alpha=0.5
    )

    # --------------------------------------------------------
    # Legend
    # --------------------------------------------------------

    ax.legend(
        loc="upper right",
        ncol=2,
        fontsize=14,
        frameon=True
    )

    # ========================================================
    # CONDITION NAMES ON TOP X-AXIS
    # ========================================================

    # Create a second x-axis
    ax_top = ax.twiny()

    # Keep exactly the same x limits
    ax_top.set_xlim(
        ax.get_xlim()
    )

    # Put one tick at the center of each test condition
    ax_top.set_xticks(
        condition_centers
    )

    # Use directory names as labels
    ax_top.set_xticklabels(
        condition_names,
        fontsize=14,
        fontweight="bold"
    )

    # Hide tick marks
    ax_top.tick_params(
        axis="x",
        length=0,
        pad=8
    )

    # --------------------------------------------------------
    # Layout
    # --------------------------------------------------------

    plt.tight_layout()

    # --------------------------------------------------------
    # Save PNG
    # --------------------------------------------------------

    plt.savefig(
        output_png,
        dpi=150,
        bbox_inches="tight"
    )

    print()
    print(
        f"PNG saved to:"
    )
    print(
        f"  {output_png}"
    )

    # --------------------------------------------------------
    # Save PDF
    # --------------------------------------------------------

    plt.savefig(
        output_pdf,
        format="pdf",
        bbox_inches="tight"
    )

    print()
    print(
        f"PDF saved to:"
    )
    print(
        f"  {output_pdf}"
    )

    # --------------------------------------------------------
    # Show
    # --------------------------------------------------------

    plt.show()

# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print(
        "=============================================="
    )

    print(
        " Dark Rate Multi-Test Analysis"
    )

    print(
        "=============================================="
    )

    print()
    print(
        "Base directory:"
    )

    print(
        f"  {BASE_DIR}"
    )

    # --------------------------------------------------------
    # Find tests
    # --------------------------------------------------------

    tests = find_test_files()

    if not tests:

        print()
        print(
            "ERROR: No test_results_*.json files found."
        )

        return

    print()
    print(
        f"Found {len(tests)} test runs:"
    )

    print()

    for i, test in enumerate(
        tests,
        start=1
    ):

        print(
            f"{i}. "
            f"{test['condition']}"
        )

        print(
            f"   {test['timestamp']}"
        )

        print(
            f"   {test['file']}"
        )

    # --------------------------------------------------------
    # Merge
    # --------------------------------------------------------

    measurements = (
        merge_all_tests(
            tests
        )
    )

    print()
    print(
        f"Total measurements: "
        f"{len(measurements)}"
    )

    # --------------------------------------------------------
    # Save CSV
    # --------------------------------------------------------

    save_csv(
        measurements,
        OUTPUT_CSV
    )

    # --------------------------------------------------------
    # Plot
    # --------------------------------------------------------

    make_plot(
        measurements,
        OUTPUT_PNG,
        OUTPUT_PDF
    )

    print()
    print(
        "=============================================="
    )

    print(
        " Done"
    )

    print(
        "=============================================="
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
