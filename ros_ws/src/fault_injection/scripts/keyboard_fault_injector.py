#!/usr/bin/env python3
"""
Keyboard Fault Injector for PenguinPi Educational System
========================================================

This script intercepts keyboard control messages and injects various types of faults
to teach students about fault tolerance and debugging in robotics systems.

Fault Types:
- Delay: Adds random delays to keyboard commands
- Drop: Randomly drops keyboard commands 
- Corruption: Corrupts velocity values

Usage:
    rosrun fault_injection keyboard_fault_injector.py _scenario:=keyboard_delay

Topics:
    Subscribes to: /PenguinPi/cmd_vel_clean (original commands)
    Publishes to: /PenguinPi/cmd_vel (faulty commands)
    Status: /fault_injection/keyboard_status
"""

import rospy
import random
import time
import yaml
import os
from geometry_msgs.msg import Twist
from std_msgs.msg import Header
from fault_injection.msg import FaultStatus


class KeyboardFaultInjector:
    def __init__(self):
        # Initialize ROS node
        rospy.init_node('keyboard_fault_injector', anonymous=True)
        
        # Load configuration
        self.load_config()
        
        # Fault injection state
        self.fault_active = False
        self.fault_start_time = None
        self.current_scenario = None
        self.scenario_config = None
        self.messages_processed = 0
        self.messages_affected = 0
        
        # Delayed message queue for delay faults
        self.delayed_messages = []
        
        # Publishers and Subscribers
        self.setup_communication()
        
        # Start the fault injection controller
        self.start_fault_injection()
        
        rospy.loginfo("Keyboard Fault Injector initialized")
        rospy.loginfo("Remapping: /PenguinPi/cmd_vel_clean -> /PenguinPi/cmd_vel")
        
    def load_config(self):
        """Load fault injection configuration from YAML file"""
        try:
            # Get package path
            import rospkg
            pkg_path = rospkg.RosPack().get_path('fault_injection')
            config_path = os.path.join(pkg_path, 'config', 'scenarios.yaml')
            
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            
            rospy.loginfo(f"Loaded config from {config_path}")
        except Exception as e:
            rospy.logwarn(f"Failed to load config: {e}")
            # Default configuration
            self.config = {
                'scenarios': {
                    'keyboard_delay': {
                        'name': 'Keyboard Delay Fault',
                        'component': 'keyboard',
                        'fault_type': 'delay',
                        'normal_duration': 60,
                        'fault_duration': 240,
                        'fault_rate': 0.4,
                        'fault_severity': 0.3,
                        'parameters': {
                            'delay_range': [0.2, 1.0],
                            'jitter': 0.1
                        }
                    }
                }
            }
    
    def setup_communication(self):
        """Setup ROS publishers and subscribers"""
        # Subscribe to clean keyboard commands
        self.cmd_sub = rospy.Subscriber(
            '/PenguinPi/cmd_vel_clean', 
            Twist, 
            self.cmd_callback, 
            queue_size=10
        )
        
        # Publish faulty commands
        self.cmd_pub = rospy.Publisher(
            '/PenguinPi/cmd_vel', 
            Twist, 
            queue_size=10
        )
        
        # Publish fault status
        self.status_pub = rospy.Publisher(
            '/fault_injection/keyboard_status',
            FaultStatus,
            queue_size=10
        )
        
        # Timer for publishing status updates
        self.status_timer = rospy.Timer(rospy.Duration(1.0), self.publish_status)
        
        # Timer for processing delayed messages
        self.delay_timer = rospy.Timer(rospy.Duration(0.1), self.process_delayed_messages)
    
    def start_fault_injection(self):
        """Start the fault injection scenario"""
        scenario_name = rospy.get_param('~scenario', 'keyboard_delay')
        
        if scenario_name not in self.config['scenarios']:
            rospy.logerr(f"Unknown scenario: {scenario_name}")
            return
        
        self.current_scenario = scenario_name
        self.scenario_config = self.config['scenarios'][scenario_name]
        
        # Verify this is a keyboard scenario
        if self.scenario_config['component'] != 'keyboard':
            rospy.logerr(f"Scenario {scenario_name} is not a keyboard scenario")
            return
        
        self.fault_start_time = rospy.Time.now()
        
        rospy.loginfo(f"Starting fault injection scenario: {self.scenario_config['name']}")
        rospy.loginfo(f"Fault type: {self.scenario_config['fault_type']}")
        rospy.loginfo(f"Normal operation for {self.scenario_config['normal_duration']} seconds")
        
        # Schedule fault activation
        normal_duration = self.scenario_config['normal_duration']
        rospy.Timer(
            rospy.Duration(normal_duration), 
            self.activate_fault, 
            oneshot=True
        )
        
        # Schedule fault deactivation
        total_duration = normal_duration + self.scenario_config['fault_duration']
        rospy.Timer(
            rospy.Duration(total_duration), 
            self.deactivate_fault, 
            oneshot=True
        )
    
    def activate_fault(self, event):
        """Activate fault injection"""
        self.fault_active = True
        rospy.loginfo(f"Activating {self.scenario_config['fault_type']} fault")
        rospy.loginfo(f"Rate: {self.scenario_config['fault_rate']*100:.1f}%, Severity: {self.scenario_config['fault_severity']*100:.1f}%")
    
    def deactivate_fault(self, event):
        """Deactivate fault injection"""
        self.fault_active = False
        rospy.loginfo("Fault injection completed - returning to normal operation")
    
    def cmd_callback(self, msg):
        """Process incoming keyboard commands"""
        self.messages_processed += 1
        
        if not self.fault_active:
            # Normal operation - just forward the message
            self.cmd_pub.publish(msg)
            return
        
        # Apply fault injection
        faulty_msg = self.apply_fault(msg)
        
        if faulty_msg is not None:
            self.cmd_pub.publish(faulty_msg)
    
    def apply_fault(self, msg):
        """Apply fault injection to a command message"""
        if not self.scenario_config:
            return msg
        
        # Check if we should inject a fault
        if random.random() > self.scenario_config['fault_rate']:
            return msg  # No fault injection
        
        self.messages_affected += 1
        fault_type = self.scenario_config['fault_type']
        
        if fault_type == 'delay':
            return self.apply_delay_fault(msg)
        elif fault_type == 'drop':
            return self.apply_drop_fault(msg)
        elif fault_type == 'corruption':
            return self.apply_corruption_fault(msg)
        
        return msg
    
    def apply_delay_fault(self, msg):
        """Apply delay fault to message"""
        params = self.scenario_config['parameters']
        delay_range = params.get('delay_range', [0.1, 1.0])
        jitter = params.get('jitter', 0.1)
        
        base_delay = random.uniform(delay_range[0], delay_range[1])
        delay = base_delay + random.uniform(-jitter, jitter)
        delay = max(0.01, delay)  # Ensure minimum delay
        
        deliver_time = rospy.Time.now() + rospy.Duration(delay)
        
        self.delayed_messages.append({
            'message': msg,
            'deliver_time': deliver_time
        })
        
        rospy.logdebug(f"Delaying message by {delay:.3f} seconds")
        return None  # Don't publish immediately
    
    def apply_drop_fault(self, msg):
        """Apply drop fault to message"""
        rospy.logdebug("Dropping keyboard command")
        return None  # Drop the message
    
    def apply_corruption_fault(self, msg):
        """Apply corruption fault to message"""
        params = self.scenario_config['parameters']
        corruption_factor = params.get('corruption_factor', [0.5, 2.0])
        add_noise = params.get('add_noise', True)
        noise_std = params.get('noise_std', 0.1)
        
        corrupted_msg = Twist()
        
        # Corrupt linear velocity
        factor = random.uniform(corruption_factor[0], corruption_factor[1])
        corrupted_msg.linear.x = msg.linear.x * factor
        
        # Corrupt angular velocity
        factor = random.uniform(corruption_factor[0], corruption_factor[1])
        corrupted_msg.angular.z = msg.angular.z * factor
        
        # Add noise if enabled
        if add_noise:
            corrupted_msg.linear.x += random.gauss(0, noise_std)
            corrupted_msg.angular.z += random.gauss(0, noise_std)
        
        rospy.logdebug("Corrupting keyboard command")
        return corrupted_msg
    
    def process_delayed_messages(self, event):
        """Process delayed messages"""
        current_time = rospy.Time.now()
        
        # Find messages ready to be delivered
        ready_messages = []
        remaining_messages = []
        
        for delayed_msg in self.delayed_messages:
            if current_time >= delayed_msg['deliver_time']:
                ready_messages.append(delayed_msg['message'])
            else:
                remaining_messages.append(delayed_msg)
        
        # Publish ready messages
        for msg in ready_messages:
            self.cmd_pub.publish(msg)
        
        # Keep remaining messages
        self.delayed_messages = remaining_messages
    
    def publish_status(self, event):
        """Publish fault injection status"""
        status = FaultStatus()
        status.header = Header()
        status.header.stamp = rospy.Time.now()
        status.header.frame_id = "fault_injection"
        
        status.fault_type = "keyboard"
        status.is_active = self.fault_active
        status.messages_affected = self.messages_affected
        status.total_messages = self.messages_processed
        
        if self.fault_active and self.scenario_config:
            status.fault_mode = self.scenario_config['fault_type']
            status.fault_rate = self.scenario_config['fault_rate']
            status.fault_severity = self.scenario_config['fault_severity']
            status.description = f"Scenario: {self.scenario_config['name']}"
        else:
            status.fault_mode = "none"
            status.fault_rate = 0.0
            status.fault_severity = 0.0
            status.description = "Normal operation"
        
        self.status_pub.publish(status)
    
    def run(self):
        """Main run loop"""
        rospy.spin()


if __name__ == '__main__':
    try:
        injector = KeyboardFaultInjector()
        injector.run()
    except rospy.ROSInterruptException:
        pass 