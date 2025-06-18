#!/bin/bash

echo "Setting up PenguinPi Agent Conda Environment..."

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo "Error: conda is not installed. Please install Anaconda or Miniconda first."
    exit 1
fi

# Create the conda environment
echo "Creating conda environment 'penguinpi_agent'..."
conda env create -f environment.yml

# Activate the environment
echo "Activating conda environment..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate penguinpi_agent

# Verify installation
echo "Verifying installation..."
python -c "import rosa; print('ROSA installed successfully')" || echo "Warning: ROSA installation may have failed"

# Make scripts executable
echo "Making scripts executable..."
chmod +x ros_ws/src/penguinpi_agent/scripts/*.py

echo ""
echo "Setup complete! To activate the environment, run:"
echo "conda activate penguinpi_agent"
echo ""
echo "To test the system:"
echo "1. Activate environment: conda activate penguinpi_agent"
echo "2. Build ROS workspace: cd ros_ws && catkin_make"
echo "3. Source ROS: source devel/setup.bash"
echo "4. Test: roslaunch penguinpi_gazebo penguinpi.launch"
echo "5. In another terminal: rosrun penguinpi_agent penguinpi_control.py" 