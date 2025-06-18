#!/usr/bin/env python

def get_help(examples):
    """Get help information for the PenguinPi agent"""
    
    help_text = """
# PenguinPi Agent Help

Welcome to the PenguinPi Agent! I'm your personal assistant for controlling and debugging the PenguinPi robot.

## Available Commands

### Basic Commands
- `help` - Show this help message
- `examples` - Show interactive examples
- `clear` - Clear the chat history
- `status` - Get current robot status
- `pose` - Get current position and orientation
- `camera` - Analyze camera feed
- `laser` - Analyze laser scanner data

### Movement Commands
You can ask me to:
- Move the robot forward/backward
- Turn the robot left/right
- Drive in patterns (circles, squares, etc.)
- Navigate to specific positions
- Follow walls using the laser scanner

### Analysis Commands
- Analyze camera feed for obstacles and objects
- Process laser scanner data for navigation
- Check system health and diagnostics
- Monitor ROS topics and nodes

## Example Queries

### Basic Movement
- "Move the PenguinPi forward for 2 seconds"
- "Turn the PenguinPi left for 1 second"
- "Stop the robot"

### Navigation
- "Move to position (1, 1) with orientation 0 degrees"
- "Follow the wall on the right side"
- "Drive in a circle with radius 0.5 meters"

### Analysis
- "What do you see in the camera?"
- "Are there any obstacles nearby?"
- "What's my current position?"
- "Check the system health"

### Educational
- "Explain how the laser scanner works"
- "Show me the ROS topics"
- "What sensors do you have?"

## Safety Features

- I always check for obstacles before moving
- Speed limits are enforced (max 0.5 m/s linear, 1.0 rad/s angular)
- Emergency stop if obstacles are too close (< 0.3m)
- Continuous monitoring of sensor data

## Robot Specifications

- **Size**: 150mm x 120mm x 30mm
- **Wheel Separation**: 156mm
- **Wheel Diameter**: 65mm
- **Max Speed**: 0.5 m/s linear, 1.0 rad/s angular
- **Sensors**: Raspberry Pi camera, laser scanner, wheel encoders

## ROS Topics

- `/cmd_vel` - Command velocity (Twist)
- `/odom` - Odometry data
- `/joint_states` - Wheel encoder data
- `/picam/camera/image_raw` - Camera feed
- `/scan` - Laser scanner data

## Getting Started

1. Make sure the PenguinPi is running and connected
2. Start the ROS system: `roslaunch penguinpi_gazebo penguinpi.launch`
3. Run the agent: `rosrun penguinpi_agent penguinpi_control.py`
4. Try some basic commands like "status" or "pose"
5. Experiment with movement commands

## Troubleshooting

If you encounter issues:
- Check that all ROS topics are publishing
- Verify sensor data is available
- Ensure the robot is not blocked by obstacles
- Use "check_system_health" for diagnostics

## Examples

Here are some examples you can try:

"""
    
    # Add the examples
    for i, example in enumerate(examples, 1):
        help_text += f"{i}. {example}\n"
    
    help_text += """
## Need More Help?

- Type `examples` to see interactive examples
- Ask me to explain any robot operation
- Request system diagnostics with "check_system_health"
- I'm here to help you learn robotics!

Remember: Safety first! I'll always check for obstacles and respect speed limits.
"""
    
    return help_text 