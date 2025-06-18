#!/usr/bin/env python3
import rospy
import math
import time
import numpy as np
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Image
import subprocess
import json
import os
from langchain.agents import tool
from typing import Optional, List
import cv2
from cv_bridge import CvBridge, CvBridgeError
from sensor_msgs.msg import Image
class PenguinPiTools:
    def __init__(self, agent):
        """Initialize PenguinPi tools with reference to the agent"""
        self.agent = agent
        
        # PenguinPi specific parameters
        self.max_linear_speed = 0.5  # m/s
        self.max_angular_speed = 1.0  # rad/s
        self.wheel_separation = 0.156  # meters
        self.wheel_diameter = 0.065    # meters
        
        # Image related parameters
        self.bridge = CvBridge()
        self.latest_image_msg = None  # To store the latest image message

        
        # Create tool functions that can be properly decorated
        self.move_forward = self._create_move_forward_tool()
        self.move_backward = self._create_move_backward_tool()
        self.turn_left = self._create_turn_left_tool()
        self.turn_right = self._create_turn_right_tool()
        self.stop_robot = self._create_stop_robot_tool()
        self.get_robot_pose = self._create_get_robot_pose_tool()
        self.get_robot_status = self._create_get_robot_status_tool()
        self.move_to_position = self._create_move_to_position_tool()
        self.draw_shape = self._create_draw_shape_tool()
        self.get_ros_topics = self._create_get_ros_topics_tool()
        self.get_ros_nodes = self._create_get_ros_nodes_tool()
        self.check_system_health = self._create_check_system_health_tool()
        self.get_topic_frequency = self._create_get_topic_frequency_tool()
        self.get_topic_delay = self._create_get_topic_delay_tool()
        self.reset_robot_pose = self._create_reset_robot_pose_tool()
        self.get_battery_status = self._create_get_battery_status_tool()
        self.emergency_stop = self._create_emergency_stop_tool()
    
    def _create_move_forward_tool(self):
        @tool
        def move_forward(speed: float = 0.2, duration: float = 2.0):
            """Move the PenguinPi robot forward"""
            try:
                speed = min(speed, self.max_linear_speed)
                twist = Twist()
                twist.linear.x = speed
                twist.angular.z = 0.0
                
                start_time = time.time()
                while time.time() - start_time < duration and not rospy.is_shutdown():
                    self.agent.cmd_vel_pub.publish(twist)
                    rospy.sleep(0.1)
                
                # Stop the robot
                self._stop_robot()
                
                return f"Successfully moved forward at {speed} m/s for {duration} seconds"
                
            except Exception as e:
                return f"Error moving forward: {str(e)}"
        return move_forward
    
    def _create_move_backward_tool(self):
        @tool
        def move_backward(speed: float = 0.2, duration: float = 2.0):
            """Move the PenguinPi robot backward"""
            try:
                speed = min(speed, self.max_linear_speed)
                twist = Twist()
                twist.linear.x = -speed
                twist.angular.z = 0.0
                
                start_time = time.time()
                while time.time() - start_time < duration and not rospy.is_shutdown():
                    self.agent.cmd_vel_pub.publish(twist)
                    rospy.sleep(0.1)
                
                self._stop_robot()
                return f"Successfully moved backward at {speed} m/s for {duration} seconds"
                
            except Exception as e:
                return f"Error moving backward: {str(e)}"
        return move_backward
    
    def _create_turn_left_tool(self):
        @tool
        def turn_left(angular_speed: float = 0.5, duration: float = 1.0):
            """Turn the PenguinPi robot left"""
            try:
                angular_speed = min(angular_speed, self.max_angular_speed)
                twist = Twist()
                twist.linear.x = 0.0
                twist.angular.z = angular_speed
                
                start_time = time.time()
                while time.time() - start_time < duration and not rospy.is_shutdown():
                    self.agent.cmd_vel_pub.publish(twist)
                    rospy.sleep(0.1)
                
                self._stop_robot()
                return f"Successfully turned left at {angular_speed} rad/s for {duration} seconds"
                
            except Exception as e:
                return f"Error turning left: {str(e)}"
        return turn_left
    
    def _create_turn_right_tool(self):
        @tool
        def turn_right(angular_speed: float = 0.5, duration: float = 1.0):
            """Turn the PenguinPi robot right"""
            try:
                angular_speed = min(angular_speed, self.max_angular_speed)
                twist = Twist()
                twist.linear.x = 0.0
                twist.angular.z = -angular_speed
                
                start_time = time.time()
                while time.time() - start_time < duration and not rospy.is_shutdown():
                    self.agent.cmd_vel_pub.publish(twist)
                    rospy.sleep(0.1)
                
                self._stop_robot()
                return f"Successfully turned right at {angular_speed} rad/s for {duration} seconds"
                
            except Exception as e:
                return f"Error turning right: {str(e)}"
        return turn_right
    
    def _create_stop_robot_tool(self):
        @tool
        def stop_robot():
            """Stop the PenguinPi robot immediately"""
            try:
                twist = Twist()
                twist.linear.x = 0.0
                twist.angular.z = 0.0
                self.agent.cmd_vel_pub.publish(twist)
                return "Robot stopped successfully"
            except Exception as e:
                return f"Error stopping robot: {str(e)}"
        return stop_robot
    
    def _stop_robot(self):
        """Internal method to stop the robot"""
        twist = Twist()
        twist.linear.x = 0.0
        twist.angular.z = 0.0
        self.agent.cmd_vel_pub.publish(twist)
    
    def _create_get_robot_pose_tool(self):
        @tool
        def get_robot_pose():
            """Get the current position and orientation of the robot"""
            try:
                pose_info = {
                    "position": {
                        "x": round(self.agent.x, 3),
                        "y": round(self.agent.y, 3)
                    },
                    "orientation": {
                        "theta_radians": round(self.agent.theta, 3),
                        "theta_degrees": round(math.degrees(self.agent.theta), 1)
                    },
                    "encoders": {
                        "left": round(self.agent.encoder_left, 3),
                        "right": round(self.agent.encoder_right, 3)
                    }
                }
                
                return f"Current robot pose:\n{json.dumps(pose_info, indent=2)}"
                
            except Exception as e:
                return f"Error getting robot pose: {str(e)}"
        return get_robot_pose
    
    def _create_get_robot_status_tool(self):
        @tool
        def get_robot_status():
            """Get comprehensive status information about the robot"""
            try:
                status = {
                    "pose": {
                        "x": round(self.agent.x, 3),
                        "y": round(self.agent.y, 3),
                        "theta_degrees": round(math.degrees(self.agent.theta), 1)
                    },
                    "encoders": {
                        "left": round(self.agent.encoder_left, 3),
                        "right": round(self.agent.encoder_right, 3)
                    },
                    "sensors": {
                        "camera_available": self.agent.latest_image is not None
                    },
                    "system": {
                        "ros_time": rospy.Time.now().to_sec(),
                        "node_name": rospy.get_name()
                    }
                }
                
                return f"Robot Status:\n{json.dumps(status, indent=2)}"
                
            except Exception as e:
                return f"Error getting robot status: {str(e)}"
        return get_robot_status
    
    def _create_move_to_position_tool(self):
        @tool
        def move_to_position(target_x: float, target_y: float, target_theta: float = 0.0, tolerance: float = 0.1):
            """Move the robot to a specific position and orientation"""
            try:
                # Simple point-to-point navigation
                max_attempts = 100
                attempt = 0
                
                while attempt < max_attempts and not rospy.is_shutdown():
                    # Calculate distance to target
                    dx = target_x - self.agent.x
                    dy = target_y - self.agent.y
                    distance = math.sqrt(dx*dx + dy*dy)
                    
                    if distance < tolerance:
                        # Close enough to target position
                        break
                    
                    # Calculate desired heading
                    desired_theta = math.atan2(dy, dx)
                    theta_error = desired_theta - self.agent.theta
                    
                    # Normalize angle error
                    while theta_error > math.pi:
                        theta_error -= 2 * math.pi
                    while theta_error < -math.pi:
                        theta_error += 2 * math.pi
                    
                    # Control law
                    twist = Twist()
                    if abs(theta_error) > 0.1:  # Need to turn first
                        twist.angular.z = 0.5 * theta_error
                    else:  # Move forward
                        twist.linear.x = min(0.2, distance)
                        twist.angular.z = 0.1 * theta_error
                    
                    self.agent.cmd_vel_pub.publish(twist)
                    rospy.sleep(0.1)
                    attempt += 1
                
                self._stop_robot()
                
                if attempt >= max_attempts:
                    return f"Failed to reach target position ({target_x}, {target_y}) within {max_attempts} attempts"
                else:
                    return f"Successfully reached target position ({target_x}, {target_y})"
                    
            except Exception as e:
                return f"Error moving to position: {str(e)}"
        return move_to_position
    
    def _create_draw_shape_tool(self):
        @tool
        def draw_shape(shape_type: str = "circle", size: float = 0.5):
            """Make the robot draw a shape"""
            try:
                if shape_type.lower() == "circle":
                    return self._draw_circle(size)
                elif shape_type.lower() == "square":
                    return self._draw_square(size)
                elif shape_type.lower() == "triangle":
                    return self._draw_triangle(size)
                else:
                    return f"Unknown shape type: {shape_type}. Supported shapes: circle, square, triangle"
                    
            except Exception as e:
                return f"Error drawing shape: {str(e)}"
        return draw_shape
    
    def _draw_circle(self, radius):
        """Draw a circle with given radius"""
        circumference = 2 * math.pi * radius
        angular_speed = 0.3  # rad/s
        duration = circumference / (angular_speed * self.wheel_separation / 2)
        
        twist = Twist()
        twist.linear.x = angular_speed * self.wheel_separation / 2
        twist.angular.z = angular_speed
        
        start_time = time.time()
        while time.time() - start_time < duration and not rospy.is_shutdown():
            self.agent.cmd_vel_pub.publish(twist)
            rospy.sleep(0.1)
        
        self._stop_robot()
        return f"Successfully drew a circle with radius {radius} meters"
    
    def _draw_square(self, side_length):
        """Draw a square with given side length"""
        for i in range(4):
            # Move forward
            self._move_forward_helper(speed=0.2, duration=side_length/0.2)
            rospy.sleep(0.5)
            
            # Turn 90 degrees
            self._turn_left_helper(angular_speed=0.5, duration=math.pi/2/0.5)
            rospy.sleep(0.5)
        
        return f"Successfully drew a square with side length {side_length} meters"
    
    def _draw_triangle(self, side_length):
        """Draw a triangle with given side length"""
        for i in range(3):
            # Move forward
            self._move_forward_helper(speed=0.2, duration=side_length/0.2)
            rospy.sleep(0.5)
            
            # Turn 120 degrees
            self._turn_left_helper(angular_speed=0.5, duration=2*math.pi/3/0.5)
            rospy.sleep(0.5)
        
        return f"Successfully drew a triangle with side length {side_length} meters"
    
    def _move_forward_helper(self, speed, duration):
        """Helper method for moving forward without tool decoration"""
        speed = min(speed, self.max_linear_speed)
        twist = Twist()
        twist.linear.x = speed
        twist.angular.z = 0.0
        
        start_time = time.time()
        while time.time() - start_time < duration and not rospy.is_shutdown():
            self.agent.cmd_vel_pub.publish(twist)
            rospy.sleep(0.1)
        
        self._stop_robot()
    
    def _turn_left_helper(self, angular_speed, duration):
        """Helper method for turning left without tool decoration"""
        angular_speed = min(angular_speed, self.max_angular_speed)
        twist = Twist()
        twist.linear.x = 0.0
        twist.angular.z = angular_speed
        
        start_time = time.time()
        while time.time() - start_time < duration and not rospy.is_shutdown():
            self.agent.cmd_vel_pub.publish(twist)
            rospy.sleep(0.1)
        
        self._stop_robot()
    
    def _create_get_ros_topics_tool(self):
        @tool
        def get_ros_topics():
            """Get information about active ROS topics"""
            try:
                result = subprocess.run(['rostopic', 'list'], capture_output=True, text=True)
                if result.returncode == 0:
                    topics = result.stdout.strip().split('\n')
                    topic_info = []
                    
                    for topic in topics[:10]:  # Limit to first 10 topics
                        if topic:
                            # Get topic type
                            type_result = subprocess.run(['rostopic', 'type', topic], 
                                                       capture_output=True, text=True)
                            topic_type = type_result.stdout.strip() if type_result.returncode == 0 else "Unknown"
                            
                            topic_info.append({
                                "name": topic,
                                "type": topic_type
                            })
                    
                    return f"Active ROS Topics:\n{json.dumps(topic_info, indent=2)}"
                else:
                    return "Error getting ROS topics"
                    
            except Exception as e:
                return f"Error getting ROS topics: {str(e)}"
        return get_ros_topics
    
    def _create_get_ros_nodes_tool(self):
        @tool
        def get_ros_nodes():
            """Get information about running ROS nodes"""
            try:
                result = subprocess.run(['rosnode', 'list'], capture_output=True, text=True)
                if result.returncode == 0:
                    nodes = result.stdout.strip().split('\n')
                    node_info = []
                    
                    for node in nodes[:10]:  # Limit to first 10 nodes
                        if node:
                            node_info.append({"name": node})
                    
                    return f"Running ROS Nodes:\n{json.dumps(node_info, indent=2)}"
                else:
                    return "Error getting ROS nodes"
                    
            except Exception as e:
                return f"Error getting ROS nodes: {str(e)}"
        return get_ros_nodes
    
    def _create_check_system_health_tool(self):
        @tool
        def check_system_health():
            """Perform a comprehensive health check of the PenguinPi system"""
            try:
                health_report = {
                    "timestamp": rospy.Time.now().to_sec(),
                    "robot_state": {
                        "position": {"x": self.agent.x, "y": self.agent.y},
                        "orientation_degrees": math.degrees(self.agent.theta),
                        "encoders": {"left": self.agent.encoder_left, "right": self.agent.encoder_right}
                    },
                    "sensor_status": {
                        "camera": self.agent.latest_image is not None
                    },
                    "ros_system": {
                        "node_name": rospy.get_name(),
                        "ros_time": rospy.Time.now().to_sec()
                    }
                }
                
                return f"System Health Report:\n{json.dumps(health_report, indent=2)}"
                
            except Exception as e:
                return f"Error during system health check: {str(e)}"
        return check_system_health
    
    def _create_get_topic_frequency_tool(self):
        @tool
        def get_topic_frequency(topic: str):
            """Get the publishing frequency of a ROS topic"""
            try:
                result = subprocess.run(['rostopic', 'hz', topic], 
                                      capture_output=True, text=True, timeout=5)
                return f"Topic frequency for {topic}:\n{result.stdout}"
            except subprocess.TimeoutExpired:
                return f"Timeout while checking frequency of topic {topic}"
            except Exception as e:
                return f"Error getting topic frequency: {str(e)}"
        return get_topic_frequency
    
    def _create_get_topic_delay_tool(self):
        @tool
        def get_topic_delay(topic: str):
            """Get the delay/latency of a ROS topic"""
            try:
                result = subprocess.run(['rostopic', 'delay', topic], 
                                      capture_output=True, text=True, timeout=5)
                return f"Topic delay for {topic}:\n{result.stdout}"
            except subprocess.TimeoutExpired:
                return f"Timeout while checking delay of topic {topic}"
            except Exception as e:
                return f"Error getting topic delay: {str(e)}"
        return get_topic_delay
    
    def _create_reset_robot_pose_tool(self):
        @tool
        def reset_robot_pose():
            """Reset the robot's pose estimation to origin"""
            try:
                self.agent.x = 0.0
                self.agent.y = 0.0
                self.agent.theta = 0.0
                return "Robot pose reset to origin (0, 0, 0)"
            except Exception as e:
                return f"Error resetting robot pose: {str(e)}"
        return reset_robot_pose
    
    def _create_get_battery_status_tool(self):
        @tool
        def get_battery_status():
            """Get the battery status of the robot (simulated for Gazebo)"""
            try:
                # Simulated battery status for Gazebo
                battery_info = {
                    "voltage": 12.0,
                    "current": 0.5,
                    "charge_percentage": 85,
                    "status": "Good",
                    "estimated_runtime_hours": 4.2
                }
                return f"Battery Status:\n{json.dumps(battery_info, indent=2)}"
            except Exception as e:
                return f"Error getting battery status: {str(e)}"
        return get_battery_status
    
    def _create_emergency_stop_tool(self):
        @tool
        def emergency_stop():
            """Emergency stop - immediately halt all robot movement"""
            try:
                # Send stop command multiple times to ensure it's received
                for _ in range(5):
                    twist = Twist()
                    twist.linear.x = 0.0
                    twist.angular.z = 0.0
                    self.agent.cmd_vel_pub.publish(twist)
                    rospy.sleep(0.1)
                
                return "EMERGENCY STOP ACTIVATED - Robot stopped immediately"
            except Exception as e:
                return f"Error during emergency stop: {str(e)}"
        return emergency_stop 
