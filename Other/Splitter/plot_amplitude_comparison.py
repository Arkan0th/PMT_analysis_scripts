import ROOT
import os
import matplotlib.pyplot as plt
import numpy as np

def get_amplitude_values(root_file_path):
    root_file = ROOT.TFile(root_file_path)
    tree = root_file.Get("singlephotons/pmtaf_tree")

    amplitude_values = []
    for event in tree:
        amplitude_values.append(event.amplitude_V * 1000.0)  # <-- convert to mV

    root_file.Close()
    return np.array(amplitude_values)


def plot_amplitude_histograms(parent_directory):
    plt.figure(figsize=(16, 9))

    measurements = {}

    # Collect data from outX folders
    for folder in os.listdir(parent_directory):
        folder_path = os.path.join(parent_directory, folder)

        if os.path.isdir(folder_path) and folder.startswith("out"):
            root_file_path = os.path.join(folder_path, "pulses.root")

            if os.path.exists(root_file_path):
                amplitude_values = get_amplitude_values(root_file_path)
                measurements[folder] = amplitude_values

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

    # Plot raw counts
    for label, amplitude_values in sorted(measurements.items()):
        plt.hist(
            amplitude_values,
            bins=bin_edges,
            histtype='step',
            linewidth=1.5,
            label=f"{label}"
        )

    plt.xlabel("Amplitude [mV]")   # updated unit
    plt.ylabel("#")
    plt.title("Amplitude comparison")

    plt.xlim(min_val, max_val)

    plt.legend()
    plt.grid(visible=True, linestyle=':', linewidth=0.5)
    plt.tight_layout()

    plt.savefig(os.path.join(parent_directory, "Amplitude_comparison.png"), dpi=120)

    plt.show()
    plt.close()


# Run in current directory
parent_directory = os.getcwd()
plot_amplitude_histograms(parent_directory)
