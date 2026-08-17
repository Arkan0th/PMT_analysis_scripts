import ROOT
import os
import matplotlib.pyplot as plt
import numpy as np

def get_energy_values(root_file_path):
    root_file = ROOT.TFile(root_file_path)
    tree = root_file.Get("singlephotons/pmtaf_tree")

    energy_values = []
    for event in tree:
        energy_values.append(event.energy)

    root_file.Close()
    return energy_values


def plot_multiple_energy_histograms(parent_directory):
    all_measurements = {}

    # Loop over directories like out1, out2, out3, ...
    for folder in os.listdir(parent_directory):
        folder_path = os.path.join(parent_directory, folder)

        if os.path.isdir(folder_path) and folder.startswith("out"):
            root_file_path = os.path.join(folder_path, "pulses.root")

            if os.path.exists(root_file_path):
                energy_values = np.array(get_energy_values(root_file_path))

                # Remove all values < 0.1
                energy_values = energy_values[energy_values >= 0.1]

                if len(energy_values) > 0:
                    all_measurements[folder] = energy_values

    if not all_measurements:
        print("No valid measurements found after filtering x < 0.1.")
        return

    # Determine global min/max for consistent binning
    all_values = np.concatenate(list(all_measurements.values()))
    min_energy = np.min(all_values)
    max_energy = np.max(all_values)
    bins = 150

    plt.figure(figsize=(16, 9))

    for label, energy_values in sorted(all_measurements.items()):
        mean_energy = np.mean(energy_values)
        stddev_energy = np.std(energy_values)

        plt.hist(
            energy_values,
            bins=bins,
            range=(min_energy, max_energy),
            histtype='step',
            linewidth=1.5,
            label=f"{label} (μ={mean_energy:.2f}, σ={stddev_energy:.2f})"
        )

    plt.xlabel("Energy")
    plt.ylabel("#")
    plt.title("Energy comparison, 0.1 cut")

    # Optional log scale
    # plt.yscale('log')
    plt.ylim(bottom=0.5)

    plt.legend()
    plt.grid(visible=True, linestyle=':', linewidth=0.5)
    plt.tight_layout()

    output_path = os.path.join(parent_directory, "Energy_comparison_0.1cut.png")
    plt.savefig(output_path, dpi=120)
    plt.show()


# Run on current directory (where outX folders exist)
parent_directory = os.getcwd()
plot_multiple_energy_histograms(parent_directory)
