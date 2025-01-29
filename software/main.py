import cv2 as cv
from rpm import opticalflow as flow

# --------Keep this file short!--------
feed_path = '/dev/video2'

# Second argument is crop points. format: [[y1,y2], [x1,x2]]
crop_points = [[100,300],[100,300]]
feed = flow.opticalflow(feed_path, crop_points)

while(1):
    data, frame = feed.get_optical_flow_vectors()
    mask, flow_image = feed.draw_optical_flow(frame, data[0], data[1], overwrite=False)
 
    cv.imshow('Camera feed', flow_image)
    k = cv.waitKey(30) & 0xff
    if k == 27:
        break
