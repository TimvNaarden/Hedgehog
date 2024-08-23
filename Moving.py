import time

import cv2
import numpy as np
import requests

url = "http://root:root@192.168.2.57/mjpg/video.mjpg"
fpsRate = 1 / 30.0
byteStream = bytes()
stream = requests.get(url, stream=True)

# Initialize the background subtractor
fgbg = cv2.createBackgroundSubtractorMOG2(
    history=500, varThreshold=50, detectShadows=True
)

if stream.status_code == 200:
    print("Connected")
    lastRun = time.time()

    for chunk in stream.iter_content(chunk_size=1024):
        byteStream += chunk
        a = byteStream.find(b"\xff\xd8")
        b = byteStream.find(b"\xff\xd9")
        if a != -1 and b != -1:
            jpg = byteStream[a : b + 2]
            byteStream = byteStream[b + 2 :]
            frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)

            if frame is not None:
                # Apply Gaussian blur to reduce noise
                frame_blurred = cv2.GaussianBlur(frame, (21, 21), 0)

                # Apply the background subtractor
                fgmask = fgbg.apply(frame_blurred)

                # Threshold the mask to remove shadows and noise
                _, thresh = cv2.threshold(fgmask, 240, 255, cv2.THRESH_BINARY)

                # Calculate the ratio of non-zero pixels in the thresholded image
                non_zero_ratio = np.count_nonzero(thresh) / thresh.size

                # Detect movement if the ratio exceeds the threshold
                if non_zero_ratio > 0.01:  # Adjust this threshold based on your needs
                    print("Movement detected")

                # Control the frame rate
                if (time.time() - lastRun) < fpsRate:
                    time.sleep(max(0, fpsRate - (time.time() - lastRun)))
                lastRun = time.time()

else:
    print("Could not Connect")
