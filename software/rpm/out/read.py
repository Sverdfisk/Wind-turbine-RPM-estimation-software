import matplotlib.pyplot as plt
import numpy as np

# Initialize lists to store the x-values, RPM values, and Error values
x_vals = []
rpm_vals = []
error_vals = []

# Read data from the file 'data.txt'
with open('run_results.csv', 'r') as file:
    for line in file:
        # Remove any extra whitespace or newline characters
        line = line.strip()
        if not line:
            continue  # Skip empty lines
        
        # Split the line by commas
        parts = line.split(',')
        if len(parts) != 3:
            print(f"Skipping line (expected 3 values): {line}")
            continue
        
        try:
            # Convert the strings to floats
            x = float(parts[0].strip())
            rpm = float(parts[1].strip())
            error = float(parts[2].strip())
        except ValueError:
            print(f"Could not convert values to float in line: {line}")
            continue

        # Append the values to the lists
        x_vals.append(x)
        rpm_vals.append(rpm)
        error_vals.append(error)

# Create a figure with two subplots (stacked vertically)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12), sharex=True)

print(np.mean(rpm_vals))
# Plot the RPM values on the first subplot
ax1.plot(x_vals, rpm_vals, marker='o', linestyle='-', color='blue')
ax1.set_title('RPM vs X')
ax1.set_ylabel('RPM')
ax1.grid(True)

# Plot the Error values on the second subplot
ax2.plot(x_vals, error_vals, marker='s', linestyle='-', color='red')
ax2.set_title('Error vs X')
ax2.set_xlabel('X Value')
ax2.set_ylabel('Error')
ax2.grid(True)

# Adjust layout to prevent overlap
plt.tight_layout()

# Display the plots
plt.show()
