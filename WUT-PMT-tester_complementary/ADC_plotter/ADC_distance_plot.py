#!/usr/bin/env python3

import os
import re
import matplotlib.pyplot as plt


def main():

    # --------------------------------------------------
    # Read data
    # --------------------------------------------------

    channel_data = {ch: [] for ch in range(1, 7)}

    for dirname in sorted(os.listdir(".")):

        match = re.match(r"(\d+)cm$", dirname)
        if not match:
            continue

        distance = float(match.group(1))

        txt_path = os.path.join(dirname, "fit_parameters.txt")

        if not os.path.exists(txt_path):
            continue

        print(f"Reading {txt_path}")

        with open(txt_path, "r") as f:

            for line in f:

                line = line.strip()

                # skip header
                if not line or line.startswith("CH"):
                    continue

                parts = line.split()

                if len(parts) < 4:
                    continue

                ch = int(parts[0])
                mean = float(parts[2])   # Mean_corr
                sigma_mean = float(parts[3])
                sigma = float(parts[4])  # Sigma

                channel_data[ch].append({
                    "distance": distance,
                    "mean": mean,
                    "sigma_mean": sigma_mean,
                    "sigma": sigma,
                })

    # --------------------------------------------------
    # Normalize
    # --------------------------------------------------

    for ch in range(1, 7):

        if not channel_data[ch]:
            continue

        max_mean = max(d["mean"] for d in channel_data[ch])

        for d in channel_data[ch]:
            d["norm"] = d["mean"] / max_mean
            #d["norm_sigma"] = d["sigma"] / max_mean
            d["norm_sigma_mean"] = d["sigma_mean"] / max_mean

    # --------------------------------------------------
    # Determine common Y range
    # --------------------------------------------------

    global_min = float("inf")
    global_max = float("-inf")

    for ch in range(1, 7):
        for d in channel_data[ch]:

            #global_min = min(global_min, d["norm"] - d["norm_sigma"])
            #global_max = max(global_max, d["norm"] + d["norm_sigma"])

            global_min = min(global_min, d["norm"] - d["norm_sigma_mean"])
            global_max = max(global_max, d["norm"] + d["norm_sigma_mean"])

    padding = 0.05 * (global_max - global_min)

    ymin = global_min - padding
    ymax = global_max + padding

    # --------------------------------------------------
    # Plot settings
    # --------------------------------------------------

    plt.rcParams["font.size"] = 11
    plt.rcParams["axes.labelsize"] = 11
    plt.rcParams["axes.titlesize"] = 13

    colors = [
        "tab:blue",
        "tab:orange",
        "tab:green",
        "tab:red",
        "tab:purple",
        "tab:brown",
    ]

    fig, axes = plt.subplots(
        2, 3,
        figsize=(16, 9),
        constrained_layout=True
    )

    axes = axes.flatten()

    # --------------------------------------------------
    # Plot channels
    # --------------------------------------------------

    for ch in range(1, 7):

        ax = axes[ch - 1]

        data = sorted(channel_data[ch], key=lambda d: d["distance"])

        if not data:
            continue

        x = [d["distance"] for d in data]
        y = [d["norm"] for d in data]
        #yerr = [d["norm_sigma"] for d in data]
        yerr = [d["norm_sigma_mean"] for d in data]
        adc = [d["mean"] for d in data]

        color = colors[ch - 1]

        ax.errorbar(
            x, y,
            yerr=yerr,
            fmt="o-",
            color=color,
            linewidth=1.5,
            markersize=5,
            elinewidth=0.5,
            capsize=2,
            alpha=1,
        )

        for xx, yy, adc_val in zip(x, y, adc):
            ax.annotate(
                f"{adc_val:.2f}",
                (xx, yy),
                xytext=(15, 7.5),
                textcoords="offset points",
                ha="center",
                fontsize=6,
                alpha=0.8,
            )

        ax.set_title(f"CH{ch}")
        ax.set_xlabel("Distance [cm]")
        ax.set_ylabel("Normalized ADC")
        ax.set_ylim(ymin, ymax)

        ax.grid(True, linestyle="--", alpha=0.3)

    # --------------------------------------------------
    # Global title
    # --------------------------------------------------

    fig.suptitle(
        "ADC as a function of PMT-fiber distance",
        fontsize=16,
        fontweight="bold"
    )

    # --------------------------------------------------
    # Save figure
    # --------------------------------------------------

    outfile_png = "Final_ADC_distance_plot.png"
    outfile_pdf = "Final_ADC_distance_plot.pdf"

    plt.savefig(outfile_png, dpi=120, bbox_inches="tight")
    print(f"Saved {outfile_png}")
    plt.savefig(outfile_pdf, dpi=120, bbox_inches="tight")
    print(f"Saved {outfile_pdf}")

    plt.show()


if __name__ == "__main__":
    main()
