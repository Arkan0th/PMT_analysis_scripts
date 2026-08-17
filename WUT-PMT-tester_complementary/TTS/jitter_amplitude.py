import ROOT
import numpy as np
import matplotlib.pyplot as plt
import math
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
# Settings
# ==========================================

threshold = 0.005       # 5 mV threshold
bin_width = 0.025         # ns


# amplitude intervals [mV]
amp_bins = [
    (0,49),
    (50,99),
    (100,149),
    (150,199),
    (200,249),
    (250,299),
    (300,349),
    (350,399),
    (400,449),
    (450,np.inf)
]


# storage
cfd_times = {}

for amp_range in amp_bins:
    cfd_times[amp_range] = []


# ==========================================
# Loop over events
# ==========================================

for event in tree:

    t = np.array(list(event.t))
    x = np.array(list(event.x))


    if len(x) < 2:
        continue


    # subtract fixed threshold
    y = x - threshold


    # peak amplitude
    peak_index = np.argmax(y)
    peak = y[peak_index]


    if peak <= 0:
        continue


    # convert amplitude to mV
    peak_mV = peak * 1000


    # find amplitude interval

    selected_bin = None

    for amp_range in cfd_times.keys():

        if amp_range[0] <= peak_mV < amp_range[1]:

            selected_bin = amp_range
            break


    if selected_bin is None:
        continue



    # ======================================
    # CFD50 calculation
    # ======================================

    cfd_level = 0.5 * peak

    t50 = np.nan


    for i in range(peak_index):

        if y[i] < cfd_level and y[i+1] >= cfd_level:


            t50 = (
                t[i]
                +
                (cfd_level-y[i])
                *
                (t[i+1]-t[i])
                /
                (y[i+1]-y[i])
            )

            break



    if not np.isnan(t50):

        cfd_times[selected_bin].append(
            t50*1e9
        )



# ==========================================
# Remove empty bins
# ==========================================

valid_bins = {}


for amp_range, values in cfd_times.items():

    if len(values) > 10:

        valid_bins[amp_range] = np.array(values)



print("\nAmplitude bins:")

for amp_range, values in valid_bins.items():

    print(
        amp_range,
        "mV :",
        len(values),
        "events"
    )



# ==========================================
# Plot CFD histograms
# ==========================================

nplots = len(valid_bins)

cols = 3
rows = math.ceil(nplots/cols)


fig, axes = plt.subplots(
    rows,
    cols,
    figsize=(15,4*rows)
)


axes = np.array(axes).reshape(-1)


fwhm_results = []
amp_labels = []
peak_positions = []


for ax, (amp_range, times) in zip(
        axes,
        valid_bins.items()
):


    hist_min = times.min()
    hist_max = times.max()


    nbins = max(
        10,
        int((hist_max-hist_min)/bin_width)
    )


    counts, bins = np.histogram(
        times,
        bins=nbins,
        range=(hist_min,hist_max)
    )


    centers = (
        bins[:-1]
        +
        bins[1:]
    )/2



    # ==================================
    # FWHM
    # ==================================

    peak_bin = np.argmax(counts)
    peak_position = centers[peak_bin]
    peak_positions.append(peak_position)

    half_max = counts[peak_bin]/2



    left = peak_bin

    while left > 0 and counts[left] > half_max:
        left -= 1



    right = peak_bin

    while right < len(counts)-1 and counts[right] > half_max:
        right += 1



    # interpolation

    if left+1 < len(counts):

        x_left = np.interp(
            half_max,
            [counts[left],counts[left+1]],
            [centers[left],centers[left+1]]
        )

    else:

        x_left = centers[left]



    if right-1 >= 0:

        x_right = np.interp(
            half_max,
            [counts[right],counts[right-1]],
            [centers[right],centers[right-1]]
        )

    else:

        x_right = centers[right]



    fwhm = x_right-x_left



    # save FWHM

    fwhm_results.append(fwhm)


    if amp_range[1] == np.inf:

        amp_labels.append("30+")

    else:

        amp_labels.append(
            f"{amp_range[0]}-{amp_range[1]}"
        )



    # ==================================
    # Histogram plot
    # ==================================

    ax.hist(
        times,
        bins=nbins,
        label="CFD50 distribution"
    )


    ax.axvline(
        x_left,
        linestyle="--"
    )
    
    
    ax.axvline(
        x_right,
        linestyle="--"
    )
    
    
    # legend information
    
    legend_text = (
        f"Peak position = {peak_position:.3f} ns\n"
        f"Amplitude = {amp_labels[-1]} mV\n"
        f"N_CFD events = {len(times)}\n"
        f"N_bins = {nbins}\n"
        f"Bin width = {bin_width:.3f} ns"
    )
    
    
    info = Patch(
        visible=False,
        label=legend_text
    )


    ax.legend(
        handles=[
            plt.Line2D(
                [],
                [],
                linestyle="--",
                label=f"FWHM = {fwhm:.3f} ns"
            ),
            info
        ],
        fontsize=9
    )


    title = (
        f"{amp_labels[-1]} mV\n"
        f"N={len(times)}"
    )


    ax.set_title(title)

    ax.set_xlabel(
        "CFD50 time [ns]"
    )

    ax.set_ylabel(
        "Counts"
    )

    ax.grid(True)



# remove empty axes

for ax in axes[nplots:]:

    ax.remove()



plt.tight_layout()

plt.savefig(
    "FWHM_vs_amplitude.png",
    dpi=150,
    bbox_inches="tight"
)

plt.savefig(
    "FWHM_vs_amplitude.pdf",
    bbox_inches="tight"
)

plt.show()


# ==========================================
# FWHM vs amplitude plot
# ==========================================

plt.figure(figsize=(8,5))


plt.plot(
    amp_labels,
    fwhm_results,
    marker="o"
)


plt.xlabel(
    "Pulse amplitude interval [mV]"
)


plt.ylabel(
    "CFD50 FWHM [ns]"
)


plt.title(
    "Timing resolution vs pulse amplitude"
)


plt.grid(True)



# write values on points

for i, value in enumerate(fwhm_results):
    plt.text(
        i,
        value + 0.01,
        f"{value:.3f}",
        ha="center",
        va="bottom"
    )

plt.tight_layout()

plt.savefig(
    "Timing_resolution_vs_pulse_amplitude.png",
    dpi=100,
    bbox_inches="tight"
)

plt.savefig(
    "Timing_resolution_vs_pulse_amplitude.pdf",
    bbox_inches="tight"
)

plt.show()


# ==========================================
# Peak position vs amplitude plot
# ==========================================

plt.figure(figsize=(8,5))

plt.plot(
    amp_labels,
    peak_positions,
    marker="o"
)

plt.xlabel(
    "Pulse amplitude interval [mV]"
)

plt.ylabel(
    "Peak position [ns]"
)

plt.title(
    "Peak position vs pulse amplitude"
)

plt.grid(True)

# write values on points
for i, value in enumerate(peak_positions):

    plt.text(
        i,
        value + 0.01,
        f"{value:.3f}",
        ha="center",
        va="bottom"
    )

plt.tight_layout()

plt.savefig(
    "Peak_position_vs_pulse_amplitude.png",
    dpi=100,
    bbox_inches="tight"
)

plt.savefig(
    "Peak_position_vs_pulse_amplitude.pdf",
    bbox_inches="tight"
)

plt.show()
