#!/usr/bin/env python3
import rospy
import os
import sys
import math
import time
import json
import numpy as np
from datetime import datetime

# ROS imports
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Image, JointState
from nav_msgs.msg import Odometry
from std_msgs.msg import String, Bool

# AI/LLM imports
import dotenv
from langchain.agents import tool, Tool
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text
import pyinputplus as pyip

# ROSA imports
from rosa import ROSA, RobotSystemPrompts

# Custom imports
from penguinpi_tools import PenguinPiTools
from penguinpi_prompts import get_prompts
from penguinpi_llm import get_llm
from penguinpi_help import get_help

from tools_prev.image_tools import IMAGE_TOOLS
from tools_prev.code_analyzer import CODE_ANALYZER_TOOLS

class PenguinPiAgent(ROSA):
    def __init__(self, streaming=False, verbose=True, prompts: RobotSystemPrompts = get_prompts()):
        """Initialize the PenguinPi Agent for ROS1 using ROSA framework"""
        
        # Store streaming parameter
        self.streaming = streaming
        
        # Initialize ROS node
        rospy.init_node('penguinpi_agent', anonymous=True)
        
        # Robot parameters (from PenguinPi specifications)
        self.wheel_separation = 0.156  # meters
        self.wheel_diameter = 0.065    # meters
        self.encoder_scale = math.pi * self.wheel_diameter / 384
        
        # Robot state
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.encoder_left = 0
        self.encoder_right = 0
        self.motor_left = 0
        self.motor_right = 0
        
        # Setup ROS publishers and subscribers
        self.setup_ros_communication()
        
        # Initialize tools
        self.penguinpi_tools = PenguinPiTools(self)
        
        # Create tools list for ROSA - basic movement and navigation tools
        tools = [
            # Movement tools
            self.penguinpi_tools.move_forward,
            self.penguinpi_tools.move_backward,
            self.penguinpi_tools.turn_left,
            self.penguinpi_tools.turn_right,
            self.penguinpi_tools.stop_robot,
            
            # Navigation tools
            self.penguinpi_tools.move_to_position,
            self.penguinpi_tools.draw_shape,
            
            # Status and monitoring tools
            self.penguinpi_tools.get_robot_pose,
            self.penguinpi_tools.get_robot_status,
            self.penguinpi_tools.check_system_health,
            self.penguinpi_tools.get_battery_status,
            self.penguinpi_tools.emergency_stop,
            self.penguinpi_tools.reset_robot_pose,
            
            # ROS system tools
            self.penguinpi_tools.get_ros_topics,
            self.penguinpi_tools.get_ros_nodes,
            self.penguinpi_tools.get_topic_frequency,
            self.penguinpi_tools.get_topic_delay,
        ]
        
        tools += IMAGE_TOOLS
        tools += CODE_ANALYZER_TOOLS
        
        # Initialize ROSA with ROS1 configuration
        super().__init__(
            ros_version=1,  # ROS1 for PenguinPi
            llm=get_llm(streaming=streaming),
            tools=tools,
            blacklist=["master", "docker"],
            prompts=prompts,
            verbose=verbose,
            accumulate_chat_history=True,
            streaming=streaming,
        )
        
        # Command handlers
        self.setup_command_handlers()
        
        # Examples for user guidance
        self.examples = [
            "Move the PenguinPi forward for 2 seconds",
            "Turn the PenguinPi left for 1 second",
            "Drive the PenguinPi in a circle",
            "Get the current robot pose",
            "Check robot status and diagnostics",
            "Move to position (1, 1) with orientation 0",
            "Draw a square with 0.5 meter sides"
        ]
        
        rospy.loginfo("PenguinPi Agent initialized successfully!")
    
    def setup_ros_communication(self):
        """Setup ROS publishers and subscribers for PenguinPi"""
        
        # Publishers - use PenguinPi namespace to match the robot simulation
        self.cmd_vel_pub = rospy.Publisher('/PenguinPi/cmd_vel', Twist, queue_size=10)
        
        # Subscribers - use PenguinPi namespace to match the robot simulation
        rospy.Subscriber('/PenguinPi/odom', Odometry, self.odom_callback)
        rospy.Subscriber('/PenguinPi/joint_states', JointState, self.joint_callback)
        rospy.Subscriber('/picam/camera/image_raw', Image, self.image_callback)
        
        # Store latest sensor data
        self.latest_image = None
        
        # Wait for publishers to be ready
        rospy.sleep(1)
    
    def setup_command_handlers(self):
        """Setup command handlers for special commands"""
        self.command_handler = {
            "help": lambda: self.submit(get_help(self.examples)),
            "examples": lambda: self.submit(self.choose_example()),
            "clear": lambda: self.clear(),
            "status": lambda: self.submit("Get the current robot status and diagnostics"),
            "pose": lambda: self.submit("What is my current position and orientation?"),
        }
    
    def odom_callback(self, msg):
        """Callback for odometry data"""
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y
        
        # Extract yaw from quaternion
        q = msg.pose.pose.orientation
        self.theta = math.atan2(2.0 * (q.w * q.z + q.x * q.y), 
                               1.0 - 2.0 * (q.y * q.y + q.z * q.z))
    
    def joint_callback(self, msg):
        """Callback for joint state data (encoders)"""
        if len(msg.position) >= 2:
            self.encoder_left = msg.position[0]
            self.encoder_right = msg.position[1]
    
    def image_callback(self, msg):
        """Callback for camera image - simplified without cv_bridge"""
        try:
            # Store raw image message for now
            self.latest_image = msg
        except Exception as e:
            rospy.logwarn(f"Error storing image: {e}")
    
    @property
    def greeting(self):
        """Generate greeting message"""
        greeting = Text(
            "\nHi! I'm the PenguinPi Agent - your personal assistant for PenguinPi robot control and debugging!\n"
        )
        greeting.stylize("frame bold blue")
        greeting.append(
            f"Try {', '.join(self.command_handler.keys())} or exit.",
            style="italic",
        )
        return greeting
    
    def choose_example(self):
        """Get user selection from the list of examples"""
        return pyip.inputMenu(
            self.examples,
            prompt="\nEnter your choice and press enter: \n",
            numbered=True,
            blank=False,
            timeout=60,
            default="1",
        )
    
    def clear(self):
        """Clear the chat history and screen"""
        self.clear_chat()
        self.last_events = []
        os.system("clear")
        rospy.loginfo("Chat history cleared")
    
    def get_input(self, prompt: str):
        """Get user input from the console"""
        return pyip.inputStr(prompt, default="help")
    
    def submit(self, query: str):
        """Submit a query to the agent using ROSA's invoke method"""
        if self.streaming:
            self.stream_response(query)
        else:
            self.print_response(query)
    
    def print_response(self, query: str):
        """Process query and print response using ROSA's invoke method"""
        console = Console()
        
        try:
            # Use ROSA's invoke method for proper tool execution
            response = self.invoke(query)
            
            content_panel = Panel(
                Markdown(response), 
                title="PenguinPi Agent Response", 
                border_style="green"
            )
            console.print(content_panel)
            
        except Exception as e:
            error_panel = Panel(
                f"Error processing request: {str(e)}", 
                title="Error", 
                border_style="red"
            )
            console.print(error_panel)
    
    def stream_response(self, query: str):
        """Stream the agent's response"""
        console = Console()
        console.print("Streaming response... (not implemented yet)")
        # Implementation for streaming would go here
    
    def run(self):
        """Run the main interaction loop"""
        console = Console()
        
        while not rospy.is_shutdown():
            try:
                console.print(self.greeting)
                user_input = self.get_input("> ")
                
                if user_input == "exit":
                    break
                elif user_input in self.command_handler:
                    self.command_handler[user_input]()
                else:
                    self.submit(user_input)
                    
            except KeyboardInterrupt:
                rospy.loginfo("Shutting down PenguinPi Agent")
                break
            except Exception as e:
                rospy.logerr(f"Error in main loop: {e}")
        
        # Clean shutdown - use internal stop method instead of LangChain tool
        self.penguinpi_tools._stop_robot()
        rospy.loginfo("PenguinPi Agent shutdown complete")

def main():
    """Main function"""
    try:
        agent = PenguinPiAgent(streaming=False, verbose=True)
        agent.run()
    except rospy.ROSInterruptException:
        rospy.loginfo("PenguinPi Agent interrupted")
    except Exception as e:
        rospy.logerr(f"Error starting PenguinPi Agent: {e}")

if __name__ == '__main__':
    main() 