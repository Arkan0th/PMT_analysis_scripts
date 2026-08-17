from pathlib import Path
import csv

csv_file = next(Path(".").glob("*cm/*.csv"))

print("Testing:", csv_file)

with open(csv_file, newline="") as f:
    reader = csv.DictReader(f, delimiter="\t")

    print("Columns:")
    print(reader.fieldnames)

    for row in reader:
        print(row)
        break
