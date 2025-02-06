#Slave script. Formats data for testing with calculate_rpm.py.
import re

def sanitize_file(input_file_path: str, output_file_path: str):
    with open(input_file_path, 'r') as infile:
        lines = infile.readlines()
    
    sanitized_lines = []
    for line in lines:
        # Remove any leading/trailing whitespace from the line
        line = line.strip()
        # Skip lines that are empty or contain only empty brackets
        if line == '' or line == '[]':
            continue
        
        # Replace the contents of a bracket. This regex allows for extra whitespace after the '[' and before the ']'
        # It captures the first number and the second number (which may include signs, decimals, or exponential notation)
        # and replaces the whitespace between them with a comma.
        line = re.sub(r'\[\s*([-\d\.e]+)\s+([-\d\.e]+)\s*\]', r'[\1,\2]', line)
        
        # If the line ends with a closing bracket, add a comma after it if not already present
        if line.endswith(']') and not line.endswith('],'):
            line += ','
        
        sanitized_lines.append(line)
    
    # Join all sanitized lines into one single line (removing any newline characters)
    result = ''.join(sanitized_lines)
    
    with open(output_file_path, 'w') as outfile:
        outfile.write(result)
    


if __name__ == '__main__':
    input_file = "data/data.txt"
    output_file = "data/sanitized_data.txt"
    sanitize_file(input_file, output_file)