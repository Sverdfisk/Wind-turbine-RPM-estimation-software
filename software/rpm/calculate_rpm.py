import math
import numpy as np
from . import utils


def calculate_frequency(velocity: float, radius: float, fps: float) -> float:
    # velocity is in pixels per frame
    # units: (pixels / frame) * (frames / second) / pixels ) = 1/s = rad/s
    ang_vel = (velocity * fps) / radius 
    freq = ang_vel / (2 * math.pi) # unit: 1/s
    return freq

def filter_magnitudes(magnitudes: list) -> list:

    magnitudes = np.array(magnitudes)
    std_dev = np.std(magnitudes)
    mean = np.mean(magnitudes)

    # Filter elements within two standard deviations
    magnitudes = magnitudes[(magnitudes >= mean - 2 * std_dev) & (magnitudes <= mean + 2 * std_dev)]
    return magnitudes

def get_rpm(data: list, radius: float, fps: float, real_rpm: float = None) -> tuple:
    if data.size == 0:
        return None
    
    magnitudes = []
    for vector in data:
        mag = math.sqrt(vector[0]**2 + vector[1]**2)
        magnitudes.append(mag)

    filtered_magnitudes = filter_magnitudes(magnitudes)
<<<<<<< Updated upstream
    mag_avg = np.average(filtered_magnitudes)

    vel = mag_avg
    frequency = calculate_frequency(vel, radius, fps)
    rpm = 60 * frequency
=======
    vel = np.average(filtered_magnitudes) / 0.463406
>>>>>>> Stashed changes

    return rpm

if __name__ == '__main__':

    rpms = []
    errors = []
    fps = 10
    pixel_radius = 100
    real_rpm = 13

    utils.print_statistics(rpms, errors)