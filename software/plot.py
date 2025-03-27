import matplotlib.pyplot as plt

# --- 1) Read files ---
x_smooth, y_smooth = [], []
with open("out_smoothed.txt", "r") as f:
    for line in f:
        parts = line.strip().split()
        x_smooth.append(float(parts[0]))
        y_smooth.append(float(parts[1]))

x_nonsmooth, y_nonsmooth = [], []
with open("out_nonsmoothed.txt", "r") as f:
    for line in f:
        parts = line.strip().split()
        x_nonsmooth.append(float(parts[0]))
        y_nonsmooth.append(float(parts[1]))

x_ultra, y_ultra = [], []
with open("out_ultrasmoothed.txt", "r") as f:
    for line in f:
        parts = line.strip().split()
        x_ultra.append(float(parts[0]))
        y_ultra.append(float(parts[1]))

# --- 2) Truncate so all three have the same length ---
min_length = min(len(x_smooth), len(x_nonsmooth), len(x_ultra))
x_smooth = x_smooth[600:min_length]
y_smooth = y_smooth[600:min_length]
x_nonsmooth = x_nonsmooth[600:min_length]
y_nonsmooth = y_nonsmooth[600:min_length]
x_ultra = x_ultra[600:min_length]
y_ultra = y_ultra[600:min_length]

# --- 3) Compute means ---
mean_smooth = sum(y_smooth) / len(y_smooth)
mean_nonsmooth = sum(y_nonsmooth) / len(y_nonsmooth)
mean_ultra = sum(y_ultra) / len(y_ultra)

# Example real RPM line
real_rpm = 11.578

# --- 4) Create single figure & axes ---
fig, ax = plt.subplots(figsize=(10, 6))

# Plot each dataset with a unique color
ax.plot(x_smooth, y_smooth, color="blue", label="Smoothed Data")
ax.plot(x_nonsmooth, y_nonsmooth, color="green", label="Non-Smoothed Data")
ax.plot(x_ultra, y_ultra, color="orange", label="Ultra-Smoothed Data")

# Draw lines for real RPM and each mean
ax.axhline(
    y=real_rpm, color="black", linestyle="--", label=f"Real RPM = {real_rpm:.2f}"
)
ax.axhline(
    y=mean_smooth,
    color="blue",
    linestyle=":",
    label=f"Smoothed Mean = {mean_smooth:.2f}",
)
ax.axhline(
    y=mean_nonsmooth,
    color="green",
    linestyle=":",
    label=f"Non-Smoothed Mean = {mean_nonsmooth:.2f}",
)
ax.axhline(
    y=mean_ultra,
    color="orange",
    linestyle=":",
    label=f"Ultra-Smoothed Mean = {mean_ultra:.2f}",
)

# (Optional) Annotate each mean or real RPM:
ax.annotate(
    f"{real_rpm:.2f}",
    xy=(0.5, real_rpm),
    xytext=(0, 10),
    textcoords="offset points",
    ha="center",
    color="black",
)
ax.annotate(
    f"{mean_smooth:.2f}",
    xy=(0.5, mean_smooth),
    xytext=(0, 10),
    textcoords="offset points",
    ha="center",
    color="blue",
)
ax.annotate(
    f"{mean_nonsmooth:.2f}",
    xy=(0.5, mean_nonsmooth),
    xytext=(0, 10),
    textcoords="offset points",
    ha="center",
    color="green",
)
ax.annotate(
    f"{mean_ultra:.2f}",
    xy=(0.5, mean_ultra),
    xytext=(0, 10),
    textcoords="offset points",
    ha="center",
    color="orange",
)

# Axis labels, title, legend
ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_title("Comparison of Smoothed, Non-Smoothed, and Ultra-Smoothed Data")
ax.legend(fontsize=12)  # Increase legend font if needed

plt.tight_layout()
plt.show()
