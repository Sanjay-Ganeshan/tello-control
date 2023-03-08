import code
from .autonomous import DroneIPC, DroneState

def main():
    with DroneIPC() as ipc:
        code.interact(local=locals())

if __name__ == '__main__':
    main()