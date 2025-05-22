import pandas as pd
import matplotlib.pyplot as plt

# ——— Config ———
files = ["runs/fewbiguns.csv", "runs/manysmalluns.csv"]
labels = ["6 boxes at size 12", "13 boxes at size 5"]
colors = {"6 boxes at size 12": "red", "13 boxes at size 5": "blue"}

# ——— Load & parse ———
data = {}
for path, label in zip(files, labels):
    df = pd.read_csv(
        path,
        header=None,
        skiprows=1,  # drop header line
        skipfooter=1,  # drop trailing summary
        engine="python",
        names=["frame", "composite", "rpm"],
    )
    comps = df["composite"].str.split("/", expand=True)
    comps.columns = ["color_delta", "mode", "threshold"]
    for col in ("color_delta", "mode", "threshold"):
        df[col] = pd.to_numeric(comps[col], errors="coerce")
    df["rpm"] = pd.to_numeric(df["rpm"], errors="coerce")
    data[label] = df

# ——— Plot 1: RPM vs Frame ———
plt.figure(figsize=(8, 4))
for label, df in data.items():
    plt.plot(df["frame"], df["rpm"], color=colors[label], label=label)
plt.title("Frame Number vs RPM")
plt.xlabel("Frame Number")
plt.ylabel("RPM")
plt.legend()
plt.tight_layout()
plt.show()

# ——— Plot 2: Separate windows for each file ———
for label, df in data.items():
    plt.figure(figsize=(8, 4))
    c = colors[label]
    plt.plot(
        df["frame"], df["color_delta"], linestyle="-", color=c, label="color delta"
    )
    plt.plot(df["frame"], df["threshold"], linestyle="--", color=c, label="threshold")
    plt.title(f"{label}: Color Delta & Threshold")
    plt.xlabel("Frame Number")
    plt.ylabel("Value")
    plt.legend()
    plt.tight_layout()
    plt.show()
