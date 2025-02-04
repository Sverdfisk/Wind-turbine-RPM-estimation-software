import math

data = [[-2.6827393, 0.85583496], [0.5624485, -2.4189186], [2.032364, 1.5400848], [2.3854752, 1.7025433], [-3.6663742, 0.9887543]], [[4.318115, 4.2935143], [2.589962, -5.564888], [2.7539425, -6.683098], [4.6326447, 5.055702], [-4.68499, -21.659775]],[[-2.1736145, -0.06526947], [1.5017014, -1.8979301], [1.3080368, 2.0414696], [1.9634552, -2.101715], [1.5410461, 2.2659721]],[[1.6093292, 3.2220116], [2.7347183, -2.7369652], [-4.1615067, -0.76732635], [3.1675072, -3.0552826], [2.1065369, 3.9619637]],[[-0.7155762, -0.43344116], [0.32800293, 0.61196136], [0.6070328, -0.51979446], [0.457016, 1.4143677], [1.3553371, -0.83041954]],[[-2.8198357, -0.92411804], [2.2038803, -1.4301224], [0.50509644, 2.379959], [2.4137268, -1.4809341], [0.9078064, 2.6945038]],[[1.8644447, -1.107647], [0.3713684, 1.835823], [-1.4758186, -0.22117615], [2.1772194, -1.3119583], [0.18041992, 2.1361923]]

#data contains a sequence of motion vectors for each frame
def get_signs(mat):
    signs = []
    for vec in block:
        sign_x = math.copysign(1, vec[0])
        sign_y = math.copysign(1, vec[1])
        signs.append([sign_x, sign_y])
    return signs

def find_pairs_and_remove_duplicates(signs):
    equalpairs = []
    #Select a pair
    for first_index, pair in enumerate(signs):
        # break if we're over halfway as we will just mirror the previous results
        if first_index > len(signs)/2:
            break

        # check the rest of the list if we find equals
        for second_index, other_pair in enumerate(signs):
            if pair == other_pair:
                equalpairs.append([first_index, second_index])

    equalpairs_no_duplicates = []
    for i in equalpairs:
        if i[0] == i[1]:
            pass
        else:
            equalpairs_no_duplicates.append(i)
    return equalpairs_no_duplicates

def group_pairs(pairs):
    vectors_grouped = []
    for pair in pairs:
        first_idx = pair[0]
        second_idx = pair[1]
        group = [block[first_idx], block[second_idx]]
        vectors_grouped.append(group)
    return vectors_grouped

rpms = []
fps = 300
frame_time = 1/fps
pixel_radius = 50

for block in data:
    signs = get_signs(block)
    out = find_pairs_and_remove_duplicates(signs)
    vectors_grouped = group_pairs(out)
    avg_vectors = []

    for pair in vectors_grouped:
        x_avg = (pair[0][0] + pair[1][0])/2
        y_avg = (pair[0][1] + pair[1][1])/2
        avg_vectors.append([round(x_avg, 4), round(y_avg, 4)])

    avg_vectors.append(block[1])

    magnitudes = []
    for vector in avg_vectors:
        mag = round(math.sqrt(vector[0]**2 + vector[1]**2), 3)
        magnitudes.append(mag)

    angular_velocity = magnitudes[0]/(pixel_radius*frame_time)
    period = (2*math.pi)/angular_velocity
    rpm = round(period * 60, 3)
    rpms.append(rpm)

avg_rpm = sum(rpms)/len(rpms)
print(f'rpms: {", ".join(str(x) for x in rpms)}')
print(f'Average rpm: {avg_rpm}')