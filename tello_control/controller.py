import pygame
import typing as T
from dataclasses import dataclass, field
import time
from djitellopy import Tello
import cv2
from .autonomous import DroneIPC
import logging
from .controller_state import (
    clamp,
    WINDOWS_SHIELD_CONTROLLER,
    MAC_SHIELD_CONTROLLER,
    STEAM_DECK_INTEGRATED_CONTROLLER,
    Binding,
    Input,
    Axis1D,
    Button,
    Hat,
)
import sys

CONTROLLER: T.List[Binding]
SCREEN_FLAGS = pygame.RESIZABLE
if sys.platform == "win32":
    CONTROLLER = WINDOWS_SHIELD_CONTROLLER
elif sys.platform == "darwin":
    CONTROLLER = MAC_SHIELD_CONTROLLER
elif sys.platform == "linux":
    CONTROLLER = STEAM_DECK_INTEGRATED_CONTROLLER
    SCREEN_FLAGS= pygame.FULLSCREEN
else:
    raise Exception("Your controller bindings are not defined.")




def draw_controllers(screen: pygame.Surface, controller: Input) -> None:
    width, height = screen.get_size()

    l_offset_x = controller[Axis1D.L_THUMBSTICK_X] * width // 12
    l_offset_y = -1 * controller[Axis1D.L_THUMBSTICK_Y] * width // 12
    r_offset_x = controller[Axis1D.R_THUMBSTICK_X] * width // 12
    r_offset_y = -1 * controller[Axis1D.R_THUMBSTICK_Y] * width // 12

    l_thumbstick_x = 2 * width // 12
    r_thumbstick_x = 10 * width // 12
    thumbstick_y = height - (2 * width // 12)
    thumbstick_r = width // 12

    GRAY = (127, 127, 127)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)

    pygame.draw.circle(
        surface = screen,
        color = GRAY,
        center = (l_thumbstick_x, thumbstick_y),
        radius = thumbstick_r,
    )

    pygame.draw.circle(
        surface = screen,
        color = GRAY,
        center = (r_thumbstick_x, thumbstick_y),
        radius = thumbstick_r,
    )

    pygame.draw.circle(
        surface = screen,
        color = RED,
        center = (l_thumbstick_x + l_offset_x, thumbstick_y + l_offset_y),
        radius = thumbstick_r // 3,
    )

    pygame.draw.circle(
        surface = screen,
        color = GREEN,
        center = (r_thumbstick_x + r_offset_x, thumbstick_y + r_offset_y),
        radius = thumbstick_r // 3,
    )

    trigger_width = width // 12
    trigger_height = height // 4
    trigger_top = 0

    l_trigger_l = width // 6 - trigger_width // 2
    r_trigger_l = 5 * width // 6 - trigger_width // 2

    l_trigger_offset = int(controller[Axis1D.L_TRIGGER] * trigger_height)
    r_trigger_offset = int(controller[Axis1D.R_TRIGGER] * trigger_height)

    pygame.draw.rect(
        surface=screen,
        color=GRAY,
        rect=((l_trigger_l, trigger_top), (trigger_width, trigger_height)),
    )

    pygame.draw.rect(
        surface=screen,
        color=GRAY,
        rect=((r_trigger_l, trigger_top), (trigger_width, trigger_height)),
    )

    pygame.draw.rect(
        surface=screen,
        color=RED,
        rect=((l_trigger_l, trigger_top + (trigger_height - l_trigger_offset)), (trigger_width, l_trigger_offset)),
    )

    pygame.draw.rect(
        surface=screen,
        color=GREEN,
        rect=((r_trigger_l, trigger_top + (trigger_height - r_trigger_offset)), (trigger_width, r_trigger_offset)),
    )





def _to_control(x: float) -> int:
    return int(clamp(x * 100, -100, 100))

def control_drone(tello: Tello, controller: Input) -> None:
    if controller.get_down(Button.A):
        # TODO: If your drone crashes, tello.is_flying is False, so you can't
        # takeoff again. But, if you call tello.takeoff() twice in the air,
        # the drone returns errors and crashes.
        print("takeoff")
        if not tello.is_flying:
            tello.takeoff()
    if controller.get_down(Button.B):
        print("land")
        # TODO: If you call land twice in the air or on the ground, the program
        # crashes and the drone lands.
        if tello.is_flying:
            tello.land()
    if controller.get_down(Button.START):
        print("connect")
        tello.connect()
    if controller.get_down(Button.X):
        print("streamon")
        # Enables video stream.
        tello.streamon()
    if controller.get_down(Button.Y):
        print("streamoff")
        # Disables video stream.
        tello.streamoff()
    
    # Unsupported by our tello - might need a firmware update.
    """
    if controller.get_down(Button.R_BUTTON):
        print("FWD camera")
        tello.set_video_direction(
            Tello.CAMERA_FORWARD
        )
    if controller.get_down(Button.L_BUTTON):
        print("DOWN camera")
        tello.set_video_direction(
            Tello.CAMERA_DOWNWARD
        )
    """
    
    if tello.is_flying:
        up_down_velocity = 0
        yaw_velocity = 0
        fw_backward_velocity = 0
        left_right_velocity = 0

        # The 0.1 here is a dead zone where we ignore the input. This is
        # to cope with small amounts of drift.
        # Notice below that if both triggers are pressed at once, we prefer
        # descending to ascending.
        up_down_velocity = controller[Axis1D.R_TRIGGER] - controller[Axis1D.L_TRIGGER]
        yaw_velocity = controller[Axis1D.R_THUMBSTICK_X]
        left_right_velocity = controller[Axis1D.L_THUMBSTICK_X]
        fw_backward_velocity = controller[Axis1D.L_THUMBSTICK_Y]

        tello.send_rc_control(
            left_right_velocity=_to_control(left_right_velocity),
            forward_backward_velocity=_to_control(fw_backward_velocity),
            up_down_velocity=_to_control(up_down_velocity),
            yaw_velocity=_to_control(yaw_velocity),
        )

def print_kw(**kwargs):
    print(" ".join((f"{key}={kwargs[key]}" for key in kwargs)))

def control_drone_autonomous(tello: Tello, drone_ipc: DroneIPC):
    state = drone_ipc.get_state()
    if state.takeoff:
        if not tello.is_flying:
            tello.takeoff()
    if state.land:
        if tello.is_flying:
            tello.land()
    if state.emergency:
        tello.emergency()
    if state.streamon:
        tello.streamon()
    if state.streamoff:
        tello.streamoff()
    
    if tello.is_flying:
        tello.send_rc_control(
            left_right_velocity=state.left_right_vel,
            forward_backward_velocity=state.fwd_back_vel,
            up_down_velocity=state.up_down_vel,
            yaw_velocity=state.yaw_vel,
        )

def render_drone_view(screen: pygame.Surface, tello: Tello, drone_ipc: DroneIPC) -> None:
    if tello.stream_on:
        reader = tello.get_frame_read()
        if not reader.grabbed:
            return
        
        frame = reader.frame
        drone_ipc.save_frame(frame)

        screen_w, screen_h = screen.get_size()
        left = 3 * screen_w // 12
        right = 9 * screen_w // 12
        top = screen_h // 10
        bottom = 9 * screen_h // 10

        w, h = (right - left), (bottom - top)

        smaller = cv2.resize(frame, (w, h))
        img = pygame.image.frombuffer(smaller.tobytes(), (w, h), "BGR")
        screen.blit(
            img,
            (
                (left, top),
                (w, h)
            )
        )

def main() -> None:
    pygame.init()
    size = (1280, 800)
    screen = pygame.display.set_mode(size, SCREEN_FLAGS)
    tello = Tello()
    tello.LOGGER.setLevel(logging.INFO)
    n_controllers = pygame.joystick.get_count()
    assert n_controllers == 1
    joystick = pygame.joystick.Joystick(0)
    print(joystick.get_name())
    should_quit: bool = False
    target_seconds_per_frame: float = 1 / 60
    
    controller_state = Input()

    autonomous_mode = False

    with DroneIPC() as ipc:
        while not should_quit:
            frame_start = time.time()
            controller_state._tick()
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    should_quit = True
                for each_binding in CONTROLLER:
                    each_binding.process_event(event, controller_state)

            if should_quit:
                break

            if controller_state.get_down(Button.R_BUTTON):
                autonomous_mode = not autonomous_mode
                print(f"{autonomous_mode=}")
            if controller_state.get_down(Button.L_BUTTON):
                tello.emergency()

            if autonomous_mode:
                control_drone_autonomous(tello, ipc)
            else:
                control_drone(tello, controller_state)
            
            screen.fill((0,0,0))

            render_drone_view(screen, tello, ipc)
            draw_controllers(screen, controller_state)

            pygame.display.flip()
            frame_end = time.time()
            elapsed = frame_end - frame_start

            if elapsed > target_seconds_per_frame:
                print("DROP")
            if elapsed < target_seconds_per_frame:
                time.sleep(target_seconds_per_frame - elapsed)

    pygame.quit()
    if tello.stream_on:
        tello.streamoff()
    if tello.is_flying:
        tello.land()
    
if __name__ == "__main__":
    main()

