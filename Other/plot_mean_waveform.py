#!/usr/bin/env python3

import os
import glob
import ROOT
import numpy as np
import matplotlib.pyplot as plt


def mean_waveform_from_th2(th2):
    """
    Reconstruct mean waveform from TH2D heatmap.

    X axis = time
    Y axis = amplitude
    Bin content = occupancy
    """

    nx = th2.GetNbinsX()
    ny = th2.GetNbinsY()

    xvals = np.zeros(nx)
    meanvals = np.full(nx, np.nan)

    for ix in range(1, nx + 1):

        xvals[ix - 1] = th2.GetXaxis().GetBinCenter(ix)

        sumw = 0.0
        sumwy = 0.0

        for iy in range(1, ny + 1):

            w = th2.GetBinContent(ix, iy)

            if w == 0:
                continue

            y = th2.GetYaxis().GetBinCenter(iy)

            sumw += w
            sumwy += w * y

        if sumw > 0:
            meanvals[ix - 1] = sumwy / sumw

    return xvals, meanvals


def calculate_fwhm(x, y):
    """
    Calculate FWHM for a positive pulse.
    Returns FWHM in same units as x.
    """

    valid = np.isfinite(y)

    x = x[valid]
    y = y[valid]

    if len(y) < 3:
        return np.nan, np.nan, np.nan, np.nan

    peak_idx = np.argmax(y)
    peak = y[peak_idx]

    half_level = peak / 2.0

    # Left crossing
    t_left = np.nan

    for i in range(peak_idx, 0, -1):

        if y[i] >= half_level and y[i - 1] < half_level:

            t_left = (
                x[i - 1]
                + (half_level - y[i - 1])
                * (x[i] - x[i - 1])
                / (y[i] - y[i - 1])
            )

            break

    # Right crossing
    t_right = np.nan

    for i in range(peak_idx, len(y) - 1):

        if y[i] >= half_level and y[i + 1] < half_level:

            t_right = (
                x[i]
                + (half_level - y[i])
                * (x[i + 1] - x[i])
                / (y[i + 1] - y[i])
            )

            break

    if np.isnan(t_left) or np.isnan(t_right):
        return np.nan, t_left, t_right, half_level

    return t_right - t_left, t_left, t_right, half_level


plt.figure(figsize=(10, 6))

dirs = sorted(
    d for d in glob.glob("S*")
    if os.path.isdir(d)
)

print("\nFWHM results:")
print("-" * 50)

for d in dirs:

    rootfile = os.path.join(d, "pulses.root")

    if not os.path.exists(rootfile):
        print(f"Missing: {rootfile}")
        continue

    f = ROOT.TFile.Open(rootfile)

    if not f or f.IsZombie():
        print(f"Cannot open: {rootfile}")
        continue

    th2 = f.Get("singlephotons/wfm_Stack")

    if not th2:
        print(f"Missing histogram in {d}")
        f.Close()
        continue

    x, y = mean_waveform_from_th2(th2)

    # Convert seconds -> nanoseconds
    x = x * 1e9

    # Calculate FWHM
    fwhm, t_left, t_right, half_level = calculate_fwhm(x, y)

    print(
        f"{d:20s} "
        f"FWHM = {fwhm:8.3f} ns"
    )

    plt.plot(
        x,
        y,
        lw=2,
        label=f"{d} (FWHM = {fwhm:.2f} ns)"
    )

    # Optional: draw FWHM markers
    if np.isfinite(fwhm):
        plt.hlines(
            half_level,
            t_left,
            t_right,
            linestyle="--",
            alpha=0.3
        )

    f.Close()

print("-" * 50)

plt.xlabel("Time [ns]")
plt.ylabel("Voltage [V]")
plt.title("Mean waveforms from PMTAF pulses.root wfm_Stack, 1000V")
plt.grid(True, alpha=0.3)
plt.legend(fontsize=8)
plt.tight_layout()

plt.savefig("mean_waveforms.png", dpi=100)

print("\nSaved: mean_waveforms.png\n")

plt.show()
