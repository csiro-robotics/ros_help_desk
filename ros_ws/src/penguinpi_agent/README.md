# ROSHD- PenguinPi Agent

A ROS1-based LLM (Large Language Model) agent designed specifically for the PenguinPi educational robot. This agent provides intelligent control, debugging, and educational assistance for robotics learning.

## Overview

The PenguinPi Agent is an AI-powered assistant that helps users learn robotics by providing:
- Natural language control of the PenguinPi robot
- Real-time sensor analysis and diagnostics
- Educational explanations of robotics concepts
- Automated debugging and troubleshooting
- Interactive web interface for easy interaction

## Features

### 🤖 Robot Control
- **Movement Commands**: Forward/backward motion, turning, complex patterns
- **Navigation**: Position-based navigation, wall following, shape drawing
- **Safety**: Obstacle detection, speed limits, emergency stops

### 📊 Sensor Analysis
- **Camera Feed**: Real-time image analysis, obstacle detection, color analysis
- **Laser Scanner**: Distance measurement, obstacle mapping, navigation assistance
- **Encoders**: Position tracking, odometry, movement validation

### 🎓 Educational Features
- **Experience Levels**: Adapts responses for beginner, intermediate, and expert users
- **Task Focus**: Specialized assistance for learning basics, navigation, computer vision, or diagnostics
- **Interactive Examples**: Pre-built examples for common robotics tasks
- **Real-time Feedback**: Continuous monitoring and status updates

### 🔧 System Diagnostics
- **Health Monitoring**: Comprehensive system health checks
- **ROS Integration**: Topic and node monitoring
- **Error Detection**: Automatic error identification and resolution
- **Performance Analysis**: Sensor quality and system performance metrics

## Robot Specifications

- **Size**: 150mm x 120mm x 30mm
- **Wheel Separation**: 156mm
- **Wheel Diameter**: 65mm
- **Max Speed**: 0.5 m/s linear, 1.0 rad/s angular
- **Sensors**: Raspberry Pi camera, laser scanner, wheel encoders
- **ROS Version**: ROS1 (Noetic/Melodic)

## Installation

### Prerequisites
- ROS1 (Noetic or Melodic)
- Python 3.6+
- Gazebo simulator
- PenguinPi packages (penguinpi_gazebo, penguinpi_description)

### Setup
1. **Clone the repository**:
   ```bash
   cd ~/catkin_ws/src
   git clone <repository-url>
   ```

2. **Install Python dependencies**:
   ```bash
   cd penguinpi_agent
   pip install -r requirements.txt
   ```

3. **Build the package**:
   ```bash
   cd ~/catkin_ws
   catkin_make
   source devel/setup.bash
   ```

4. **Set up environment variables**:
   ```bash
   # Create .env file in your home directory
   echo "OPENAI_API_KEY=your_api_key_here" > ~/.env
   ```

## Usage

### Console Interface
```bash
# Start the PenguinPi simulation
roslaunch penguinpi_gazebo penguinpi.launch

# In another terminal, run the agent
rosrun penguinpi_agent penguinpi_control.py
```

### Web Interface
```bash
# Start the Gradio web interface
rosrun penguinpi_agent ROSHD.py
```
Then open your browser to `http://localhost:7860`

### Launch File
```bash
# Use the provided launch file (includes simulation)
roslaunch penguinpi_agent penguinpi_agent.launch
```

## Available Commands

### Basic Commands
- `help` - Show help information
- `examples` - Show interactive examples
- `clear` - Clear chat history
- `status` - Get robot status
- `pose` - Get current position
- `camera` - Analyze camera feed
- `laser` - Analyze laser data

### Movement Examples
- "Move the PenguinPi forward for 2 seconds"
- "Turn the PenguinPi left for 1 second"
- "Drive in a circle with radius 0.5 meters"
- "Move to position (1, 1) with orientation 0 degrees"
- "Follow the wall on the right side"

### Analysis Examples
- "What do you see in the camera?"
- "Are there any obstacles nearby?"
- "Check the system health"
- "Show me the ROS topics"

## ROS Topics

### Subscribed Topics
- `/cmd_vel` - Command velocity (Twist)
- `/odom` - Odometry data
- `/joint_states` - Wheel encoder data
- `/picam/camera/image_raw` - Camera feed
- `/scan` - Laser scanner data

### Published Topics
- `/cmd_vel` - Robot movement commands

## Configuration

### User Experience Levels
The agent adapts its responses based on user experience:
- **Beginner**: Detailed explanations, simple language, educational focus
- **Intermediate**: Moderate explanations, practical applications
- **Expert**: Technical language, advanced features, optimization focus

### Primary Tasks
- **Learning Basics**: Fundamental robotics concepts and sensor operation
- **Navigation**: Path planning, obstacle avoidance, position control
- **Computer Vision**: Image processing, object detection, visual navigation
- **System Diagnostics**: Monitoring, error detection, troubleshooting

## Safety Features

- **Obstacle Detection**: Automatic stop if obstacles < 0.3m detected
- **Speed Limits**: Enforced maximum speeds (0.5 m/s linear, 1.0 rad/s angular)
- **Emergency Stop**: Immediate stop capability
- **Sensor Validation**: Data quality checks before making decisions
- **Boundary Awareness**: Workspace boundary monitoring

## Troubleshooting

### Common Issues

1. **No camera feed**:
   - Check if camera node is running: `rostopic echo /picam/camera/image_raw`
   - Verify camera permissions and connections

2. **No laser data**:
   - Check laser scanner: `rostopic echo /scan`
   - Ensure laser scanner is properly connected

3. **Movement not working**:
   - Verify cmd_vel topic: `rostopic echo /cmd_vel`
   - Check robot state and obstacles

4. **LLM errors**:
   - Verify OpenAI API key in ~/.env file
   - Check internet connection
   - Ensure API key has sufficient credits

### Debug Commands
```bash
# Check ROS topics
rostopic list
rostopic echo /cmd_vel

# Check robot state
rosnode list
rosnode info /penguinpi_agent

# Monitor sensor data
rostopic echo /odom
rostopic echo /joint_states
```

## Development

### Package Structure
```
penguinpi_agent/
├── scripts/
│   ├── penguinpi_control.py          # Main agent
│   ├── ROSHD.py   # Web interface
│   ├── penguinpi_tools.py            # Robot tools
│   ├── penguinpi_prompts.py          # System prompts
│   ├── penguinpi_llm.py              # LLM configuration
│   └── penguinpi_help.py             # Help system
├── launch/
│   └── penguinpi_agent.launch        # Launch file
├── requirements.txt                  # Python dependencies
├── package.xml                      # ROS package info
├── CMakeLists.txt                   # Build configuration
└── README.md                        # This file
```

### Adding New Tools
1. Add tool function to `penguinpi_tools.py`
2. Register tool in `penguinpi_control.py` setup_ai_components()
3. Update prompts if needed
4. Test with various user queries

### Customizing Prompts
Edit `penguinpi_prompts.py` to modify:
- Robot personality and capabilities
- Safety instructions
- Educational content
- System constraints

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the Apache-2.0 License.

## Acknowledgments

- Based on the original TurtleBot agent design
- Adapted for PenguinPi robot specifications
- Uses OpenAI GPT models for natural language processing
- Built with ROS1 and Python

## Support

For issues and questions:
- Check the troubleshooting section
- Review ROS logs: `rosnode info /penguinpi_agent`
- Ensure all dependencies are installed
- Verify PenguinPi simulation is running correctly 