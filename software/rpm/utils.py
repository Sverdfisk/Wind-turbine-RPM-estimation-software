import numpy as np

def calculate_error_percentage(measured_value: float, actual_value: float) -> float:
    error_percentage = abs(measured_value - actual_value) / actual_value * 100
    return round(error_percentage, 2)

def print_statistics(rpms: list, errors: list, real_rpm: float) -> None:
    avg_rpm = round(np.average(rpms), 2)
    print(real_rpm)
    if real_rpm is not None:
        avg_error = round(np.average(errors), 2)
        avg_error_from_real = calculate_error_percentage(avg_rpm, real_rpm)
    else:
        avg_error = None
        avg_error_from_real = None

    for index, element in enumerate(rpms):
        print('RPM:', rpms[index], f'Error: {errors[index]}%')

    print(f'Average rpm: {avg_rpm}')
    print(f'Average RPM error percentage from real RPM: {avg_error_from_real}%')
    print(f'Average of all error percentages: {avg_error}%')

    return None