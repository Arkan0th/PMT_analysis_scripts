#!/usr/bin/env python3

from ROOT_ADC_ext import main as run_root_processing
from ADC_distance_plot import main as run_plotting

def main():
    print("\n=== Running ROOT processing ===")
    run_root_processing()

    print("\n=== Running plotting ===")
    run_plotting()

if __name__ == "__main__":
    main()
