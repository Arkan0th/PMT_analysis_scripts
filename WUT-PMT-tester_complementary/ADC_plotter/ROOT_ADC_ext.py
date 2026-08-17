#!/usr/bin/env python3

import ROOT
import os
import sys
import glob
import math

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)   # disables histogram stats box
ROOT.gStyle.SetOptFit(0)    # disables fit stats box

ADC_BITS = 12
ADC_MAX = 2 ** ADC_BITS      # 4096
XRANGE = ADC_MAX // 2        # Display first half (0-2048)


def find_pedestal(tree, raw_ch):
    """
    Find pedestal as weighted centroid around the highest bin.
    """
    htmp = ROOT.TH1F(
        f"htmp_{raw_ch}",
        "",
        ADC_MAX,
        0,
        ADC_MAX,
    )

    tree.Draw(
        f"adc>>htmp_{raw_ch}",
        f"channel=={raw_ch}",
        "goff",
    )

    peak = htmp.GetMaximumBin()
    first = max(1, peak - 5)
    last = min(htmp.GetNbinsX(), peak + 5)

    weighted_sum = 0.0
    weight = 0.0

    for b in range(first, last + 1):
        y = htmp.GetBinContent(b)
        x = htmp.GetBinCenter(b)
        weighted_sum += x * y
        weight += y

    if weight > 0:
        pedestal = weighted_sum / weight
    else:
        pedestal = htmp.GetBinCenter(peak)

    return pedestal


def process_file(input_file):
    print(f"\nProcessing {input_file}")

    fin = ROOT.TFile.Open(input_file)
    if not fin or fin.IsZombie():
        print("ERROR: Cannot open file.")
        return

    tree = fin.Get("pmt_events")
    if tree is None:
        print("ERROR: No TTree 'pmt_events' found.")
        fin.Close()
        return

    output_file = os.path.join(
        os.path.dirname(input_file),
        "adc_per_channel.root",
    )

    fout = ROOT.TFile(output_file, "RECREATE")

    canvas = ROOT.TCanvas("c1", "", 900, 700)
    canvas.SetLogy()

    txt_file = os.path.join(
        os.path.dirname(input_file),
        "fit_parameters.txt",
    )

    txt = open(txt_file, "w")
    txt.write("CH   Pedestal   Mean_corr  Sigma_mean  Sigma      Chi2     NDF\n")

    raw_channels = sorted({int(ev.channel) for ev in tree})
    print("Channels:", [c + 1 for c in raw_channels])

    for raw_ch in raw_channels:
        display_ch = raw_ch + 1

        pedestal = find_pedestal(tree, raw_ch)
        pedestal_int = math.floor(pedestal)

        print(
            f" Ch {display_ch:02d}: pedestal = {pedestal:.2f} ADC "
            f"(using floor = {pedestal_int})"
        )

        hist_name = f"adc_ch{display_ch:02d}"

        hist = ROOT.TH1F(
            hist_name,
            f"ADC CH{display_ch};ADC - pedestal corrected;#",
            XRANGE,
            0,
            XRANGE,
        )

        tree.Draw(
            f"(adc-{pedestal_int})>>{hist_name}",
            f"channel=={raw_ch}",
            "goff",
        )

        hist.Rebin(4)

        fit = fit_main_peak(hist)

        mean = fit.GetParameter(1)
        sigma = fit.GetParameter(2)
        sigma_mean = fit.GetParError(1)
        chi2 = fit.GetChisquare()
        ndf = fit.GetNDF()

        print(f"Mean = {mean:.2f}")
        print(f"Sigma_mean = {sigma_mean:.2f}")
        print(f"Sigma = {sigma:.2f}")

        txt.write(
            f"{display_ch:1d} "
            f"{pedestal:10.2f} "
            f"{mean:10.2f} "
            f"{sigma_mean:10.2f}"
            f"{sigma:10.2f} "
            f"{chi2:10.2f} "
            f"{ndf:5d}\n"
        )

        hist.Write()

        # Draw histogram with fit
        canvas.cd()
        canvas.Clear()
        canvas.SetLogy()

        hist.SetLineColor(ROOT.kBlue)
        hist.SetLineWidth(2)
        hist.Draw("HIST")

        fit.SetLineColor(ROOT.kRed)
        fit.SetLineWidth(3)
        fit.SetNpx(1000)
        fit.Draw("SAME")

        # Build legend
        entries = int(hist.GetEntries())
        chi2 = fit.GetChisquare()
        ndf = fit.GetNDF()
        mean = fit.GetParameter(1)
        sigma = fit.GetParameter(2)
        sigma_mean = fit.GetParError(1)

        entries_box = ROOT.TH1F(
            f"entries_box_ch{raw_ch}",
            "",
            1,
            0,
            1,
        )

        entries_box.SetDirectory(0)
        entries_box.SetFillColor(ROOT.kBlue)
        entries_box.SetFillStyle(0)
        entries_box.SetLineColor(ROOT.kBlue)
        entries_box.SetLineWidth(0)

        legend = ROOT.TLegend(0.58, 0.62, 0.88, 0.88)
        legend.SetBorderSize(0)
        legend.SetFillStyle(0)

        legend.AddEntry(entries_box, f"Entries = {entries}", "f")
        legend.AddEntry(fit, "Gaussian fit:", "l")
        legend.AddEntry("", f" #mu = {mean:.2f}", "")
        legend.AddEntry("", f" #sigma = {sigma:.2f}", "")
        legend.AddEntry("", f" #chi^2/ndf = {chi2:.1f}/{ndf}", "")

        legend.Draw()

        canvas.Update()

        png_name = os.path.join(
            os.path.dirname(input_file),
            f"adc_ch{display_ch:02d}_fit.png",
        )

        pdf_name = os.path.join(
            os.path.dirname(input_file),
            f"adc_ch{display_ch:02d}_fit.pdf",
        )

        canvas.SaveAs(png_name)
        canvas.SaveAs(pdf_name)

    txt.close()
    fout.Close()
    fin.Close()

    print(f"Saved {output_file}")


def collect_files(path):
    if os.path.isfile(path):
        return [path]

    return sorted(
        glob.glob(
            os.path.join(path, "**", "test_run*.root"),
            recursive=True,
        )
    )


def fit_main_peak(hist, threshold_adc=40, frac=0.7):
    # Ignore pedestal
    start_bin = hist.FindBin(threshold_adc)

    # Find maximum after threshold
    max_bin = start_bin
    max_counts = 0

    for b in range(start_bin, hist.GetNbinsX() + 1):
        y = hist.GetBinContent(b)
        if y > max_counts:
            max_counts = y
            max_bin = b

    peak = hist.GetBinCenter(max_bin)

    # Determine fit window
    level = frac * max_counts

    left = max_bin
    while left > start_bin and hist.GetBinContent(left) > level:
        left -= 1

    right = max_bin
    while right < hist.GetNbinsX() and hist.GetBinContent(right) > level:
        right += 1

    xmin = hist.GetBinCenter(left)
    xmax = hist.GetBinCenter(right)

    fit_temp = ROOT.TF1(
        f"fit_{hist.GetName()}",
        "gaus",
        xmin,
        xmax,
    )

    hist.Fit(fit_temp, "RQ0")

    mu = fit_temp.GetParameter(1)
    sigma = fit_temp.GetParameter(2)
    sigma_mu = fit_temp.GetParError(1)

    fit = ROOT.TF1(
        f"fit_{hist.GetName()}",
        "gaus",
        mu - 1 * sigma,
        mu + 1 * sigma,
    )

    #print(mu-sigma)
    #print(mu+sigma)

    fit.SetParameters(
        fit_temp.GetParameter(0),
        mu,
        sigma,
    )

    hist.Fit(fit, "RQ", "", mu-0.75*sigma, mu+0.75*sigma)

    return fit


def main():
    if len(sys.argv) > 1:
        files = collect_files(sys.argv[1])
    else:
        files = collect_files(".")

    if not files:
        print("No test_run*.root files found.")
        return

    print(f"Found {len(files)} file(s).")

    for f in files:
        process_file(f)


if __name__ == "__main__":
    main()
