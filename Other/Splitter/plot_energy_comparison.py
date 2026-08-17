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


def get_most_populated_bin_value(energy_values, bins=300, threshold=0.2):
    """
    Find the center of the most populated histogram bin for values
    above the specified x-value threshold.
    """

    # Keep only values above the threshold
    filtered_values = np.array(energy_values)
    filtered_values = filtered_values[filtered_values > threshold]

    if len(filtered_values) == 0:
        return np.nan

    # Create histogram
    counts, bin_edges = np.histogram(filtered_values, bins=bins)

    # Find the most populated bin
    most_populated_bin = np.argmax(counts)

    # Return the center of that bin
    bin_center = (
        bin_edges[most_populated_bin] +
        bin_edges[most_populated_bin + 1]
    ) / 2

    return bin_center


def plot_multiple_energy_histograms(parent_directory):
    all_measurements = {}

    # Loop over directories like out1, out2, out3, ...
    for folder in os.listdir(parent_directory):
        folder_path = os.path.join(parent_directory, folder)

        if os.path.isdir(folder_path) and folder.startswith("out"):
            root_file_path = os.path.join(folder_path, "pulses.root")

            if os.path.exists(root_file_path):
                energy_values = get_energy_values(root_file_path)
                all_measurements[folder] = energy_values

    if not all_measurements:
        print("No valid measurements found.")
        return

    # Determine global min/max for consistent binning
    all_values = np.concatenate(list(all_measurements.values()))
    min_energy = np.min(all_values)
    max_energy = np.max(all_values)
    bins = 150

    plt.figure(figsize=(10, 6))

    for label, energy_values in sorted(all_measurements.items()):
        # Find the most populated bin above x = 0.2
        mean_energy = get_most_populated_bin_value(
            energy_values,
            bins=bins,
            threshold=0.2
        )

        stddev_energy = np.std(energy_values)

        plt.hist(
            energy_values,
            bins=bins,
            range=(min_energy, max_energy),
            histtype='step',
            linewidth=1.5,
            label=f"{label} (μ={mean_energy:.2f})"
        )

    # Axis labels
    plt.xlabel("Energy", fontsize=14)
    plt.ylabel("Count", fontsize=14)

    # Tick labels
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)

    # Logarithmic y-axis
    plt.yscale('log')

    # Avoid log(0) issues
    plt.ylim(bottom=0.5)

    # Legend: 2 columns
    plt.legend(
        fontsize=12,
        ncol=2
    )

    plt.grid(visible=True, linestyle=':', linewidth=0.5)
    plt.tight_layout()

    png_path = os.path.join(parent_directory, "Energy_comparison.png")
    pdf_path = os.path.join(parent_directory, "Energy_comparison.pdf")

    plt.savefig(png_path, dpi=150, bbox_inches='tight')
    plt.savefig(pdf_path, bbox_inches='tight')

    plt.show()


# Run on current directory (where outX folders exist)
parent_directory = os.getcwd()
plot_multiple_energy_histograms(parent_directory)
