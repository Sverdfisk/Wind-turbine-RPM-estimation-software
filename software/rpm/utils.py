import numpy as np
import math
import json

def calculate_error_percentage(measured_value: float, actual_value: float) -> float:
    if actual_value is None:
        return None
    error_percentage = abs(measured_value - actual_value) / actual_value * 100
    return error_percentage

def view_angle_scaling(ground_to_turbine_angle: float, perspective_rotation_angle:float) -> float:
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

def print_statistics(rpms: list, errors: list, real_rpm: float = None, rounding_factor: int = 2, verbose: bool = False) -> None:
    avg_rpm = round(np.average(rpms), rounding_factor)

    if real_rpm is not None:
        avg_error = round(np.average(errors), rounding_factor)
        avg_error_from_real = calculate_error_percentage(avg_rpm, real_rpm)

        if verbose:
            for index, element in enumerate(rpms):
                print('RPM:', round(rpms[index], rounding_factor), f'Error: {round(errors[index], rounding_factor)}%')
        
        print(f'Average rpm: {avg_rpm}')
        print(f'Average RPM error percentage from real RPM: {avg_error_from_real}%')
        print(f'Average of all error percentages: {avg_error}%')

    else:
        avg_error = None
        avg_error_from_real = None
        if verbose:
            for index, element in enumerate(rpms):
                print('RPM:', round(rpms[index], rounding_factor))

        print(f'Average rpm: {avg_rpm}')

    return None

def parse_json(file_path: str) -> dict:
    with open(file_path) as config_file:
        params = json.load(config_file)
        return params

def write_output(turbine_id: int, run_number: int, rpms: list, real_rpm: int = None):
    with open(f"runs/run_turbine{str(turbine_id)}.csv", "a") as output_file:
        output_file.write(f"{run_number}, {np.average(rpms)}, {calculate_error_percentage(np.average(rpms), real_rpm)}\n")
