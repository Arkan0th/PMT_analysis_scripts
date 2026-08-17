import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
import math

x, mean, stddev = [], [], []
with open("energy_data_mean", "r") as f:
    for line in f:
        if line.strip():
            parts = line.strip().split()
            if len(parts) == 3:
                x.append(int(parts[0]))
                mean.append(float(parts[1]))
                stddev.append(float(parts[2]))

n_events = 30000
mean_error = [5*s / math.sqrt(n_events) for s in stddev]

avg_energy = sum(mean) / len(mean)

sorted_indices = sorted(range(len(mean)), key=lambda i: mean[i], reverse=True)
top_indices = sorted_indices[:19]

plt.figure(figsize=(10, 6))

# Vykresli všechny body s chybami
plt.errorbar(
    x, mean, yerr=mean_error, fmt='o', ecolor='gray', elinewidth=1,
    capsize=2, color='blue', alpha=0.5, markersize=4, label='Mean ± 5*error'
)

# Zvýrazni top 19 bodů (menší, ale kontrastnější)
plt.scatter(
    [x[i] for i in top_indices],
    [mean[i] for i in top_indices],
    color='black', s=25, linewidths=0.6, label='Top 19'
)

# Průměrná energie (vodorovná čára)
plt.axhline(
    y=avg_energy, color='red', linestyle='--', linewidth=2,
    label=f'Average = {avg_energy:.2f}'
)

plt.title("Splitter out energy comparison", fontsize=14)
plt.xlabel("Splitter out n.", fontsize=12)
plt.ylabel("Mean energy", fontsize=12)
plt.grid(True, which='both', linestyle='--', alpha=0.6)
plt.legend()
plt.tight_layout()
plt.savefig("Energy_comparison.png", dpi=180)
plt.show()

