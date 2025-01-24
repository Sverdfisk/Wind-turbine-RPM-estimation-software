import cv2

#We want the inverse of the crop coordinates.
#Order: Clockwise. bottom left, top left, top right, bottom right 
def transform_crop_coords_to_absolute(full_height, full_width, fromx, tox, fromy, toy):

    #Flip the y axis, and the coordinates are now in a "normal" coordinate system
    bottom_left = [fromx, full_height-toy]
    top_left = [fromx, full_height-fromy]
    top_right = [tox, full_height-fromy]
    bottom_right = [tox, full_height-toy]

    return [bottom_left, top_left, top_right, bottom_right]


def crop(image, fromx, tox, fromy, toy):
    crop = image[fromy:toy, fromx:tox]
    height, width, channels = image.shape
    crop_coords = transform_crop_coords_to_absolute(height, width, fromx, tox, fromy, toy)
    return crop, crop_coords


if __name__ == '__main__':

    print('\n Running test case:')

    frompoint = input("Top-left coordinate: ").split(',')
    topoint = input("Bottom-right coordinate: ").split(',')
    fromx = int(frompoint[0])
    fromy = int(frompoint[1])
    tox = int(topoint[0])
    toy = int(topoint[1])

    #fromx = 100
    #fromy = 169
    #tox = 500
    #toy = 269

    original_image = cv2.imread('test.jpg')
    cropped_image, coords = crop(original_image, fromx, tox, fromy, toy)
    cv2.imwrite("cropped_image.jpg", cropped_image)

    #Save a copy of the original with red dots marking the crop points for cross reference
    red = [0,0,255]
    cv2.circle(original_image, (fromx,toy), 4, red, -1)
    cv2.circle(original_image, (fromx,fromy), 4, red, -1)
    cv2.circle(original_image, (tox,fromy), 4, red, -1)
    cv2.circle(original_image, (tox,toy), 4, red, -1)



    cv2.imwrite('test_crop_points_marked.jpg', original_image)

    height, width, channels = original_image.shape
    coords = transform_crop_coords_to_absolute(height, width, fromx, tox, fromy, toy)
    print(coords)