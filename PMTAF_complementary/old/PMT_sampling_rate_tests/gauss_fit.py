import ROOT

# ---------------------
# USER CUSTOM SETTINGS
# ---------------------
hist_name = "h_t_peak_rebinned_8x"  # You can change this
custom_title = "TPaveText::title = Time Peak Distribution at 5GS/s"  # Your custom title text
# ---------------------

# Open ROOT file
file = ROOT.TFile.Open("rebinned_hist_8x.root")
if not file or file.IsZombie():
    raise RuntimeError("Could not open the file.")

# Access histogram directly (no subdirectory)
hist = file.Get(hist_name)
if not hist:
    raise RuntimeError(f"Could not find histogram '{hist_name}' in the ROOT file.")

# Set histogram title from user input
hist.SetTitle(custom_title.replace("TPaveText::title = ", ""))

# Disable automatic stats box
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetOptFit(0)

# --- Step 1: Initial rough fit ---
initial_fit = ROOT.TF1("initial_fit", "gaus", 94e-9, 95e-9)
hist.Fit(initial_fit, "RQ")

mean_est = initial_fit.GetParameter(1)
sigma_est = initial_fit.GetParameter(2)

# --- Step 2: Final symmetric fit ---
fit_min = mean_est - sigma_est
fit_max = mean_est + sigma_est

gaus = ROOT.TF1("gaus", "gaus", fit_min, fit_max)
fit_result = hist.Fit(gaus, "RS")

# Get fit results
mean = gaus.GetParameter(1)
sigma = gaus.GetParameter(2)
mean_err = gaus.GetParError(1)
sigma_err = gaus.GetParError(2)
chi2 = gaus.GetChisquare()
ndf = gaus.GetNDF()
chi2_ndf = chi2 / ndf if ndf != 0 else float('inf')
entries = hist.GetEntries()

# Print in terminal
print(f"Fit Mean:     {mean:.4e} ± {mean_err:.4e}")
print(f"Fit Sigma:    {sigma:.4e} ± {sigma_err:.4e}")
print(f"Chi2 / NDF:   {chi2:.2f} / {ndf} = {chi2_ndf:.2f}")
print(f"Entries:      {int(entries)}")
print(f"Fit Range:    [{fit_min:.4e}, {fit_max:.4e}]")

# Draw canvas
canvas = ROOT.TCanvas("c", "Gaussian Fit Zoomed", 800, 600)
hist.Draw()
gaus.Draw("same")

# Create TPaveText to display fit parameters in a nice box
pave = ROOT.TPaveText(0.60, 0.60, 0.88, 0.85, "NDC")  # NDC = normalized device coords
pave.SetFillColor(0)    # White background
pave.SetTextFont(42)    # Standard font
pave.SetTextSize(0.03)
pave.SetBorderSize(1)

pave.AddText(f"Entries: {int(entries)}")
pave.AddText(f"Mean = {mean:.2e} #pm {mean_err:.1e}")
pave.AddText(f"Sigma = {sigma:.2e} #pm {sigma_err:.1e}")
pave.AddText(f"#chi^{{2}}/NDF = {chi2:.1f} / {ndf} = {chi2_ndf:.2f}")
pave.Draw()

# Zoom x-axis to 90 ns – 100 ns
hist.GetXaxis().SetRangeUser(0.09e-6, 0.1e-6)

# Save output
canvas.SaveAs("gauss_fit_zoomed.png")

