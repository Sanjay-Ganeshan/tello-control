import pygame
import typing as T
from dataclasses import dataclass, field
import time
from djitellopy import Tello
import cv2
import os
from .autonomous import DroneState, DroneIPC
import logging

@dataclass
class Button:
    current: bool = False
    previous: bool = field(default=False, init=False)

    def down(self) -> bool:
        return self.current and not self.previous
    
    def get(self) -> bool:
        return self.current

    def up(self) -> bool:
        return not self.current and self.previous
    
    def _tick(self) -> None:
        self.previous = self.current

@dataclass
class ControllerState:
    L_THUMBSTICK_X: float = 0.0
    L_THUMBSTICK_Y: float = 0.0
    R_THUMBSTICK_X: float = 0.0
    R_THUMBSTICK_Y: float = 0.0
    L_TRIGGER: float = 0.0
    R_TRIGGER: float = 0.0
    D_PAD: T.Tuple[int, int] = (0, 0)
    START: Button = field(default_factory=Button)
    BACK: Button = field(default_factory=Button)
    HOME: Button = field(default_factory=Button)
    SHIELD: Button = field(default_factory=Button)
    A: Button = field(default_factory=Button)
    B: Button = field(default_factory=Button)
    X: Button = field(default_factory=Button)
    Y: Button = field(default_factory=Button)
    L_BUTTON: Button = field(default_factory=Button)
    R_BUTTON: Button = field(default_factory=Button)

    def _tick(self) -> None:
        self.START._tick()
        self.BACK._tick()
        self.HOME._tick()
        self.SHIELD._tick()
        self.A._tick()
        self.B._tick()
        self.X._tick()
        self.Y._tick()
        self.L_BUTTON._tick()
        self.R_BUTTON._tick()
    
def clamp(x: float, minimum: float, maximum: float) -> float:
    return min(max(x, minimum), maximum)

def draw_controllers(screen: pygame.Surface, controller: ControllerState) -> None:
    width, height = screen.get_size()

    l_offset_x = controller.L_THUMBSTICK_X * width // 12
    l_offset_y = -1 * controller.L_THUMBSTICK_Y * width // 12
    r_offset_x = controller.R_THUMBSTICK_X * width // 12
    r_offset_y = -1 * controller.R_THUMBSTICK_Y * width // 12

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

    l_trigger_offset = int(controller.L_TRIGGER * trigger_height)
    r_trigger_offset = int(controller.R_TRIGGER * trigger_height)

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
    return clamp(int(x * 100), -100, 100)

def control_drone(tello: Tello, controller: ControllerState) -> None:
    if controller.A.down():
        print("takeoff")
        if not tello.is_flying:
            tello.takeoff()
    if controller.B.down():
        print("land")
        if tello.is_flying:
            tello.land()
    if controller.HOME.down():
        print("emergency")
        tello.emergency()
    if controller.START.down():
        print("connect")
        tello.connect()
    if controller.X.down():
        print("streamon")
        tello.streamon()
    if controller.Y.down():
        print("streamoff")
        tello.streamoff()
    
    # Unsupported by our tello
    """
    if controller.R_BUTTON.down():
        print("FWD camera")
        tello.set_video_direction(
            Tello.CAMERA_FORWARD
        )
    if controller.L_BUTTON.down():
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
        if controller.L_TRIGGER > 0.1:
            up_down_velocity = ((controller.L_TRIGGER - 0.1) / 0.9) * -1
        elif controller.R_TRIGGER > 0.1:
            up_down_velocity = ((controller.R_TRIGGER - 0.1) / 0.9)
        
        if abs(controller.R_THUMBSTICK_X) > 0.1:
            offset = -0.1 if controller.R_THUMBSTICK_X > 0 else 0.1
            yaw_velocity = ((controller.R_THUMBSTICK_X + offset) / 0.9)
        
        if abs(controller.L_THUMBSTICK_X) > 0.1:
            offset = -0.1 if controller.L_THUMBSTICK_X > 0 else 0.1
            left_right_velocity = ((controller.L_THUMBSTICK_X + offset) / 0.9)
        
        if abs(controller.L_THUMBSTICK_Y) > 0.1:
            offset = -0.1 if controller.L_THUMBSTICK_Y > 0 else 0.1
            fw_backward_velocity = ((controller.L_THUMBSTICK_Y + offset) / 0.9)
        
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
    screen = pygame.display.set_mode(size)
    tello = Tello()
    tello.LOGGER.setLevel(logging.WARNING)
    n_controllers = pygame.joystick.get_count()
    assert n_controllers == 1
    joystick = pygame.joystick.Joystick(0)
    print(joystick.get_name())
    should_quit: bool = False
    target_seconds_per_frame: float = 1 / 60
    
    controller_state = ControllerState()

    autonomous_mode = False

    with DroneIPC() as ipc:
        while not should_quit:
            frame_start = time.time()
            controller_state._tick()
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    should_quit = True
                elif event.type == pygame.JOYAXISMOTION:
                    if event.axis == 1:
                        controller_state.L_THUMBSTICK_Y = clamp(-1.0 * event.value, -1.0, 1.0)
                    elif event.axis == 0:
                        controller_state.L_THUMBSTICK_X = clamp(event.value, -1.0, 1.0)
                    elif event.axis == 6:
                        controller_state.R_THUMBSTICK_Y = clamp(-1.0 * event.value, -1.0, 1.0)
                    elif event.axis == 3:
                        controller_state.R_THUMBSTICK_X = clamp(event.value, -1.0, 1.0)
                    elif event.axis == 4:
                        controller_state.L_TRIGGER = clamp((event.value + 1.0) / 2.0, 0.0, 1.0)
                    elif event.axis == 5:
                        controller_state.R_TRIGGER = clamp((event.value + 1.0) / 2.0, -1.0, 1.0)
                elif event.type == pygame.JOYBUTTONDOWN or event.type == pygame.JOYBUTTONUP:
                    newval = True if event.type == pygame.JOYBUTTONDOWN else False
                    if event.button == 8:
                        controller_state.Y.current = newval
                    elif event.button == 9:
                        controller_state.X.current = newval
                    elif event.button == 10:
                        controller_state.B.current = newval
                    elif event.button == 11:
                        controller_state.A.current = newval
                    elif event.button == 6:
                        controller_state.R_BUTTON.current = newval
                    elif event.button == 7:
                        controller_state.L_BUTTON.current = newval
                    elif event.button == 3:
                        controller_state.START.current = newval
                    elif event.button == 13:
                        controller_state.BACK.current = newval
                    elif event.button == 14:
                        controller_state.HOME.current = newval
                    elif event.button == 12:
                        controller_state.SHIELD.current = newval
                elif event.type == pygame.JOYHATMOTION:
                    if event.hat == 0:
                        controller_state.D_PAD = event.value
                        print(event.value)

            if should_quit:
                break

            if controller_state.R_BUTTON.down():
                autonomous_mode = not autonomous_mode
                print(f"{autonomous_mode=}")

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

