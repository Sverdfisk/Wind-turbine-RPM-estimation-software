import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# --------------------------------------------------------------------
# 1) Files and their timestamp-column index
# --------------------------------------------------------------------
files = {
    "Resolution: 280x290\n Large boxes": "box_params/huge_boxes/out.csv",
    "Resolution: 280×290\n Small boxes": "resolution_frametime/run_280x290/out.csv",
    "Resolution: 1920×1080\n Small boxes": "resolution_frametime/run_1920x1080/out.csv",
    "50 erosion-dilation iterations": "box_params/many_er_dil_iterations/out.csv",
}

# Timestamp column: 0 for run_280x290/out.csv, 1 everywhere else
ts_col_for = {
    name: (0 if path.endswith("run_280x290/out.csv") else 1)
    for name, path in files.items()
}

# --------------------------------------------------------------------
# 2) Crunch the numbers
# --------------------------------------------------------------------
avg_fps = {}  # name → mean FPS
p01_fps = {}  # name → 1 % low FPS

for name, path in files.items():
    col = ts_col_for[name]

    df = pd.read_csv(path, header=None, skiprows=1, skipfooter=1, engine="python")

    ts = pd.to_datetime(df[col])
    delta_ms = ts.diff().dt.total_seconds().iloc[1:] * 1_000  # ms between frames

    fps_series = 1_000 / delta_ms  # instantaneous FPS
    avg_fps[name] = fps_series.mean()  # average FPS
    p01_fps[name] = fps_series.quantile(0.01)  # 1 % low FPS

# --------------------------------------------------------------------
# 3) Plot
# --------------------------------------------------------------------
names = list(avg_fps.keys())
avgs = [avg_fps[n] for n in names]
p01s = [p01_fps[n] for n in names]

x_pos = range(len(names))
width = 0.8  # parent bar width
inner_w = width  # 1 %-low bar width (over-laid)

plt.figure(figsize=(9, 5))

parent_colors = plt.cm.tab10(range(len(names)))


# Helper to darken a RGB tuple
def darker(rgb, factor=0.7):
    return tuple(channel * factor for channel in rgb)


darker_colors = [darker(mcolors.to_rgb(c)) for c in parent_colors]

# Parent bars (average FPS)
bars_avg = plt.bar(x_pos, avgs, width=width, color=parent_colors, label="Average FPS")

# Child bars (1 % low FPS) – drawn after so they sit on top
bars_p01 = plt.bar(x_pos, p01s, width=inner_w, color=darker_colors, label="1% low FPS")

plt.ylabel("FPS")
plt.title("Average FPS and 1 % lows per configuration")
plt.grid(axis="y", linestyle="--", alpha=0.3)
plt.xticks(x_pos, names)

# Put the value labels just above each bar
for bar, val in zip(bars_avg, avgs):
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        val,
        f"{val:.1f} FPS",
        ha="center",
        va="bottom",
    )

for bar, val in zip(bars_p01, p01s):
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        val,
        f"1% low: {val:.1f} FPS",
        ha="center",
        va="bottom",
        fontsize=10,
    )

plt.tight_layout()
plt.show()
