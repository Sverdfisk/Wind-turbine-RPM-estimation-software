import cv2 as cv
from rpm import opticalflow as flow

# Keep this file short


feed_path = '/dev/video2'
feed = flow.opticalflow(feed_path)

while(1):
    #crop_points = [[0,200],[0,200]]
    feed.set_crop_points()
    frame = feed.get_frame()
    data = feed.get_optical_flow_vectors(frame)
    print(data[1]-data[0])
    #optical_flow = feed.get_optical_flow_vectors(frame)
    #img_out = feed.draw_optical_flow(frame, optical_flow)

    cv.imshow('Camera feed', frame)
    k = cv.waitKey(30) & 0xff
    if k == 27:
        break
