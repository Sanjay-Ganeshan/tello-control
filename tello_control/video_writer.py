import time
from .autonomous import DroneIPC, DroneState, CAMERA_W, CAMERA_H
import cv2

def main():
    frames_per_second = 60
    show_frame = False

    ms_per_iteration = 1000.0 / frames_per_second
    cap = cv2.VideoCapture(0)
    with DroneIPC() as ipc:
        while True:
            start_ts = time.perf_counter()
            _, frame = cap.read()
            frame = cv2.resize(frame, (CAMERA_W, CAMERA_H))
            if show_frame:
              cv2.imshow('writer', frame)
              if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            ipc.save_frame(frame)
            end_ts = time.perf_counter()
            elapsed_ms = end_ts - start_ts
            wait_ms = max(0, ms_per_iteration - elapsed_ms)
            time.sleep(wait_ms / 1000.0)
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()