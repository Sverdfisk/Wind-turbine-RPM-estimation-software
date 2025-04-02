import pandas as pd
import matplotlib.pyplot as plt

# --- File Paths ---
file_fb1 = "out_fb1.csv"
file_fb3 = "out_fb3.csv"
file_fb5 = "out_fb5.csv"

# --- Read CSVs ---
# Assuming:
#   - No header row
#   - Each CSV has two columns: [X-values, RPM-values]
df_fb1 = pd.read_csv(file_fb1, header=None)
df_fb3 = pd.read_csv(file_fb3, header=None)
df_fb5 = pd.read_csv(file_fb5, header=None)

# --- Extract columns ---
x_fb1, rpm_fb1 = df_fb1[0], df_fb1[1]
x_fb3, rpm_fb3 = df_fb3[0], df_fb3[1]
x_fb5, rpm_fb5 = df_fb5[0], df_fb5[1]

# -----------------------------------------------------------------
# Define the slice you want to explore:
# e.g., slice(100, 200) means you look at data from index 100 to 199 inclusive.
# -----------------------------------------------------------------
data_slice = slice(300, 1300)  # Change as needed

# --- Apply the slice ---
x_fb1_sl, rpm_fb1_sl = x_fb1[data_slice], rpm_fb1[data_slice]
x_fb3_sl, rpm_fb3_sl = x_fb3[data_slice], rpm_fb3[data_slice]
x_fb5_sl, rpm_fb5_sl = x_fb5[data_slice], rpm_fb5[data_slice]

# --- Compute means of the Y-values (for the selected slice) ---
mean_fb1 = rpm_fb1_sl.mean()
mean_fb3 = rpm_fb3_sl.mean()
mean_fb5 = rpm_fb5_sl.mean()

# --- Compute AAD of the Y-values (for the selected slice) ---
#     AAD = mean( |data_i - mean| )
aad_fb1 = (rpm_fb1_sl - mean_fb1).abs().mean()
aad_fb3 = (rpm_fb3_sl - mean_fb3).abs().mean()
aad_fb5 = (rpm_fb5_sl - mean_fb5).abs().mean()

# --- Create a figure with two subplots ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8))

# -------------------------
# Subplot 1: The data lines
# -------------------------
ax1.plot(x_fb1_sl, rpm_fb1_sl, label="Data FB1")
ax1.plot(x_fb3_sl, rpm_fb3_sl, label="Data FB3")
ax1.plot(x_fb5_sl, rpm_fb5_sl, label="Data FB5")

ax1.axhline(mean_fb1, linestyle="--", color="blue",
            label=f"Mean FB1 = {mean_fb1:.4f}")
ax1.axhline(
    mean_fb3, linestyle="--", color="orange", label=f"Mean FB3 = {mean_fb3:.4f}"
)
ax1.axhline(mean_fb5, linestyle="--", color="green",
            label=f"Mean FB5 = {mean_fb5:.4f}")

real_rpm = 11.5025
ax1.axhline(real_rpm, color="gray", label=f"Real RPM = {real_rpm}")

ax1.set_title("Comparison of Three RPM Datasets (Sliced)")
ax1.set_xlabel("X-Values (Index/Time)")
ax1.set_ylabel("RPM")
ax1.legend()

# -------------------------------------
# Subplot 2: Bar chart of each dataset’s AAD
# -------------------------------------
aad_values = [aad_fb1, aad_fb3, aad_fb5]
labels = ["FB1", "FB3", "FB5"]
ax2.bar(labels, aad_values)
ax2.set_title("Average Absolute Deviation (AAD) for Each Dataset")
ax2.set_ylabel("AAD (RPM)")

# Layout and show
fig.tight_layout()
plt.show()
