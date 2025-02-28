import cv2 as cv
import numpy as np

yrange, xrange = (slice(0, 100), slice(100, 200))


def draw_opaque_region(base_frame, range, w1, w2):
    y_range, x_range = range
    print(yrange, xrange, base_frame)
    subregion = base_frame[y_range, x_range]
    white_rect = np.ones(subregion.shape, dtype=np.uint8) * 255
    res = cv.addWeighted(subregion, w1, white_rect, w2, 1.0)
    base_frame[yrange, xrange] = res
    return base_frame


def draw_active_quadrant(base_frame: np.ndarray) -> np.ndarray:
    quadrant_range = (yrange, xrange)
    print(quadrant_range)
    marked_quadrant = draw_opaque_region(base_frame, quadrant_range, 0.7, 0.3)
    return marked_quadrant


img = cv.imread("/home/ken/projects/windturbine/software/assets/lena.png")
print(img)
marked_frame = draw_active_quadrant(img)
cv.imshow("marked", marked_frame)
k = cv.waitKey(0) & 0xFF
if k == 27:
    cv.destroyAllWindows()
