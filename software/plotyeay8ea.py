import pandas as pd
import matplotlib.pyplot as plt

# Replace 'path/to/your.csv' with the actual path to your CSV file
file_path = "runs/out.csv"

# Read the CSV into a DataFrame
df = pd.read_csv(file_path, header=None, names=["tick", "timestamp", "metrics", "rpm"])

# Split the 'metrics' column into delta, mode, threshold
metrics_split = df["metrics"].str.split("/", expand=True)
metrics_split.columns = ["delta", "mode", "threshold"]

# Convert to numeric types
df["delta"] = metrics_split["delta"].astype(float)
df["mode"] = metrics_split["mode"].astype(float)
df["threshold"] = metrics_split["threshold"].astype(float)
df["rpm"] = df["rpm"].astype(float)

# Parse timestamp column into datetime objects
df["timestamp"] = pd.to_datetime(df["timestamp"])

# Plot Delta over Time
plt.figure()
plt.plot(df["timestamp"], df["delta"])
plt.title("Delta over Time")
plt.xlabel("Timestamp")
plt.ylabel("Delta")
plt.tight_layout()
plt.show()

# Plot Threshold over Time
plt.figure()
plt.plot(df["timestamp"], df["threshold"])
plt.title("Threshold over Time")
plt.xlabel("Timestamp")
plt.ylabel("Threshold")
plt.tight_layout()
plt.show()

# Plot RPM over Time
plt.figure()
plt.plot(df["timestamp"], df["rpm"])
plt.title("RPM over Time")
plt.xlabel("Timestamp")
plt.ylabel("RPM")
plt.tight_layout()
plt.show()
