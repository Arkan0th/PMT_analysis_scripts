import ROOT
import numpy as np
import matplotlib.pyplot as plt

# ==========================================================
# Open ROOT file
# ==========================================================

filename = "sp.root"

f = ROOT.TFile.Open(filename)

if not f or f.IsZombie():
    print("Cannot open file:", filename)
    exit()

tree = f.Get("pmtaf_pulses")

if tree is None:
    print("Tree 'pmtaf_pulses' not found.")
    exit()


# ==========================================================
# Plot one waveform
# ==========================================================

def plot_waveform(event_number):

    tree.GetEntry(event_number)

    t = np.array(list(tree.t))
    x = np.array(list(tree.x))

    plt.figure(figsize=(10,5))
    plt.plot(t, x)

    plt.title(f"Waveform {event_number}")
    plt.xlabel("Time")
    plt.ylabel("Amplitude")
    plt.grid(True)

    plt.show()


# ==========================================================
# Plot many waveforms on one figure
# ==========================================================

def plot_all_waveforms(max_events=None):

    plt.figure(figsize=(10,6))

    n = tree.GetEntries()

    if max_events is None:
        max_events = n

    for i in range(min(max_events, n)):

        tree.GetEntry(i)

        t = np.array(list(tree.t))
        x = np.array(list(tree.x))

        plt.plot(t, x, linewidth=0.5, alpha=0.15)

    plt.title(f"{min(max_events,n)} waveforms")
    plt.xlabel("Time")
    plt.ylabel("Amplitude")
    plt.grid(True)

    plt.show()


# ==========================================================
# MAIN
# ==========================================================

print("Number of events:", tree.GetEntries())

# Plot first waveform
#plot_waveform(0)

# Plot first 100 waveforms together
#plot_all_waveforms(100)

# If you really want ALL 9960 waveforms, uncomment this:
plot_all_waveforms()
