cmake_minimum_required(VERSION 3.0.2)
project(fault_injection)

find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  geometry_msgs
  sensor_msgs
  nav_msgs
  cv_bridge
  message_generation
)

# Generate messages in the 'msg' folder
add_message_files(
  FILES
  FaultStatus.msg
  FaultReport.msg
)

# Generate added messages and services with any dependencies listed here
generate_messages(
  DEPENDENCIES
  std_msgs
  geometry_msgs
  sensor_msgs
)

catkin_package(
  CATKIN_DEPENDS 
    rospy 
    std_msgs 
    geometry_msgs 
    sensor_msgs 
    nav_msgs 
    cv_bridge 
    message_runtime
)

include_directories(
  ${catkin_INCLUDE_DIRS}
)

# Install Python scripts
catkin_install_python(PROGRAMS
  scripts/keyboard_fault_injector.py
  scripts/camera_fault_injector.py
  scripts/fault_controller.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
) 