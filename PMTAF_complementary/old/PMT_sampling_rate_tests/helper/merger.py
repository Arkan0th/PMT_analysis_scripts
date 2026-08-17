import ROOT
import os

# Define desired binning (adjust bins, xmin, xmax)
bins = 1961
xmin = 8.54939/10**8
xmax = 1.34494/10**7

hist_list = []

for root_dir, dirs, files in os.walk("."):
    for file_name in files:
        if file_name == "pulses.root":
            file_path = os.path.join(root_dir, file_name)
            print(f"Processing file: {file_path}")

            root_file = ROOT.TFile.Open(file_path)
            if not root_file or root_file.IsZombie():
                print(f"Error opening file: {file_path}")
                continue

            singlephotons_dir = root_file.Get("singlephotons")
            if not singlephotons_dir:
                print(f"'singlephotons' directory not found in: {file_path}")
                root_file.Close()
                continue

            hist = singlephotons_dir.Get("h_t_peak")
            if not hist:
                print(f"Histogram 'h_t_peak' not found in {file_path}")
                root_file.Close()
                continue

            # Create new histogram with fixed binning
            new_hist = ROOT.TH1D(f"h_t_peak_{file_name}", "Rebinned h_t_peak", bins, xmin, xmax)
            new_hist.SetDirectory(0)

            # Copy content bin-by-bin
            for i in range(1, hist.GetNbinsX() + 1):
                # Get bin content and error
                content = hist.GetBinContent(i)
                error = hist.GetBinError(i)
                # Find bin center for old histogram
                x_center = hist.GetBinCenter(i)
                # Fill corresponding bin in new histogram
                bin_new = new_hist.FindBin(x_center)
                # Add content and error quadratically (to be safe)
                prev_content = new_hist.GetBinContent(bin_new)
                prev_error = new_hist.GetBinError(bin_new)
                new_hist.SetBinContent(bin_new, prev_content + content)
                new_hist.SetBinError(bin_new, (prev_error**2 + error**2)**0.5)

            hist_list.append(new_hist)
            root_file.Close()

if not hist_list:
    print("No histograms found to merge.")
    exit()

# Now add all rebinned histograms
merged_hist = hist_list[0].Clone("h_t_peak_merged")
merged_hist.SetDirectory(0)
for h in hist_list[1:]:
    merged_hist.Add(h)

# Save result
output_file = ROOT.TFile.Open("h_t_peak_merged.root", "RECREATE")
merged_hist.Write()
output_file.Close()

print(f"Merged {len(hist_list)} histograms with fixed binning successfully.")

