import numpy as np

ticks = [
    46,
    99,
    156,
    214,
    268,
    326,
    384,
    438,
    498,
    557,
    611,
    670,
    729,
    783,
    842,
    901,
    955,
    1014,
    1073,
]
tick_times = []
for index, element in enumerate(ticks):
    if index != len(ticks) - 1:
        tick_times.append(ticks[index + 1] - ticks[index])
    else:
        break

fps = float(input("fps:"))
rpms = []
for time in tick_times:
    real_time = time / fps
    adjusted_ticktime_seconds = real_time * 3
    rpm = 60 / adjusted_ticktime_seconds
    rpms.append(rpm)

print(f"RPMS: {rpms}\n Mean: {np.mean(rpms)}")
