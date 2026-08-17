import ROOT

# --- USER SETTINGS ---
rebin_factor = 8  # Number of bins to combine
hist_name = "h_t_peak"
output_image = f"h_t_max_rebinned_{rebin_factor}x.png"
output_rootfile = f"rebinned_hist_{rebin_factor}x.root"
x_min = 0.09e-6  # 90 ns
x_max = 0.1e-6   # 100 ns
# ---------------------

# Open the ROOT file
file = ROOT.TFile.Open("pulses.root", "READ")
if not file or file.IsZombie():
    raise RuntimeError("Could not open 'pulses.root'.")

# Get histogram from directory
hist = file.Get("singlephotons/" + hist_name)
if not hist:
    raise RuntimeError(f"Histogram '{hist_name}' not found in 'singlephotons'.")

# Clone and rebin
hist_rebinned = hist.Clone(f"{hist_name}_rebinned_{rebin_factor}x")
hist_rebinned.Rebin(rebin_factor)

# Create canvas and draw
canvas = ROOT.TCanvas("c", "Rebinned Histogram Zoomed", 800, 600)
ROOT.gStyle.SetOptStat(1110)
hist_rebinned.SetLineColor(ROOT.kBlue + 1)
hist_rebinned.SetTitle(f"{hist_name} rebinned by {rebin_factor}x")

# Apply zoom
hist_rebinned.GetXaxis().SetRangeUser(x_min, x_max)
hist_rebinned.Draw()

# Save canvas as image
canvas.SaveAs(output_image)

# Optionally save rebinned histogram to a ROOT file
out_file = ROOT.TFile.Open(output_rootfile, "RECREATE")
hist_rebinned.Write()
out_file.Close()

print(f"Rebinned and zoomed histogram saved as: {output_image}")
print(f"Also written to: {output_rootfile}")

