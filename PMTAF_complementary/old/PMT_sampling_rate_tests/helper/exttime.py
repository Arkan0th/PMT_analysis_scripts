import ROOT

file = ROOT.TFile.Open("h_t_peak_merged.root")
dir = ROOT.gDirectory

name = "h_t_peak"
graph = dir.Get(name)

if not graph:
    print(f"Warning: {name} not found in 'singlephotons' directory.")
else:
    print(f"{name} successfully retrieved.")

    c = ROOT.TCanvas("c", "Canvas", 800, 600)
    graph.Draw()
    c.SaveAs(f"{name}.png")

file.Close()
