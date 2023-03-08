# Requirements

Tested on windows. Might not work on Mac.

# Install

```
conda create -n drone python=3.10
pip install -r requirements.txt
conda activate drone
```

# Run

Run the controller:
```
python run.py tello_control.controller
```

Separately, run an autonomous controller (anything can import `autonomous.py` and use DroneIPC):
```
python run.py tello_control.autonomous
```