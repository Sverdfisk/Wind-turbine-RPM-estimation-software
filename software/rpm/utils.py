import numpy as np

def calculate_error_percentage(measured_value: float, actual_value: float) -> float:
    if actual_value is None:
        return None
    
    error_percentage = abs(measured_value - actual_value) / actual_value * 100
    return error_percentage

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