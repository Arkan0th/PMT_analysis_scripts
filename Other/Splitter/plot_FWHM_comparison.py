import ROOT
import os
import matplotlib.pyplot as plt
import numpy as np

def get_tot_values(root_file_path):
    root_file = ROOT.TFile(root_file_path)
    tree = root_file.Get("singlephotons/pmtaf_tree")

    tot_values = []
    for event in tree:
        tot_values.append(event.time_over_threshold_ns)

    root_file.Close()
    return np.array(tot_values)


def plot_time_over_threshold_histograms(parent_directory):
    plt.figure(figsize=(16, 9))   # same size as energy plot

    measurements = {}

    # Collect data from outX folders
    for folder in os.listdir(parent_directory):
        folder_path = os.path.join(parent_directory, folder)

        if os.path.isdir(folder_path) and folder.startswith("out"):
            root_file_path = os.path.join(folder_path, "pulses.root")

            if os.path.exists(root_file_path):
                tot_values = get_tot_values(root_file_path)
                measurements[folder] = tot_values

    if not measurements:
        print("No valid measurements found.")
        return

    print("Loaded measurements:", list(measurements.keys()))

    # Global binning
    all_values = np.concatenate(list(measurements.values()))
    min_val = np.min(all_values)
    max_val = np.max(all_values)
    bins = 80
    bin_edges = np.linspace(min_val, max_val, bins + 1)

    # Plot raw counts (no normalization)
    for label, tot_values in sorted(measurements.items()):
        plt.hist(
            tot_values,
            bins=bin_edges,
            histtype='step',
            linewidth=1.5,
            label=f"{label}"
        )

    plt.xlabel("Time over threshold [ns]")
    plt.ylabel("#")   # changed from "Normalized Probability"
    plt.title("Time over Threshold Distribution Comparison, FWHM")

    plt.xlim(min_val, max_val)

    plt.legend()
    plt.grid(visible=True, linestyle=':', linewidth=0.5)
    plt.tight_layout()

    plt.savefig(os.path.join(parent_directory, "FWHM_comparison.png"), dpi=120)

    plt.show()
    plt.close()


# Run in current directory
parent_directory = os.getcwd()
plot_time_over_threshold_histograms(parent_directory)
