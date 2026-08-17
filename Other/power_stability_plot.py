import os
import re
import matplotlib.pyplot as plt

def parse_unit_in_brackets(text):
    match = re.search(r"\[(.*?)\]", text)
    return match.group(1) if match else None

def extract_number(text):
    match = re.search(r"([-+]?[0-9]*\.?[0-9]+)", text)
    return float(match.group(1)) if match else None

def parse_micro_value(text):
    text = text.replace("�", "µ").replace("u", "µ")
    match = re.search(r"([-+]?[0-9]*\.?[0-9]+)\s*([munpµ]?)W", text)
    if not match:
        return None
    value = float(match.group(1))
    prefix = match.group(2).lower()

    factor = {
        "": 1,
        "µ": 1e-6,
        "m": 1e-3,
        "n": 1e-9,
        "p": 1e-12,
    }.get(prefix, 1)

    return value * factor


def read_thorlabs_file(filepath):
    """Reads your Thorlabs format with metadata at lines 1–4."""
    with open(filepath, encoding="latin-1") as f:
        lines = [line.strip() for line in f if line.strip()]

    #metadata
    unit_line = lines[1]
    wavelength_line = lines[2]
    range_line = lines[3]

    parts = unit_line.split()
    col2_unit = parse_unit_in_brackets(parts[2])
    col3_unit = parse_unit_in_brackets(parts[-1])
    wavelength = extract_number(wavelength_line)
    range_watts = parse_micro_value(range_line)

    times_ms = []
    powers_w = []

    for line in lines[4:]:
        if "\t" in line:
            y_str, x_str = line.split("\t")
        else:
            y_str, x_str = line.split()

        powers_w.append(float(y_str))
        times_ms.append(float(x_str))

    return times_ms, powers_w, col2_unit, col3_unit, wavelength, range_watts


def main():
    base_dir = "."

    for root, dirs, files in os.walk(base_dir):
        csv_files = [f for f in files if f.lower().endswith(".csv")]
        if len(csv_files) == 0:
            continue

        csv_path = os.path.join(root, csv_files[0])
        folder_name = os.path.basename(root)

        print(f"\nProcessing: {csv_path}")

        times_ms, powers_w, unit_power, unit_time, wavelength, range_watts = read_thorlabs_file(csv_path)

        times_s = [t / 1000.0 for t in times_ms]   # ms → s
        powers_uW = [p * 1e6 for p in powers_w]    # W → µW

        #5% error for 402nm
        uncertainties = [0.05 * p for p in powers_uW]
        upper = [p + u for p, u in zip(powers_uW, uncertainties)]
        lower = [p - u for p, u in zip(powers_uW, uncertainties)]


        plt.figure(figsize=(7, 4))
        plt.plot(times_s, powers_uW, color="blue", label="Laser 402nm optical power output")
        plt.fill_between(times_s, lower, upper,
                         color="blue", alpha=0.2,
                         label="±5% uncertainty")

        plt.xlabel("Time [s]")
        plt.ylabel("Power [µW]")
        plt.ylim(0.08, 0.22)
        #plt.title(folder_name)
        plt.grid(True)
        plt.legend()
        plt.tight_layout()

        out_path = os.path.join(root, f"{folder_name}.png")
        plt.savefig(out_path, dpi=100)
        print(f"Saved: {out_path}")
        out_path = os.path.join(root, f"{folder_name}.pdf")
        plt.savefig(out_path)
        print(f"Saved: {out_path}")

        #plt.show()
        plt.close()


if __name__ == "__main__":
    main()

