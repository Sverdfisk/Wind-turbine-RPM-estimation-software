import math
import numpy as np

def calculate_frequency(velocity: float, radius: float, fps: float) -> float:
    # velocity is in pixels per frame
    # units: (pixels / frame) * (frames / second) / pixels ) = 1/s = rad/s
    ang_vel = (velocity * fps) / radius 
    freq = ang_vel / (2 * math.pi) # unit: 1/s
    return freq

def calculate_error_percentage(measured_value: float, actual_value: float=13) -> float:
    error_percentage = abs(measured_value - actual_value) / actual_value * 100
    return round(error_percentage, 2)

def filter_magnitudes(magnitudes: list) -> list:

    magnitudes = np.array(magnitudes)
    std_dev = np.std(magnitudes)
    mean = np.mean(magnitudes)

    # Filter elements within two standard deviations
    magnitudes = magnitudes[(magnitudes >= mean - 2 * std_dev) & (magnitudes <= mean + 2 * std_dev)]
    return magnitudes

def get_rpm(data: list, radius: float, fps: float, mag_scale_factor: float = math.e, real_rpm: float = None) -> tuple:

    if data.size == 0:
        return 0
    
    rpms = []
    errors = []
    magnitudes = []
    # WAAAAY down the line: this is O(k*n²) which is not very fast
    # 1. could unroll this loop into 2 and use some shenanigans to parallelize it
    # 2. could also write a shader for our tiny RPi GPU as the reads and writes are independent
    for vector in data:
        mag = math.sqrt(vector[0]**2 + vector[1]**2)
        magnitudes.append(mag)

    filtered_magnitudes = filter_magnitudes(magnitudes)
    mag_avg = np.average(filtered_magnitudes)

    vel = mag_avg*mag_scale_factor
    frequency = calculate_frequency(vel, radius, fps)
    rpm = 60 * frequency

    if real_rpm is not None:
        error = calculate_error_percentage(rpm, real_rpm)
        errors.append(error)
    
    rpms.append(rpm)

    return (rpms, errors)

if __name__ == '__main__':

    rpms = []
    errors = []
    fps = 10
    pixel_radius = 100
    real_rpm = 13

    avg_rpm = round(np.average(rpms), 2)
    avg_error = round(np.average(errors), 2)
    avg_error_from_real = calculate_error_percentage(avg_rpm, real_rpm)

    for index, element in enumerate(rpms):
        print('RPM:', rpms[index], f'Error: {errors[index]}%')
    print(f'Average rpm: {avg_rpm}')
    print(f'Average RPM error percentage from real RPM: {avg_error_from_real}%')
    print(f'Average of all error percentages: {avg_error}%')
