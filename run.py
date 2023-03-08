import tello_control
import runpy
import sys

def main() -> None:
    new_argv = sys.argv[2:]
    module = sys.argv[1]
    sys.argv = [sys.argv[0], *new_argv]
    runpy._run_module_as_main(
        module,
        alter_argv=False,
    )

if __name__ == "__main__":
    main()