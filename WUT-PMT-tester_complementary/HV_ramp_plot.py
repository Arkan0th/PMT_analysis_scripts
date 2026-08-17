import csv
import matplotlib.pyplot as plt

# ==========================
# Read CSV
# ==========================
csv_file = "hv_ramp_20260702_104542.csv"

# Dictionary to store data by channel
data = {}

with open(csv_file, "r", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        ch = int(row["channel"])

        if ch not in data:
            data[ch] = {
                "hv_set": [],
                "hv_meas": [],
                "current": []
            }

        data[ch]["hv_set"].append(float(row["voltage_set"]))
        data[ch]["hv_meas"].append(float(row["voltage"]))
        data[ch]["current"].append(float(row["current"]))

# ==========================
# Plot (3 columns × 2 rows)
# ==========================
fig, axes = plt.subplots(2, 3, figsize=(13, 7), constrained_layout=True)
axes = axes.flatten()

channels = sorted(data.keys())

for i, ch in enumerate(channels):

    ax = axes[i]

    hv_set = data[ch]["hv_set"]
    hv_meas = data[ch]["hv_meas"]
    current = data[ch]["current"]

    # Calculate maximum voltage difference
    delta_v = max(abs(m - s) for m, s in zip(hv_meas, hv_set))

    # Left axis
    ax.plot(
        hv_set,
        hv_meas,
        's-',
        color='tab:blue',
        markersize=4,
        linewidth=1.5
    )

    ax.set_xlabel("HV Set [V]")
    ax.set_ylabel("Measured HV [V]", color='tab:blue')
    ax.tick_params(axis='y', labelcolor='tab:blue')
    ax.grid(True, linestyle='--', alpha=0.75)


    # Right axis
    ax2 = ax.twinx()
    ax2.plot(
        hv_set,
        current,
        's-',
        color='tab:red',
        markersize=4,
        linewidth=1.5
    )

    ax2.set_ylabel("Current [µA]", color='tab:red')
    ax2.tick_params(axis='y', labelcolor='tab:red')

    ax.set_title(f"Ch {ch:02d} (ΔV={delta_v:.1f}V)", fontsize=10)

# Remove unused subplot(s) if fewer than 6 channels
for j in range(len(channels), len(axes)):
    fig.delaxes(axes[j])

plt.savefig("hv_ramp.png", dpi=300, bbox_inches="tight")
plt.savefig("hv_ramp.pdf", dpi=300, bbox_inches="tight")
plt.show()
