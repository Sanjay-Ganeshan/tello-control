from .autonomous import DroneIPC, DroneState

def main():
    with DroneIPC() as ipc:
        while True:
            state = DroneState()
            state.yaw_vel = 30
            ipc.save_state(state)

if __name__ == '__main__':
    main()