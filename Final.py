import time
from datetime import datetime

import cv2
import numpy as np
import requests

url = "http://root:root@192.168.2.57/mjpg/video.mjpg"
fps = 30.0
fpsRate = 1 / fps
byteStream = bytes()
stream = requests.get(url, stream=True)
frameBuffer = []
framesAfterMoved = 0
moved = 0


def bufferAdd(inputFrame):
    if len(frameBuffer) == (fps * 5):
        frameBuffer.pop(0)
    frameBuffer.append(inputFrame)


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
                frame_blurred = cv2.GaussianBlur(frame, (21, 21), 0)
                fgmask = fgbg.apply(frame_blurred)
                _, thresh = cv2.threshold(fgmask, 240, 255, cv2.THRESH_BINARY)
                non_zero_ratio = np.count_nonzero(thresh) / thresh.size

                if non_zero_ratio > 0.01:
                    if moved == 0:
                        print(str(len(frameBuffer)) + "Frames Buffered")
                        print("Recording")
                        now = datetime.now()
                        timeFormatted = now.strftime("%Y-%m-%d %H:%M")
                        out = cv2.VideoWriter(
                            timeFormatted + ".avi",
                            cv2.VideoWriter_fourcc(*"MJPG"),
                            fps,
                            (640, 480),
                        )
                        while len(frameBuffer) != 0:
                            out.write(frameBuffer[0])
                            frameBuffer.pop(0)
                        moved = 1

                if moved:
                    framesAfterMoved += 1
                    out.write(frame)
                    if framesAfterMoved == 60 * fps:
                        framesAfterMoved = 0
                        moved = 0
                        print("Done Recording")
                        time.sleep(900)
                else:
                    bufferAdd(frame)

                lastRun = time.time()
                if (time.time() - lastRun) < fpsRate:
                    time.sleep(max(0, fpsRate - (time.time() - lastRun)))

                cv2.imshow("Hedgehogs", frame)
                cv2.waitKey(1)
else:
    print("Could not Connect")

# Release resources
out.release()
cv2.destroyAllWindows()
