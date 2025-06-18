# ROS Help Desk - Simplified implementation of ROS Help desk for PenguinPi robot.

## Overview 
We present ROS Help Desk (RosHD): a framework that enables developers with diverse expertise levels to detect system anomalies and effectively debug system errors. RosHD leverages LLM-powered ReAct agents coordinating specialised tools for real-time system health monitoring, multimodal data integration, user-tailored explanations and an intuitive graphical interface, collectively assisting developers to monitor complex ROS-based robotic systems and resolve reported or characterised issues.
## System Architecture
<div align="center">
  <img src="resources/System architecture - RosHD.jpg" alt="RosHD System Diagram" width="600"/>
  <h3>ROS Help Desk - LLM-Powered Debugging Framework</h3>
</div>
## Installation

1. Make sure you have Docker installed in your machine. Also enable the docker extentions in the vscode. 
2. Build the docker container. Ctrl+Shift+P 

Need to install rosa once you crate the conda env

``` bash
wget -O Miniforge3.sh "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"

# Make it executable
chmod +x Miniforge3.sh

# Run the installer
bash Miniforge3.sh

./setup_conda_env.sh
conda activate penguinpi_agent
cd ros_ws
catkin_make
source devel/setup.bash
```

Manually install the following:
```bash
pip install rospkg langchain-openai jpl-rosa ipython
```

Change the following file:
```bash
code ~/.ignition/fuel/config.yaml
url: http://api.ignitionfuel.org
```

To not have to manually set up the env all the time add this to the bashrc of the container
```bash
code ~/.bashrc
# conda activate penguinpi_agent
source ros_ws/devel/setup.bash
```


### Important
Make changes to the following files. 
/home/ROSHD/miniforge3/envs/penguinpi_agent/lib/python3.9/site-packages/langchain/agents/agent.py
Line 1051     return_intermediate_steps: bool = True instead of False

/home/ROSHD/miniforge3/envs/penguinpi_agent/lib/python3.9/site-packages/rosa/rosa.py
Line 136 return result instead of return result["output"]



### Important 2

Install these outside the conda env
python3 -m pip install gevent pyyaml numpy requests pynput pygame

### Launch ROS Help Desk
```bash
roslaunch penguinpi_gazebo ECE4078_maze.launch (outside conda env)

rosrun penguinpi_agent ROSHD.py (inside conda env)
```

### Setting up the LLM

#### OpenAI
Add your API key 


#### Ollama
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3
ollama run llava "What's in this image? /PenguinPi_agent/img.png"

```
## Usage Instructions
```bash
# Part 1 
cd ros_ws
catkin_make_isolated --ignore-pkg ros_help_desk
roslaunch penguinpi_gazebo ECE4078.launch
# If you get this error [Err] [REST.cc:205] Error in REST request
# Change the following file:
# code ~/.ignition/fuel/config.yaml
# url: http://api.ignitionfuel.org
cd ros_ws/src
python3 ros_help_desk/ros_help_desk/ros_help_desk_gradio.py 

# Part 2.1
#Demo the system 
cd ros_ws
roslaunch penguinpi_small_house small_house_vacuum.launch

#Inject error and run the proposed agent
cd ros_ws
catkin_make_isolated --ignore-pkg ros_help_desk
roslaunch penguinpi_small_house small_house_vacuum.launch
cd ros_ws/src
python3 ros_help_desk/ros_help_desk/proposed_gradio.py --correct_line <> --ID <>

# Part 2.2
cd ros_ws
#Inject error and run the baseline agent
catkin_make_isolated --ignore-pkg ros_help_desk
roslaunch penguinpi_small_house small_house_vacuum.launch
cd ros_ws/src
python3 ros_help_desk/ros_help_desk/baseline_gradio.py --correct_line <> --ID <>
`