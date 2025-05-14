import cv2

def display_video(video_path):
    # Open the video file
    cap = cv2.VideoCapture(video_path)

    # Check if the video was opened successfully
    if not cap.isOpened():
        print("Error: Could not open video file.")
        return

    # Loop to read and display frames
    while True:
        ret, frame = cap.read()

        # If the frame is read correctly, ret will be True
        if not ret:
            print("End of video or error reading frame.")
            break

        # Display the frame
        cv2.imshow('Video', frame)

        # Wait for 1 ms and check if the user presses 'q' to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the video capture object and close any open windows
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    video_path = "/dev/video1"
    display_video(video_path)

