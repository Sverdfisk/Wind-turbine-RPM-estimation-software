import cv2 as cv
from rpm import opticalflow as flow

# --------Keep this file short!--------

# Feed configuration
feed_path = '/dev/video2'
crop_points = [[100,250],[100,250]]
crosshair_size = [20,20]

feed = flow.opticalflow(feed_path, crop_points, crosshair_size)

while(1):
    data, image = feed.get_optical_flow_vectors()
    flow_image = feed.draw_optical_flow(image, data[0], data[1])

    cv.imshow('Camera feed', flow_image)
    k = cv.waitKey(30) & 0xff
    if k == 27:
        break