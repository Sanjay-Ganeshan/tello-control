import mmap
import numpy as np
import typing as T
from dataclasses import dataclass, field
import sys

CAMERA_W = 960
CAMERA_H = 720
CAMERA_C = 3

TAKEOFF   = 0b0000_0001
LAND      = 0b0000_0010
STREAMON  = 0b0000_0100
STREAMOFF = 0b0000_1000
EMERGENCY = 0b0001_0000

CONTROL_LENGTH_IN_BYTES = (
    # Flags
    1 + 
    # RC commands
    4
)


FRAME_LENGTH_IN_BYTES = (
    CAMERA_W * CAMERA_H * CAMERA_C
)

BUFFER_LENGTH = CONTROL_LENGTH_IN_BYTES + FRAME_LENGTH_IN_BYTES

def uint_to_int(number: np.uint8) -> int:
    return max(min(int(number.view(dtype=np.int8)), 100), -100)

def int_to_uint(number: int) -> np.uint8:
    return np.int8(max(min(number, 100), -100)).view(dtype=np.uint8)

@dataclass
class DroneState:
    land: bool = False
    takeoff: bool = False
    streamon: bool = False
    streamoff: bool = False
    emergency: bool = False
    left_right_vel: int = 0
    up_down_vel: int = 0
    fwd_back_vel: int = 0
    yaw_vel: int = 0

class DroneIPC:
    def __init__(self):
        self._arr = None
        self._shmem = None

    def __enter__(self) -> "DroneIPC":
        # This function is only called once, so it can be expensive
        if sys.platform == "win32":
            self._shmem = mmap.mmap(-1, BUFFER_LENGTH, tagname="droneipc")
        else:
            self._shmem = bytearray(BUFFER_LENGTH)
        self._arr = np.frombuffer(self._shmem, dtype=np.uint8)
        return self
    
    def __exit__(self, exc_type, exc, tb):
        if sys.platform == "win32":
            self._shmem.close()
    
    def save_state(self, state: DroneState) -> None:
        commands = np.uint8(
            LAND if state.land else 0 +
            TAKEOFF if state.takeoff else 0 +
            STREAMON if state.streamon else 0 +
            STREAMOFF if state.streamoff else 0 +
            EMERGENCY if state.emergency else 0
        )

        arr = np.zeros((CONTROL_LENGTH_IN_BYTES,), dtype=np.uint8)
        arr[0] = commands
        arr[1] = int_to_uint(state.left_right_vel)
        arr[2] = int_to_uint(state.up_down_vel)
        arr[3] = int_to_uint(state.fwd_back_vel)
        arr[4] = int_to_uint(state.yaw_vel)
        np.copyto(self._arr[:CONTROL_LENGTH_IN_BYTES], arr)

    def get_state(self) -> DroneState:
        arr = np.zeros((CONTROL_LENGTH_IN_BYTES,), dtype=np.uint8)
        np.copyto(arr, self._arr[:CONTROL_LENGTH_IN_BYTES])
        commands = arr[0]
        return DroneState(
            land = (commands & LAND) > 0,
            takeoff = (commands & TAKEOFF) > 0,
            streamon = (commands & STREAMON) > 0,
            streamoff = (commands & STREAMOFF) > 0,
            emergency = (commands & EMERGENCY) > 0,
            left_right_vel = uint_to_int(arr[1]),
            up_down_vel = uint_to_int(arr[2]),
            fwd_back_vel = uint_to_int(arr[3]),
            yaw_vel = uint_to_int(arr[4]),
        )

    def save_frame(self, frame: np.ndarray) -> None:
        if frame.shape == (CAMERA_H, CAMERA_W, CAMERA_C):
            np.copyto(self._arr[CONTROL_LENGTH_IN_BYTES:], frame.reshape((-1,)))

    def get_frame(self) -> np.ndarray:
        arr = np.array((FRAME_LENGTH_IN_BYTES,), dtype=np.uint8)
        np.copyto(arr, self._arr[CONTROL_LENGTH_IN_BYTES:])
        return arr.reshape((CAMERA_H, CAMERA_W, CAMERA_C))


