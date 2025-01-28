import numpy as np
import cv2 as cv

maskpoints = []

def set_shi_tomasi_params(maxCorners = 100, 
                        qualityLevel = 0.1, 
                        minDistance = 9, 
                        blockSize = 3):
    return locals()

def set_lucas_kanade_params(winSize = (15, 15), 
                            maxLevel = 2, 
                            criteria = (cv.TERM_CRITERIA_EPS | cv.TERM_CRITERIA_COUNT, 10, 0.03)):
    return locals()

def draw_flow_from_points(mask, frame, points_0, points_1, status, 
                          colors = np.random.randint(0, 255, (100, 3))):

    # Select good points
    if points_1 is not None:
        good_new = points_1[status==1]
        good_old = points_0[status==1]

    # draw the tracks
    for i, (new, old) in enumerate(zip(good_new, good_old)):
        a, b = new.ravel()
        c, d = old.ravel()
        mask = cv.line(mask, (int(a), int(b)), (int(c), int(d)), colors[i].tolist(), 2)
        frame = cv.circle(frame, (int(a), int(b)), 5, colors[i].tolist(), -1)

    return frame, mask, good_new


def translate_coords_to_centre(image_height, image_width, sizex = 0, sizey = 0):
    centre = [image_height/2, image_width/2]
    x_left = int(centre[1]-sizex)
    x_right = int(centre[1]+sizex)
    y_top = int(centre[0]-sizey)
    y_bottom = int(centre[0]+sizey)
    return [x_left, x_right, y_top, y_bottom]


def generate_mask_matrix(image, size):
    height, width, channels = image.shape
    mask = np.full((height, width), 255, dtype=np.uint8)
    x_left, x_right, y_top, y_bottom = translate_coords_to_centre(height, width, sizex = size[0], sizey = size[1])
    global maskpoints
    maskpoints = [x_left, x_right, y_top, y_bottom]
    print(maskpoints[0],':',maskpoints[1],',',maskpoints[2],':',maskpoints[3])
    mask[y_top:y_bottom, x_left:x_right] = 0
    return mask


def get_optical_flow(video_feed_path,
                     st_params, 
                     lk_params, 
                     crop_points = None
                        ):
    # read a frame
    feed = cv.VideoCapture(video_feed_path)
    ret, old_frame = feed.read()

    if crop_points is not None:
        old_frame = old_frame[crop_points[0][0]:crop_points[0][1], 
                            crop_points[1][0]:crop_points[1][1]]

    feature_mask = generate_mask_matrix(old_frame, [30,30])

    # Convert to grayscale for algorithmic purposes
    old_gray = cv.cvtColor(old_frame, cv.COLOR_BGR2GRAY)

    mask = np.zeros_like(old_frame)


    while(1):

        #Move this out of the while loop for more persistent tracking
        #mask = np.zeros_like(old_frame)

        #This is the updating frame, we need at least 2 frames to start the algorithm
        ret, frame = feed.read()

        if crop_points is not None:
            frame = frame[crop_points[0][0]:crop_points[0][1], 
                        crop_points[1][0]:crop_points[1][1]]
            
        if not ret:
            print('No frames grabbed!')
            break

        # find features in our old grayscale frame. feature mask is dynamic but manual
        p0 = cv.goodFeaturesToTrack(old_gray, mask = feature_mask, **st_params)
        frame_gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

        # calculate optical flow
        p1, st, err = cv.calcOpticalFlowPyrLK(old_gray, frame_gray, p0, None, **lk_params)

        #Reassign to itself as we want to overwrite the old frame with new drawings on top
        frame, mask, good_new = draw_flow_from_points(mask, frame, p0, p1, st)
        # Add the mask over the frame, creating a new image
        img = cv.add(frame, mask)
        red = [0,0,255]
        fromx, tox, fromy, toy = maskpoints
        cv.circle(img, (fromx,toy), 4, red, -1)
        cv.circle(img, (fromx,fromy), 4, red, -1)
        cv.circle(img, (tox,fromy), 4, red, -1)
        cv.circle(img, (tox,toy), 4, red, -1)

        # Show/write frame
        cv.imshow('Camera feed', img)
        k = cv.waitKey(30) & 0xff
        if k == 27:
            break

        # Update the previous frame and previous points
        old_gray = frame_gray.copy()
        p0 = good_new.reshape(-1, 1, 2)

    cv.destroyAllWindows()
 

if __name__ == '__main__':
    # Set this and pass as an argument in calculate_optical_flow() if other drawing colors are desired
    # colors=np.random.randint(0, 255, (100, 3))
    #     
    # fromx = 140
    # tox = 380
    # fromy = 170
    # toy = 470
    # coords = [[fromx,tox], [fromy,toy]]

    video_feed_path = '/dev/video2'
    stparams = set_shi_tomasi_params()
    lkparams = set_lucas_kanade_params()
    crop_points = [[150,400],[200,500]]
    get_optical_flow(video_feed_path, stparams, lkparams, crop_points)
