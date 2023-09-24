import pygame
import time
from pathlib import Path

mydir = Path(__file__).resolve().parent

def main() -> None:
    pygame.init()
    size = (1280, 800)
    screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
    n_controllers = pygame.joystick.get_count()
    assert n_controllers == 1
    joystick = pygame.joystick.Joystick(0)
    should_quit: bool = False

    target_seconds_per_frame: float = 1 / 60
    log_file = mydir / "recieved_inputs.txt"
    seen = set()

    with open(log_file, "w") as f:
        print(joystick.get_name(), file=f)
        print("N Axes", joystick.get_numaxes(), file=f)
        print("N Hats", joystick.get_numhats(), file=f)
        print("N Buttons", joystick.get_numbuttons(), file=f)
        while not should_quit:
            frame_start = time.time()
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    should_quit = True
                if event.type == pygame.JOYAXISMOTION and abs(event.value) > 0:
                    to_log = (event.axis, -1 if event.value < 0 else 1)
                    if to_log not in seen:
                        print(to_log, file=f)
                        seen.add(to_log)
                elif event.type == pygame.JOYBUTTONDOWN:
                    to_log = event.button
                    if to_log not in seen:
                        print(to_log, file=f)
                        seen.add(to_log)
                elif event.type == pygame.JOYHATMOTION:
                    to_log = event.hat, event.value
                    if to_log not in seen:
                        print(to_log, file=f)
                        seen.add(to_log)

            if should_quit:
                break

            screen.fill((0,0,0))

            pygame.display.flip()
            frame_end = time.time()
            elapsed = frame_end - frame_start

            if elapsed > target_seconds_per_frame:
                print("DROP")
            if elapsed < target_seconds_per_frame:
                time.sleep(target_seconds_per_frame - elapsed)

    pygame.quit()
    
if __name__ == "__main__":
    main()
