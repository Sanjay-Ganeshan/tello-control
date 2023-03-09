import time
from .autonomous import DroneIPC, DroneState, CAMERA_W, CAMERA_H
import cv2

def main():
    frames_per_second = 30
    output_filename = "/tmp/dronevideo.avi"
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    frame_size = (CAMERA_W, CAMERA_H)
    video_writer = cv2.VideoWriter(
       output_filename,
       fourcc,
       frames_per_second,
       frame_size,
    )
    show_frame = True

    ms_per_iteration = 1000.0 / frames_per_second
    cap = cv2.VideoCapture(0)
    with DroneIPC() as ipc:
        while True:
            start_ts = time.perf_counter()
            frame = ipc.get_frame()
            if show_frame:
              cv2.imshow('writer', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
              break
            video_writer.write(frame)
            end_ts = time.perf_counter()
            elapsed_ms = end_ts - start_ts
            wait_ms = max(0, ms_per_iteration - elapsed_ms)
            time.sleep(wait_ms / 1000.0)
    cap.release()
    video_writer.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()