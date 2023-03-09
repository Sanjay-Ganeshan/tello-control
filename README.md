# Requirements

Tested on Windows and Mac.

# Install

```
conda create -n drone python=3.10
conda activate drone
pip install -r requirements.txt
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