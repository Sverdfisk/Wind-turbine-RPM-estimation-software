import math
import numpy as np

data = [[[5.199341,-1.2524891],[5.61541,-1.3162785],[-1.4206238,5.1766357],[-3.649849,-3.8041687],[-1.577713,5.58165],[4.0930176,-1.0685196],[-4.1719246,-4.121353],[-2.8851318,-2.995346],[-1.0052948,4.125992],[-4.1636887,-4.990158]],[[5.6987457,-0.82115173],[4.165207,-0.60250473],[5.2722626,-0.7978344],[-2.1619263,5.443054],[-3.2843437,-4.1398926],[-2.001236,4.9857025],[-1.6076508,3.9419556],[-3.6471825,-4.4845886],[-2.69339,-3.2832794],[-2.951624,-5.638321]],[[5.769745,-0.3467512],[5.3897095,-0.23635101],[-2.902691,-4.470215],[-3.1662598,-4.879547],[-2.640213,5.2093353],[4.1602173,-0.10952759],[-2.5101318,4.7225037],[-1.9981232,3.7550964],[-2.399414,-3.5085907],[-3.1934452,-5.4486847],[-2.8861084,5.7252655]],[[5.3194275,0.34890366],[5.7980347,0.29951668],[-2.5856419,-5.2349854],[4.2395935,0.30106735],[-2.3146248,-4.7506714],[-2.9311676,4.4317017],[-1.797802,-3.765915],[-3.2708282,4.876236],[-2.3274536,3.5427856],[-4.927231,4.5122986],[-2.5365944,-5.76886],[0.5368347,0.079200745]],[[5.6251373,1.1704388],[5.303421,0.8539829],[-2.042202,-5.452591],[-1.8003426,-4.9176025],[4.161087,0.708168],[-3.3655243,4.167328],[-1.403614,-3.967636],[-3.7757416,4.4766235],[-2.8032837,3.1679077],[-4.509796,4.4041595],[-2.194724,-5.9857635]],[[5.113327,1.5109596],[5.5309143,1.5648956],[-1.4058704,-5.61232],[3.9865265,1.1165543],[-1.4302444,-5.1360474],[-3.7689667,3.7085419],[-0.9319496,-4.1728516],[-3.0365143,2.9564056],[-4.2372284,4.001526],[-4.905121,4.2317963]],[[5.357483,2.209488],[4.9477997,2.0129738],[-0.665535,-5.3269043],[-0.6847954,-4.223709],[-0.649807,-5.7549286],[3.9227448,1.4448166],[-4.5888214,3.557846],[-4.1380157,3.212799],[-3.3630981,2.6141968],[-5.2775726,3.7311096]],[[4.7312317,2.4548988],[5.0182343,2.7889843],[-0.24349594,-5.3073044],[-0.09975815,-5.749817],[-5.0577545,3.0045013],[3.7664185,1.8543091],[-0.0448761,-4.2089005],[-4.478714,2.9064484],[-3.5754242,2.212265],[-5.802414,2.8186188]],[[-5.2916718,-0.4947052]],[[4.8167725,3.2440948],[4.4766846,2.9655495],[0.48985672,-5.7738876],[0.28482056,-5.310112],[3.437912,2.4413261],[-5.2904663,2.5568085],[-4.854431,2.2198792],[0.30728912,-4.243393],[-6.174301,1.9619293]],[[-3.8781433,1.728836],[-0.49397278,1.5021973]],[[4.371811,3.7861824],[4.068512,3.4895363],[1.2202148,-5.625519],[0.88282776,-5.305214],[3.344345,2.6195679],[-4.9437866,1.8197784],[-5.561722,1.8703003],[0.8599434,-4.10421],[-5.931305,2.6179657]],[[-4.191345,1.2823944],[-0.0016021729,5.920288]],[[4.00354,4.218651],[1.5755272,-5.5038834],[3.6908875,3.8237114],[1.4541245,-5.1803055],[1.2250671,-4.0451813],[2.9073944,3.0392914],[-5.646347,1.397232],[-5.1559753,1.3011932],[-6.3312225,1.2545776]],[[3.5236206,4.577305],[3.299759,4.2212753],[1.8867111,-5.051689],[2.2952347,-5.3019485],[-5.8033752,0.8016968],[1.5178528,-3.865181],[-5.274933,0.7433624],[2.6174774,3.3650742]],[[2.536869,-4.691139],[2.827057,4.523102],[2.6425934,-5.157181],[3.0604095,4.9046173],[1.9596939,-3.7119675],[2.1873016,3.602356]],[[2.4237213,5.3104935],[3.4104958,-4.661274],[3.0098953,-4.41951],[2.3010406,4.7641754],[1.8055725,3.735527],[2.2605133,-3.5370712]],[[-5.7244873,-0.7605438]],[[3.5457535,-4.0522575],[1.7434998,5.06958],[3.768898,-4.3895645],[1.9242554,5.5143204],[1.524353,3.904007],[2.6300125,-3.2397003],[-4.2108307,-0.6009979]],[[-5.5743637,-1.4376831],[-5.1428757,-1.3279877]],[[1.3771057,5.616722],[3.8185425,-3.726509],[1.2855682,5.2273865],[4.292343,-3.7879295],[3.078888,-2.810608],[0.94480896,4.0939865],[-4.0592422,-1.1624603]],[[-5.5342712,-1.9685822],[-4.95327,-1.7559052],[-5.944664,-2.5290833]],[[4.6790314,-3.32024],[0.7984009,5.309334],[0.71388245,5.7056046],[4.167633,-3.360447],[0.5543976,4.20372],[3.3879547,-2.493122],[-3.8742828,-1.5891113],[0.17562103,-4.519394]],[[-4.8329086,-2.271576],[-5.2510376,-2.588089]],[[5.002861,-2.9725208],[4.5480347,-2.792698],[0.06828308,4.2576904],[0.12413025,5.8110657],[3.575386,-2.1118584],[0.12846375,5.3298187]],[[-4.926056,-3.1276703],[-4.4757233,-2.8144684],[-3.5171432,-2.2551422]],[[5.25737,-2.3861027],[4.7977676,-2.364151],[-0.47988892,5.3454437],[3.7222824,-1.7777214],[-0.5451813,5.7611847],[-0.17955017,4.1819],[3.8765717,-39.49843]],[[-4.190468,-3.3128662],[-4.5026016,-3.732254],[-3.4197083,-2.5684967],[-4.8241158,-4.2002563]],[[5.463089,-1.7873688],[5.0431824,-1.6695404],[-0.957489,5.297165],[-1.1340485,5.6792297],[3.9707336,-1.4312325],[-0.72940063,4.190384]]]




#data contains a sequence of motion vectors for each frame
def get_signs(mat):
    signs = []
    for vec in mat:
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

    unique_pairs = []
    seen = set()
    for pair in equalpairs_no_duplicates:
        # Create a sorted tuple from the pair
        key = tuple(sorted(pair))
        if key not in seen:
            unique_pairs.append(pair)
            seen.add(key)

    return unique_pairs

def group_pairs(pairs):
    vectors_grouped = []
    for pair in pairs:
        first_idx = pair[0]
        second_idx = pair[1]
        group = [block[first_idx], block[second_idx]]
        vectors_grouped.append(group)
    return vectors_grouped

def calculate_frequency(velocity, radius, fps):
    # velocity is in pixels per frame
    # units: (pixels / frame) * (frames / second) / pixels ) = 1/s = rad/s
    ang_vel = (velocity * fps) / radius 
    freq = ang_vel / (2 * math.pi) # unit: 1/s
    return freq

rpms = []
fps = 10
frame_time = 1/fps
pixel_radius = 130
mag_scaling_factor = 2 # The vectors are not at the tip of the blade. Scale them by some weird factor to compensate

for block in data:
    signs = get_signs(block)
    out = find_pairs_and_remove_duplicates(signs)
    """
    print(out)
    print(signs)

    # out here is a list of paired indices.
    vectors_grouped = group_pairs(out)
    #These vectors are now grouped. 


    # 1. Remove the original indices (the ones in "out") from the big list. 
    # 1.1 first sanitize duplicates here
    all_pair_indexes = sorted({num for pair in out for num in pair}, reverse=True)
    print(all_pair_indexes)
    #Pop in reverse to not fuck up the indices
    for index in all_pair_indexes:
        block.pop(index)

    #2. get average of the grouped pairs

    #3. add the averaged vectors back into the block

    #4. after this is done, we should have "one big vector" (or something close to it) for each blade.

    print(out)
    print(block)
    print('\n\n',vectors_grouped,'\n\n')
    avg_vectors = []
    

    for pair in vectors_grouped:
        x_avg = (pair[0][0] + pair[1][0])/2
        y_avg = (pair[0][1] + pair[1][1])/2
        avg_vectors.append([round(x_avg, 4), round(y_avg, 4)])

    magnitudes = []
    for vector in avg_vectors:
        mag = round(math.sqrt(vector[0]**2 + vector[1]**2), 3)
        magnitudes.append(mag)

    mag_avg = (sum(magnitudes)/len(magnitudes)) if len(magnitudes) != 0 else 1
    """
    magnitudes = []
    for vector in block:
        mag = round(math.sqrt(vector[0]**2 + vector[1]**2), 3)
        magnitudes.append(mag)


    threshold = np.percentile(magnitudes, 95)
    mag_highest = []
    for i in magnitudes:
        if i >= threshold:
            mag_highest.append(i)

    #mag_highest = (x for x in magnitudes if x > threshold)
    mag_avg = sum(mag_highest)/len(mag_highest)

    vel = mag_avg*mag_scaling_factor

    #vel = pixels/frame
    #frame_time = seconds/frame

    frequency = calculate_frequency(vel, pixel_radius, fps)
    rpm = round(60 * frequency, 3)
    rpms.append(rpm)


avg_rpm = sum(rpms)/len(rpms)
print(f'rpms: {",\n ".join(str(x) for x in rpms)}')
print(f'Average rpm: {avg_rpm}')