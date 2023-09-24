import typing as T
from enum import Enum
import pygame.mixer
from pathlib import Path

SOUNDS_FOLDER = Path(__file__).with_name("sounds")

class SoundCue(Enum):
    CONNECTING = "connecting"
    CONNECTED = "connected"
    TAKEOFF = "takeoff"
    READY = "ready"
    LANDING = "landing"
    EMERGENCY = "emergency"
    DISCONNECTED = "disconnected"
    AUTONOMOUS = "autonomous"
    MANUAL = "manual"
    RECORDING = "recording"
    STOP_RECORDING = "stoprecording"


class SoundCuePlayer:
    def __init__(self) -> None:
        pygame.mixer.init()
        self.sounds: T.Dict[SoundCue, pygame.mixer.Sound] = {}
        for each_cue in list(SoundCue):
            sound_file = SOUNDS_FOLDER / f"{each_cue.value}.ogg"
            if sound_file.exists():
                self.sounds[each_cue] = pygame.mixer.Sound(sound_file)

        self.main_channel = pygame.mixer.Channel(0)
        
    def cue(self, ev: SoundCue) -> None:
        if ev in self.sounds:
            self.main_channel.play(self.sounds[ev])