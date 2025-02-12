import cv2 as cv
import numpy as np

# 1) Load your image
img = cv.imread("assets/homography_test.png")
height, width, channels = img.shape
diff = (height-width)


# 2) Define corner points in the *source* image
pts_src = np.float32([
    [0,         0         ],   # top-left
    [width - 1, 0         ],   # top-right
    [width - 1, height - 1],   # bottom-right
    [0,         height - 1]    # bottom-left
])

pts_dst = np.float32([
    [0, 0   ],   # top-left in the new image
    [width+diff, 0    ],   # top-right in the new image
    [width+diff, height],  # bottom-right in the new image
    [0,     height]   # bottom-left in the new image
])

# 4) Compute the perspective transform (homography)
H = cv.getPerspectiveTransform(pts_src, pts_dst)

# 5) Apply the warp
warped = cv.warpPerspective(img, H, (height, height))

# 6) Show the result
cv.imshow("Original", img)
cv.imshow("Warped to Square", warped)
cv.waitKey(0)
cv.destroyAllWindows()
