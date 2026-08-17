import ROOT
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# ==========================================
# Open ROOT file
# ==========================================

filename = "sp.root"

f = ROOT.TFile.Open(filename)

if not f or f.IsZombie():
    print("Cannot open file.")
    exit()

tree = f.Get("pmtaf_pulses")


# ==========================================
# CFD calculations
# ==========================================

cfd_levels = [0.1, 0.2, 0.3, 0.4, 0.5]

t_values = {cfd: [] for cfd in cfd_levels}

threshold = 0.050 #50mV
bin_width = 0.025 #25ps

for event in tree:

    t = np.array(list(event.t))
    x = np.array(list(event.x))

    if len(x) < 2:
        continue

    y = x - threshold

    peak_index = np.argmax(y)
    peak = y[peak_index]

    if peak <= 0:
        continue

    for cfd in cfd_levels:

        level = cfd * peak
        tcfd = np.nan

        for i in range(peak_index):

            if y[i] < level and y[i+1] >= level:

                tcfd = (
                    t[i]
                    + (level - y[i])
                    * (t[i+1] - t[i])
                    / (y[i+1] - y[i])
                )

                break

        if not np.isnan(tcfd):
            t_values[cfd].append(tcfd * 1e9)   # convert immediately to ns

colors = {
    0.1: "tab:blue",
    0.2: "tab:orange",
    0.3: "tab:green",
    0.4: "tab:red",
    0.5: "tab:purple"
}

plt.figure(figsize=(9,6))

legend_handles = []

for cfd in cfd_levels:

    data = np.array(t_values[cfd])

    if len(data) < 2:
        continue

    hist_min = data.min()
    hist_max = data.max()

    nbins = int((hist_max - hist_min) / bin_width)

    counts, bins = np.histogram(
        data,
        bins=nbins,
        range=(hist_min, hist_max)
    )

    centers = (bins[:-1] + bins[1:]) / 2

    peak_bin = np.argmax(counts)
    half_max = counts[peak_bin] / 2

    # Left crossing
    left = peak_bin
    while left > 0 and counts[left] > half_max:
        left -= 1

    x_left = np.interp(
        half_max,
        [counts[left], counts[left+1]],
        [centers[left], centers[left+1]]
    )

    # Right crossing
    right = peak_bin
    while right < len(counts)-1 and counts[right] > half_max:
        right += 1

    x_right = np.interp(
        half_max,
        [counts[right], counts[right-1]],
        [centers[right], centers[right-1]]
    )

    fwhm = x_right - x_left

    print(f"CFD{int(cfd*100):2d}:")
    print(f"   Events = {len(data)}")
    print(f"   Peak   = {centers[peak_bin]:.3f} ns")
    print(f"   FWHM   = {fwhm:.3f} ns")

    plt.hist(
        data,
        bins=nbins,
        histtype="step",
        linewidth=2,
        color=colors[cfd],
        label=f"CFD{int(cfd*100)}, FWHM=({fwhm:.3f} ns)"
    )

plt.xlabel("CFD time [ns]")
plt.ylabel("Counts")
plt.title("Timing distributions for different CFD fractions")

plt.grid(True)

legend_text = (
    f"Amplitude threshold = {threshold*1000:.1f} mV\n"
    f"Bin width = {bin_width:.3f} ns"
)

info = Patch(visible=False, label=legend_text)

handles, labels = plt.gca().get_legend_handles_labels()
handles.append(info)

plt.legend(handles=handles)

plt.tight_layout()

plt.savefig("CFD_comparison.png", dpi=150, bbox_inches="tight")
plt.savefig("CFD_comparison.pdf", bbox_inches="tight")

plt.show()
