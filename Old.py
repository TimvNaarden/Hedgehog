import time

import cv2
import numpy as np
import requests

# URL of the MJPEG stream
url = "http://root:root@192.168.2.57/mjpg/video.mjpg"

# Open a connection to the MJPEG stream
stream = requests.get(url, stream=True)
if stream.status_code == 200:
    bytes_stream = bytes()
    # Create VideoWriter object to save the video
    frame_width = 640  # adjust as needed
    frame_height = 480  # adjust as needed
    out = cv2.VideoWriter(
        "output.avi", cv2.VideoWriter_fourcc(*"MJPG"), 30.0, (frame_width, frame_height)
    )

    # Variables for frame rate control
    expected_frame_interval = 1 / 30.0  # target interval between frames (in seconds)
    last_time = time.time()  # initialize last frame time

    for chunk in stream.iter_content(chunk_size=1024):
        bytes_stream += chunk
        a = bytes_stream.find(b"\xff\xd8")
        b = bytes_stream.find(b"\xff\xd9")
        if a != -1 and b != -1:
            jpg = bytes_stream[a : b + 2]
            bytes_stream = bytes_stream[b + 2 :]
            frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
            if frame is not None:
                # Calculate time difference from last frame
                current_time = time.time()
                delta_time = current_time - last_time

                if delta_time >= expected_frame_interval:
                    out.write(frame)
                    last_time = current_time

                # Adjust to prevent high CPU usage in case frames are processed faster
                time.sleep(max(0, expected_frame_interval - delta_time))

    out.release()
else:
    print(f"Failed to open stream. Status code: {stream.status_code}")
