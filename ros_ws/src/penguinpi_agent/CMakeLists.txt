cmake_minimum_required(VERSION 3.0.2)
project(penguinpi_agent)

find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  geometry_msgs
  sensor_msgs
  nav_msgs
  tf
  cv_bridge
  image_transport
)

catkin_package(
  CATKIN_DEPENDS
    rospy
    std_msgs
    geometry_msgs
    sensor_msgs
    nav_msgs
    tf
    cv_bridge
    image_transport
)

include_directories(
  ${catkin_INCLUDE_DIRS}
)

catkin_install_python(PROGRAMS
  scripts/penguinpi_control.py
  scripts/ROSHD.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
) 