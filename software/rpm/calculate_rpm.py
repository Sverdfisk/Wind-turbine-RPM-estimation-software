import math
import numpy as np
from . import utils


def view_angle_scaling(
    ground_to_turbine_angle: float, perspective_rotation_angle: float
) -> float:
    # Find the plane normal vector of the turbine
    nx = math.cos(ground_to_turbine_angle) * \
        math.sin(perspective_rotation_angle)
    ny = math.cos(ground_to_turbine_angle) * \
        math.cos(perspective_rotation_angle)
    nz = math.sin(ground_to_turbine_angle)

    turbine_normal = np.array([nx, ny, nz])
    viewing_angle = np.array([0, 1, 0])

    # Find the scaling factor of the measurements
    angle_scale = np.dot(turbine_normal, viewing_angle)
    rpm_scaling_factor = 1 / angle_scale
    return rpm_scaling_factor


def calculate_frequency(velocity: float, radius: int, fps: float) -> float:
    # velocity is in pixels per frame
    # units: (pixels / frame) * (frames / second) / pixels ) = 1/s = rad/s
    ang_vel = (velocity * fps) / radius
    freq = ang_vel / (2 * math.pi)  # unit: 1/s
    return freq


def filter_magnitudes(magnitudes: list[float]) -> list[float]:
    magnitudes = np.array(magnitudes)
    std_dev = np.std(magnitudes)
    mean = np.mean(magnitudes)

    # Filter elements within two standard deviations
    magnitudes = magnitudes[
        (magnitudes >= mean - 2 * std_dev) & (magnitudes <= mean + 2 * std_dev)
    ]
    return magnitudes


def get_rpm_from_flow_vectors(velocity_vectors: list, radius, fps: float) -> tuple:
    if velocity_vectors.size == 0:
        return None

    magnitudes = []
    for vector in velocity_vectors:
        mag = math.sqrt(vector[0] ** 2 + vector[1] ** 2)
        magnitudes.append(mag)

    filtered_magnitudes = filter_magnitudes(magnitudes)
    vel = np.average(filtered_magnitudes)

    rpm = 60 * calculate_frequency(vel, radius, fps)
    return rpm


if __name__ == "__main__":
    rpms = []
    errors = []
    fps = 10
    pixel_radius = 100
    real_rpm = 13

    utils.print_statistics(rpms, errors)
