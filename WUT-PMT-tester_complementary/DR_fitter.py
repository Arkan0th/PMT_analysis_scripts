#!/usr/bin/env python3

import sys
import json
from pathlib import Path
from datetime import datetime

import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

OUTPUT_PNG = BASE_DIR / "dark_rates.png"
OUTPUT_PDF = BASE_DIR / "dark_rates.pdf"

CHANNELS = [1, 2, 3, 4, 5, 6]


# ============================================================
# MULTIPLICATIVE INVERSE MODEL
# ============================================================

def inverse_model(t, R_inf, A, tau):
    """
    Multiplicative inverse / 1/x model:

        R(t) = R_inf + A / (t + tau)

    Parameters
    ----------
    t : time [s]

    R_inf : asymptotic dark rate [Hz]

    A : amplitude [Hz*s]

    tau : characteristic time [s]

    At t = 0:

        R(0) = R_inf + A/tau

    For t -> infinity:

        R(t) -> R_inf
    """

    return R_inf + A / (t + tau)


# ============================================================
# READ JSON FILE
# ============================================================

def read_test_file(filename):

    path = Path(filename)

    print(f"\nReading {path}")

    with open(path, "r") as f:
        data = json.load(f)

    dark_run = data["tests"]["dark_run"]

    measurements = []

    for entry in dark_run["mon_log"]:

        timestamp = datetime.fromisoformat(
            entry["timestamp"]
        )

        rates = {}

        for channel in CHANNELS:

            rates[channel] = (
                entry["channels"]
                .get(str(channel), {})
                .get("r_mon", np.nan)
            )

        measurements.append({
            "timestamp": timestamp,
            "rates": rates,
        })

    measurements.sort(
        key=lambda m: m["timestamp"]
    )

    start_time = measurements[0]["timestamp"]

    for m in measurements:

        m["elapsed_seconds"] = (
            m["timestamp"] - start_time
        ).total_seconds()

    return measurements


# ============================================================
# REMOVE EM SPIKES
# ============================================================

def remove_em_spikes(y, threshold):

    y = np.asarray(
        y,
        dtype=float
    ).copy()

    for i in range(1, len(y) - 1):

        if (
            not np.isfinite(y[i])
            or not np.isfinite(y[i - 1])
            or not np.isfinite(y[i + 1])
        ):
            continue

        if (
            y[i] > threshold * y[i - 1]
            and
            y[i] > threshold * y[i + 1]
        ):

            y[i] = 0.5 * (
                y[i - 1] + y[i + 1]
            )

    return y


# ============================================================
# BIN DATA
# ============================================================

def bin_data(
    x,
    y,
    bin_size=180
):

    x = np.asarray(x)
    y = np.asarray(y)

    n = len(y) // bin_size

    x = x[:n * bin_size]
    y = y[:n * bin_size]

    x = x.reshape(
        n,
        bin_size
    )

    y = y.reshape(
        n,
        bin_size
    )

    x_bin = np.mean(
        x,
        axis=1
    )

    y_bin = np.mean(
        y,
        axis=1
    )

    y_err = np.std(
        y,
        axis=1,
        ddof=1
    )

    # Avoid zero uncertainties
    y_err = np.maximum(
        y_err,
        0.1
    )

    return (
        x_bin,
        y_bin,
        y_err
    )


# ============================================================
# REDUCED CHI SQUARE
# ============================================================

def calculate_reduced_chi_square(
    y,
    y_pred,
    y_err,
    n_parameters
):

    residuals = (
        (y - y_pred)
        / y_err
    )

    chi2 = np.sum(
        residuals ** 2
    )

    ndf = (
        len(y)
        - n_parameters
    )

    if ndf <= 0:
        return np.nan

    return chi2 / ndf


# ============================================================
# FIT CHANNEL
# ============================================================

def fit_channel(
    x,
    y,
    channel,
    y_err
):

    print()
    print(f"CH{channel:02d}")
    print("=" * 60)

    # ========================================================
    # Valid data
    # ========================================================

    valid = (
        np.isfinite(x)
        &
        np.isfinite(y)
        &
        np.isfinite(y_err)
        &
        (y > 0)
    )

    x_valid = x[valid]
    y_valid = y[valid]
    err_valid = y_err[valid]

    if len(x_valid) < 10:

        print("Not enough data points.")

        return None

    # ========================================================
    # IMPORTANT:
    #
    # Everything is now kept in SECONDS.
    #
    # No conversion to hours during fitting.
    # ========================================================

    t_fit = x_valid.copy()

    # Shift beginning of fit to t = 0
    t_fit = t_fit - t_fit[0]

    y_fit = y_valid.copy()
    err_fit = err_valid.copy()

    # ========================================================
    # Remove EM spikes
    # ========================================================

    y_clean = remove_em_spikes(
        y_fit,
        threshold=1.2
    )

    # ========================================================
    # Initial guesses
    # ========================================================

    R_initial = np.mean(
        y_clean[-10:]
    )

    R_initial = max(
        R_initial,
        0.01
    )

    excess_initial = max(
        y_clean[0] - R_initial,
        0.1
    )

    # Estimate tau from the time scale of the measurement.
    tau_initial = max(
        (t_fit[-1] - t_fit[0]) / 10.0,
        1.0
    )

    # Since
    #
    #   excess = A / tau
    #
    # approximately:
    A_initial = (
        excess_initial
        * tau_initial
    )

    # ========================================================
    # INVERSE FIT
    # ========================================================

    try:

        inverse_params, inverse_cov = curve_fit(
            inverse_model,
            t_fit,
            y_clean,
            sigma=err_fit,
            absolute_sigma=True,

            p0=[
                R_initial,
                A_initial,
                tau_initial
            ],

            bounds=(
                [
                    0.0,
                    0.0,
                    1e-6
                ],
                [
                    np.inf,
                    np.inf,
                    np.inf
                ]
            ),

            maxfev=200000
        )

        # ====================================================
        # Extract parameters
        # ====================================================

        R_inf = inverse_params[0]
        A = inverse_params[1]
        tau = inverse_params[2]

        # ====================================================
        # Parameter uncertainties
        # ====================================================

        parameter_errors = np.sqrt(
            np.maximum(
                np.diag(inverse_cov),
                0.0
            )
        )

        R_inf_err = parameter_errors[0]
        A_err = parameter_errors[1]
        tau_err = parameter_errors[2]

        # ====================================================
        # Prediction
        # ====================================================

        y_pred = inverse_model(
            t_fit,
            R_inf,
            A,
            tau
        )

        chi2_ndf = calculate_reduced_chi_square(
            y_clean,
            y_pred,
            err_fit,
            n_parameters=3
        )

        # ====================================================
        # Also calculate initial rate
        # ====================================================

        R_initial_fit = (
            R_inf
            + A / tau
        )

        # ====================================================
        # Print results
        # ====================================================

        print()
        print("Multiplicative inverse model:")
        print()
        print(
            "    R(t) = R_inf + A / (t + tau)"
        )

        print()

        print(
            f"    R_inf = "
            f"{R_inf:.3f} ± "
            f"{R_inf_err:.3f} Hz"
        )

        print(
            f"    A     = "
            f"{A:.3e} ± "
            f"{A_err:.3e} Hz*s"
        )

        print(
            f"    tau   = "
            f"{tau:.3f} ± "
            f"{tau_err:.3f} s"
        )

        print(
            f"    tau   = "
            f"{tau / 3600.0:.4f} ± "
            f"{tau_err / 3600.0:.4f} h"
        )

        print(
            f"    R(0)  = "
            f"{R_initial_fit:.3f} Hz"
        )

        print(
            f"    chi²/ndf = "
            f"{chi2_ndf:.3f}"
        )

        # ====================================================
        # Covariance matrix
        # ====================================================

        print()
        print("Covariance matrix:")
        print(inverse_cov)

        return {
            "channel": channel,

            "R_inf_Hz": R_inf,
            "R_inf_err_Hz": R_inf_err,

            "A_Hz_s": A,
            "A_err_Hz_s": A_err,

            "tau_s": tau,
            "tau_err_s": tau_err,

            "R_initial_Hz": R_initial_fit,

            "chi2_ndf": chi2_ndf,

            "t_start_s": x_valid[0],
        }

    except Exception as e:

        print()
        print(
            f"Inverse fit failed: {e}"
        )

        return None


# ============================================================
# CREATE PLOT
# ============================================================

def make_plot(
    measurements,
    output_png,
    output_pdf
):

    # ========================================================
    # TIME AXIS
    #
    # Keep seconds for all calculations.
    # Only convert to hours for displaying the x-axis.
    # ========================================================

    x_seconds = np.array(
        [
            m["elapsed_seconds"]
            for m in measurements
        ],
        dtype=float
    )

    x_hours = (
        x_seconds / 3600.0
    )

    # ========================================================
    # FIGURE
    # ========================================================

    fig, ax = plt.subplots(
        figsize=(12, 8)
    )

    # ========================================================
    # CHANNELS
    # ========================================================

    for channel in CHANNELS:

        # ----------------------------------------------------
        # Get data
        # ----------------------------------------------------

        y = np.array(
            [
                m["rates"].get(
                    channel,
                    np.nan
                )
                for m in measurements
            ],
            dtype=float
        )

        y_clean = remove_em_spikes(
            y,
            1.2
        )

        # ----------------------------------------------------
        # Bin data
        #
        # IMPORTANT:
        # x_bin remains in seconds.
        # ----------------------------------------------------

        x_bin_seconds, y_bin, y_err = bin_data(
            x_seconds,
            y_clean
        )

        # ----------------------------------------------------
        # Fit
        # ----------------------------------------------------

        fit = fit_channel(
            x_bin_seconds,
            y_bin,
            channel,
            y_err
        )

        # ----------------------------------------------------
        # Raw data
        # ----------------------------------------------------

        ax.scatter(
            x_hours,
            y_clean,
            s=1,
            alpha=0.4
        )

        # ----------------------------------------------------
        # Binned data
        # ----------------------------------------------------

        ax.errorbar(
            x_bin_seconds / 3600.0,
            y_bin,
            yerr=y_err,
            fmt='ko',
            markersize=0.2,
            linewidth=0.1
        )

        # ----------------------------------------------------
        # Plot inverse fit
        # ----------------------------------------------------

        if fit is not None:

            R_inf = fit["R_inf_Hz"]
            R_inf_err = fit["R_inf_err_Hz"]

            A = fit["A_Hz_s"]
            A_err = fit["A_err_Hz_s"]

            tau = fit["tau_s"]
            tau_err = fit["tau_err_s"]

            # ------------------------------------------------
            # Generate curve in SECONDS
            # ------------------------------------------------

            t_plot_seconds = np.linspace(
                x_bin_seconds.min(),
                x_bin_seconds.max(),
                1000
            )

            # ------------------------------------------------
            # Shift exactly like the fitting function
            # ------------------------------------------------

            t_plot_fit = (
                t_plot_seconds
                - x_bin_seconds[0]
            )

            y_plot = inverse_model(
                t_plot_fit,
                R_inf,
                A,
                tau
            )

            # ------------------------------------------------
            # Plot
            # ------------------------------------------------

            ax.plot(
                t_plot_seconds / 3600.0,
                y_plot,
                linewidth=1.5,
                zorder=10,

                label=(
                    f"CH{channel:02d}\n"
                    f"$R_\\infty="
                    f"{R_inf:.0f}"
                    f"\\pm"
                    f"{R_inf_err:.0f}$ Hz\n"
                    f"$\\tau="
                    f"{tau / 3600.0:.3f}"
                    f"\\pm"
                    f"{tau_err / 3600.0:.3f}$ h\n"
                )
            )

    # ========================================================
    # AXIS LABELS
    # ========================================================

    ax.set_xlabel(
        "Elapsed time [h]",
        fontsize=14
    )

    ax.set_ylabel(
        "Dark rate [Hz]",
        fontsize=14
    )

    # ========================================================
    # LOG SCALE
    # ========================================================

    ax.set_yscale("log")

    # ========================================================
    # GRID
    # ========================================================

    ax.grid(
        True,
        linestyle=":",
        alpha=0.5
    )

    # ========================================================
    # LEGEND
    # ========================================================

    ax.legend(
        loc="upper right",
        ncol=2,
        fontsize=11,
        frameon=True
    )

    # ========================================================
    # LAYOUT
    # ========================================================

    plt.tight_layout()

    # ========================================================
    # SAVE PNG
    # ========================================================

    plt.savefig(
        output_png,
        dpi=150,
        bbox_inches="tight"
    )

    print()
    print(
        "PNG saved to:"
    )
    print(
        f"  {output_png}"
    )

    # ========================================================
    # SAVE PDF
    # ========================================================

    plt.savefig(
        output_pdf,
        format="pdf",
        bbox_inches="tight"
    )

    print()
    print(
        "PDF saved to:"
    )
    print(
        f"  {output_pdf}"
    )

    # ========================================================
    # SHOW
    # ========================================================

    plt.show()


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print(
        "=============================================="
    )

    print(
        " Dark Rate Analysis"
    )

    print(
        "=============================================="
    )

    print()
    print(
        "Base directory:"
    )

    print(
        f"  {BASE_DIR}"
    )

    if len(sys.argv) != 2:

        print(
            f"Usage: "
            f"python {Path(sys.argv[0]).name} "
            f"DATA_FILE.json"
        )

        sys.exit(1)

    measurements = read_test_file(
        sys.argv[1]
    )

    print()
    print(
        f"Total measurements: "
        f"{len(measurements)}"
    )

    make_plot(
        measurements,
        OUTPUT_PNG,
        OUTPUT_PDF
    )

    print()
    print(
        "=============================================="
    )

    print(
        " Done"
    )

    print(
        "==============================================")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
