import math
import numpy as np
from . import utils


def view_angle_scaling(
    ground_to_turbine_angle: float, perspective_rotation_angle: float
) -> float:
    """
    Find the angle between the turbine and the camera based on the dimensions of the cropped region.
    The measured vectors are scaled by some factors so that, on average,
    they will be the same length/magnitude as they would be head-on.

    Args:
        ground_to_turbine_angle (float): angle from the ground/camera to the turbine hub.
        perspective_rotation_angle (float): horizontal angle (i.e yaw angle) of the turbine hub relative to the camera.

    """
    # Find the plane normal vector of the turbine
    nx = math.cos(ground_to_turbine_angle) * math.sin(perspective_rotation_angle)
    ny = math.cos(ground_to_turbine_angle) * math.cos(perspective_rotation_angle)
    nz = math.sin(ground_to_turbine_angle)

    turbine_normal = np.array([nx, ny, nz])
    viewing_angle = np.array([0, 1, 0])

    # Find the scaling factor of the measurements
    angle_scale = np.dot(turbine_normal, viewing_angle)
    rpm_scaling_factor = 1 / angle_scale
    return rpm_scaling_factor


def calculate_frequency(velocity: float, radius: int, fps: float) -> float:
    """
    Converts vectors to frequency. Does some spooky math to get there.
    Note: velocity is in pixels per frame, therefore normal angular frequency doesn't work.

    Args:
        velocity (float): measured magnitude/velocity vector
        radius (int): radius of the cropped region
        fps (float): fps of the feed.

    """

    # Units: (pixels / frame) * (frames / second) / pixels ) = 1/s = rad/s
    ang_vel = (velocity * fps) / radius
    freq = ang_vel / (2 * math.pi)  # unit: 1/s
    return freq


def filter_magnitudes(magnitudes: np.ndarray) -> np.ndarray:
    magnitudes = np.array(magnitudes)
    std_dev = np.std(magnitudes)
    mean = np.mean(magnitudes)

    # Filter elements within two standard deviations
    magnitudes = magnitudes[
        (magnitudes >= mean - 2 * std_dev) & (magnitudes <= mean + 2 * std_dev)
    ]
    return magnitudes


def get_rpm_from_flow_vectors(
    velocity_vectors: np.ndarray, radius, fps: float
) -> None | float:
    if velocity_vectors.size == 0:
        return None

    magnitudes = []
    for vector in velocity_vectors:
        mag = math.sqrt(vector[0] ** 2 + vector[1] ** 2)
        magnitudes.append(mag)

    filtered_magnitudes = filter_magnitudes(np.array(magnitudes))
    vel = np.average(filtered_magnitudes)

    rpm = 60 * calculate_frequency(vel, radius, fps)
    return rpm


def calculate_rpm_from_frame_time(frame_time: int, fps: float) -> float:
    real_time = frame_time / fps
    # Any blade triggers a tick, luckily they
    # are evenly spaced 120 degrees apart
    adjusted_ticktime_seconds = real_time * 3
    return 60 / adjusted_ticktime_seconds


if __name__ == "__main__":
    rpms = []
    errors = []
    fps = 10
    pixel_radius = 100
    real_rpm = 13

    utils.print_statistics(rpms, errors)
