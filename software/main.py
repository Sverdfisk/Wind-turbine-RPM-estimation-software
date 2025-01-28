import cv2 as cv
import numpy as np
from rpm import opticalflow as flow

# Keep this file short


feed_path = '/dev/video2'
feed = flow.opticalflow(feed_path)

while(1):
    #crop_points = [[0,200],[0,200]]
    feed.set_crop_points()
    frame = feed.get_frame()
    mask = np.zeros_like(frame)
    data = feed.get_optical_flow_vectors(frame)
    optical_flow = feed.get_optical_flow_vectors(frame)
    mask, flow_image = feed.draw_optical_flow(mask, frame, data[0], data[1], overwrite=False)

    cv.imshow('Camera feed', flow_image)
    k = cv.waitKey(30) & 0xff
    if k == 27:
        break
