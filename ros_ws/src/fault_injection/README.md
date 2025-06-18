# PenguinPi Fault Injection System

## Quick Start

```bash
cd ~/workspace/PenguinPi_agent/ros_ws
catkin_make
source devel/setup.bash
```

## Commands

### Test Keyboard Faults

```bash
# Delayed keyboard responses
roslaunch fault_injection fault_injection.launch scenario:=keyboard_delay keyboard_faults:=true camera_faults:=false

# Dropped keyboard commands  
roslaunch fault_injection fault_injection.launch scenario:=keyboard_drop keyboard_faults:=true camera_faults:=false

# Corrupted keyboard commands
roslaunch fault_injection fault_injection.launch scenario:=keyboard_corruption keyboard_faults:=true camera_faults:=false
```

### Test Camera Faults

```bash
# Delayed camera frames
roslaunch fault_injection fault_injection.launch scenario:=camera_delay camera_faults:=true keyboard_faults:=false

# Dropped camera frames
roslaunch fault_injection fault_injection.launch scenario:=camera_drop camera_faults:=true keyboard_faults:=false

# Corrupted camera images (blur/noise)
roslaunch fault_injection fault_injection.launch scenario:=camera_corruption camera_faults:=true keyboard_faults:=false
```

### No Faults (Normal Operation)

```bash
roslaunch fault_injection fault_injection.launch keyboard_faults:=false camera_faults:=false
```

### Interactive Controller

```bash
rosrun fault_injection fault_controller.py
```

