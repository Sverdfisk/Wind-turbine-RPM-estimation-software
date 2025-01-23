def get_arc_length(ylen, xlen):
    return 1

def generate_radius_function(xrad, yrad):
    pass

def get_rotation_angle(arc_length, radius_function):
    pass

def calculate_rpm(total_size, coords, frame_time):
    height = total_size[0]
    width = total_size[1]
    radius_y = height/2
    radius_x = width/2

    arc_length = get_arc_length(radius_x, radius_y)
    radius_function = generate_radius_function(radius_x, radius_y)
    rotation_angle = get_rotation_angle(arc_length, radius_function)

    angular_frequency = rotation_angle / frame_time
    