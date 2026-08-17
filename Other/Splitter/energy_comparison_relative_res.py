import matplotlib.pyplot as plt
import math

N = 30000  # počet událostí v každém histogramu

x, mean, stddev = [], [], []
with open("energy_data_mean", "r") as f:
    for line in f:
        if line.strip():
            parts = line.strip().split()
            if len(parts) == 3:
                x.append(int(parts[0]))
                mean.append(float(parts[1]))
                stddev.append(float(parts[2]))

# Relativní rozlišení R = sigma / mean
ratio = [s / m if m != 0 else 0 for s, m in zip(stddev, mean)]

# Nejistoty:
sigma_err = [s / math.sqrt(2 * N) for s in stddev]   # Δσ
mean_err = [s / math.sqrt(N) for s in stddev]        # Δ<E>

# Propagace nejistoty ΔR
# Propagace nejistoty ΔR
ratio_error = []
for s, m, ds, dm in zip(stddev, mean, sigma_err, mean_err):
    if m != 0 and s != 0:
        r = s / m
        dr = r * math.sqrt((ds / s) ** 2 + (dm / m) ** 2)
        ratio_error.append(5 * dr)  # 🔹 zvětšení chyb 5× pro vizualizaci
    else:
        ratio_error.append(0)

# Průměrný poměr
avg_ratio = sum(ratio) / len(ratio)

# Top 19 (jako dřív)
sorted_indices = sorted(range(len(mean)), key=lambda i: mean[i], reverse=True)
top_indices = sorted_indices[:19]

plt.figure(figsize=(10, 6))

# Body s error bary
plt.errorbar(
    x, ratio, yerr=ratio_error, fmt='o', ecolor='gray', elinewidth=1,
    capsize=3, color='blue', alpha=0.6, markersize=4,
    label='σ/⟨E⟩ ± 5*propagated error'
)

# Zvýrazni top 19
plt.scatter(
    [x[i] for i in top_indices],
    [ratio[i] for i in top_indices],
    color='black', s=30, label='Top 19'
)

# Průměrná hodnota
plt.axhline(
    y=avg_ratio, color='red', linestyle='--', linewidth=2,
    label=f'Average ratio = {avg_ratio:.3f}'
)

plt.title("Relative energy uncertainty (σ / ⟨E⟩) with propagated error", fontsize=14)
plt.xlabel("Splitter output n.", fontsize=12)
plt.ylabel("σ / ⟨E⟩", fontsize=12)
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend()
plt.tight_layout()
plt.savefig("Energy_relative_uncertainty_with_propagated_error.png", dpi=180)
plt.show()

