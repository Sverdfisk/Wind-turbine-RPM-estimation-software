import numpy as np

roi = [234, 158, 97]
# roi is a color image (H x W x 3)
avg_val = np.mean(roi)

print(avg_val)
