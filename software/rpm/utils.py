import numpy as np
import json


def calculate_error_percentage(
    measured_value: float | None, actual_value: float | None
) -> float | None:
    if actual_value is None:
        return None

    if measured_value is not None:
        error_percentage = abs(measured_value - actual_value) / actual_value * 100
    else:
        error_percentage = None
    return error_percentage


def print_statistics(
    rpms: list,
    errors: list,
    real_rpm: float | None = None,
    rounding_factor: int = 2,
    verbose: bool = False,
) -> None:
    avg_rpm = float(round(np.average(rpms), rounding_factor))

    if real_rpm is not None:
        avg_error = round(np.average(errors), rounding_factor)
        avg_error_from_real = calculate_error_percentage(avg_rpm, real_rpm)

        if verbose:
            for index, _ in enumerate(rpms):
                print(
                    "RPM:",
                    round(rpms[index], rounding_factor),
                    f"Error: {round(errors[index], rounding_factor)}%",
                )

        print(f"Average rpm: {avg_rpm}")
        print(f"Average RPM error percentage from real RPM: {avg_error_from_real}%")
        print(f"Average of all error percentages: {avg_error}%")

    else:
        avg_error = None
        avg_error_from_real = None
        if verbose:
            for index, _ in enumerate(rpms):
                print("RPM:", round(rpms[index], rounding_factor))

        print(f"Average rpm: {avg_rpm}")

    return None


def parse_json(file_path: str) -> dict:
    with open(file_path) as config_file:
        params = json.load(config_file)
        return params


def write_output(
    turbine_id: int, run_number: int, rpms: list[float], real_rpm: int | None = None
):
    with open(f"runs/run_turbine{str(turbine_id)}.csv", "a") as output_file:
        output_file.write(
            f"{run_number}, {np.average(rpms)}, {
                calculate_error_percentage(float(np.average(rpms)), real_rpm)
            }\n"
        )
