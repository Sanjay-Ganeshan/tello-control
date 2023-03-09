from dataclasses import dataclass, field
import typing as T
from enum import Enum
import pygame
from abc import ABC

class Axis1D(Enum):
    """
    A signed axis can go from -1 to 1
    An unsigned axis can go from 0 to 1
    """

    # Signed (-1 .. 1)
    # L_THUMBSTICK left (towards -1): Strafe left.
    # L_THUMBSTICK right (towards 1): Strafe right.
    L_THUMBSTICK_X = "L_THUMBSTICK_X"
    # L_THUMBSTICK backward (towards -1): Strafe backward.
    # L_THUMBSTICK forward (towards 1): Strafe forward.
    L_THUMBSTICK_Y = "L_THUMBSTICK_Y"
    # R_THUMBSTICK left (towards -1): Rotate left.
    # R_THUMBSTICK right (towards 1): Rotate right.
    R_THUMBSTICK_X = "R_THUMBSTICK_X"
    # Does nothing
    R_THUMBSTICK_Y = "R_THUMBSTICK_Y"

    # Unsigned (0 .. 1)
    # L_TRIGGER: Press to lower altitude.
    L_TRIGGER = "L_TRIGGER"
    # R_TRIGGER: Press to increase altitude.
    R_TRIGGER = "R_TRIGGER"

class Button(Enum):
    """
    Buttons can be down (True), or up (False)
    """

    # Connect to the tello.
    START = "START"

    # Does nothing
    BACK = "BACK"
    # Emergency (immediately shuts off motors).
    HOME = "HOME"

    # Does nothing
    SHIELD = "SHIELD"

    # Takeoff.
    A = "A"

    # Land
    B = "B"

    # Enable video stream
    X = "X"

    # Disable video stream
    Y = "Y"

    # Does nothing
    L_BUTTON = "L_BUTTON"

    # Toggles between autonomous mode and control. Autonomous mode is
    # governed by the script you write.
    R_BUTTON = "R_BUTTON"

class Hat(Enum):
    """
    Hats will never produce "left AND right" or "up AND down"
    
    They return (x,y), where each X and Y are -1 (left/down), 0, or 1 (right/up)
    """
    D_PAD = "D_PAD"

def clamp(x: T.Union[int,float], min_val: T.Union[int,float], max_val: T.Union[int,float]) -> T.Union[int,float]:
    return min(max(x, min_val), max_val)

def sign(x: float) -> int:
    if x > 0:
        return 1
    elif x < 0:
        return -1
    else:
        return 0


@dataclass
class Input:
    _axes: T.Dict[Axis1D, float] = field(default_factory=dict)
    _buttons: T.Dict[Button, bool] = field(default_factory=dict)
    _prev_buttons: T.Dict[Button, bool] = field(default_factory=dict)
    _hats: T.Dict[Hat, T.Tuple[int, int]] = field(default_factory=dict)

    def __getitem__(self, inp: T.Union[Axis1D, Button, Hat]) -> T.Union[float, bool, T.Tuple[int, int]]:
        if isinstance(inp, Axis1D):
            return self._axes.get(inp, 0.0)
        elif isinstance(inp, Button):
            return self._buttons.get(inp, False)
        elif isinstance(inp, Hat):
            return self._hats.get(inp, (0,0))
        raise KeyError(f"Unknown key: {inp}")
    
    def get_down(self, button: Button) -> bool:
        """
        Returns True the frame if the button changed
        from up -> down this frame.
        """
        return self._buttons.get(button, False) and not self._prev_buttons.get(button, False)
    
    def get_up(self, button: Button) -> bool:
        """
        Returns True the frame if the button changed
        from down -> up this frame.
        """
        return not self._buttons.get(button, False) and self._prev_buttons.get(button, False)
    
    def _tick(self) -> None:
        """
        Indicate that a frame has passed
        """
        self._prev_buttons.clear()
        self._prev_buttons.update(self._buttons)

    def __setitem__(self, key: T.Union[Axis1D, Button, Hat], value: T.Union[float, bool, T.Tuple[int, int]]) -> T.Union[float, bool, T.Tuple[int, int]]:
        if isinstance(key, Axis1D):
            assert isinstance(value, float)
            self._axes[key] = clamp(value, -1.0, 1.0)
        elif isinstance(key, Button):
            assert isinstance(value, bool)
            self._axes[key] = value
        elif isinstance(key, Hat):
            assert isinstance(value, tuple) and len(value) == 2 and all((v in [-1, 0, 1] for v in value))
            self._hats[key] = value
        else:
            raise KeyError(f"Unknown key: {key}")

        return value

class Binding(ABC):
    def process_event(self, event: pygame.event.Event, controller: Input) -> None:
        ...

@dataclass
class AxisBinding(Binding):
    axis: Axis1D
    axis_id: int
    multiply: float = 1.0
    offset: float = 0.0
    deadzone: float = 0.1

    def process_event(self, event: pygame.event.Event, controller: Input) -> None:
        if event.type == pygame.JOYAXISMOTION:
            if event.axis == self.axis_id:
                value = 0 if abs(event.value) < self.deadzone else ((event.value - sign(event.value)) / (1.0 - self.deadzone))
                controller[self.axis] = value * self.multiply + self.offset

@dataclass
class ButtonBinding(Binding):
    button: Button
    button_id: int

    def process_event(self, event: pygame.event.Event, controller: Input) -> None:
        if event.type == pygame.JOYBUTTONDOWN or event.type == pygame.JOYBUTTONUP:
            newval = True if event.type == pygame.JOYBUTTONDOWN else False
            if event.button == self.button_id:
                controller[self.button] = newval

@dataclass
class HatBinding(Binding):
    hat: Hat
    hat_id: int

    def process_event(self, event: pygame.event.Event, controller: Input) -> None:
        if event.type == pygame.JOYHATMOTION:
            if event.hat == self.hat_id:
                controller[self.hat] = event.value

WINDOWS_SHIELD_CONTROLLER: T.List[Binding] = [
    AxisBinding(
        axis=Axis1D.L_THUMBSTICK_Y,
        axis_id=1,
        multiply=-1,
    ),
    AxisBinding(
        axis=Axis1D.L_THUMBSTICK_X,
        axis_id=0,
    ),
    AxisBinding(
        axis=Axis1D.R_THUMBSTICK_Y,
        axis_id=6,
        multiply=-1,
    ),
    AxisBinding(
        axis=Axis1D.R_THUMBSTICK_X,
        axis_id=3,
    ),
    AxisBinding(
        axis=Axis1D.L_TRIGGER,
        axis_id=4,
        multiply=0.5,
        offset=0.5,
    ),
    AxisBinding(
        axis=Axis1D.R_TRIGGER,
        axis_id=5,
        multiply=-0.5,
        offset=-0.5,
    ),

    ButtonBinding(
        button=Button.Y,
        button_id=8,
    ),
    ButtonBinding(
        button=Button.X,
        button_id=9,
    ),
    ButtonBinding(
        button=Button.B,
        button_id=10,
    ),
    ButtonBinding(
        button=Button.A,
        button_id=11,
    ),
    ButtonBinding(
        button=Button.R_BUTTON,
        button_id=6,
    ),
    ButtonBinding(
        button=Button.L_BUTTON,
        button_id=7,
    ),
    ButtonBinding(
        button=Button.START,
        button_id=3,
    ),
    ButtonBinding(
        button=Button.BACK,
        button_id=13,
    ),
    ButtonBinding(
        button=Button.HOME,
        button_id=14,
    ),
    ButtonBinding(
        button=Button.SHIELD,
        button_id=12,
    ),

    HatBinding(
        hat=Hat.D_PAD,
        hat_id=0
    )
]