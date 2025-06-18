#!/usr/bin/env python3
"""
Camera Fault Injector for PenguinPi Educational System
======================================================

This script intercepts camera image messages and injects various types of faults
to teach students about fault tolerance and debugging in robotics systems.

Fault Types:
- Delay: Adds random delays to camera images
- Drop: Randomly drops camera frames
- Corruption: Corrupts image data (noise, blur, distortion)

Usage:
    rosrun fault_injection camera_fault_injector.py _scenario:=camera_delay

Topics:
    Subscribes to: /picam/camera/image_raw_clean (original images)
    Publishes to: /picam/camera/image_raw (faulty images)
    Status: /fault_injection/camera_status
"""

import rospy
import random
import time
import numpy as np
import yaml
import os
from sensor_msgs.msg import Image, CameraInfo
from std_msgs.msg import Header
from fault_injection.msg import FaultStatus


class CameraFaultInjector:
    def __init__(self):
        # Initialize ROS node
        rospy.init_node('camera_fault_injector', anonymous=True)
        
        # Load configuration
        self.load_config()
        
        # Fault injection state
        self.fault_active = False
        self.fault_start_time = None
        self.current_scenario = None
        self.scenario_config = None
        self.messages_processed = 0
        self.messages_affected = 0
        self.last_image = None
        
        # Delayed message queue for delay faults
        self.delayed_messages = []
        
        # Publishers and Subscribers
        self.setup_communication()
        
        # Start the fault injection controller
        self.start_fault_injection()
        
        rospy.loginfo("Camera Fault Injector initialized")
        rospy.loginfo("Remapping: /picam/camera/image_raw_clean -> /picam/camera/image_raw")
        
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
                    'camera_delay': {
                        'name': 'Camera Delay Fault',
                        'component': 'camera',
                        'fault_type': 'delay',
                        'normal_duration': 60,
                        'fault_duration': 240,
                        'fault_rate': 0.4,
                        'fault_severity': 0.3,
                        'parameters': {
                            'delay_range': [0.1, 0.8],
                            'jitter': 0.05
                        }
                    }
                }
            }
    
    def setup_communication(self):
        """Setup ROS publishers and subscribers"""
        # Subscribe to clean camera images
        self.image_sub = rospy.Subscriber(
            '/picam/camera/image_raw', 
            Image, 
            self.image_callback, 
            queue_size=5
        )
        
        # Publish faulty images
        self.image_pub = rospy.Publisher(
            '/picam/camera/image_raw_dev', 
            Image, 
            queue_size=5
        )
        
        # Publish fault status
        self.status_pub = rospy.Publisher(
            '/fault_injection/camera_status',
            FaultStatus,
            queue_size=10
        )
        
        # Timer for publishing status updates
        self.status_timer = rospy.Timer(rospy.Duration(1.0), self.publish_status)
        
        # Timer for processing delayed messages
        self.delay_timer = rospy.Timer(rospy.Duration(0.1), self.process_delayed_messages)
    
    def start_fault_injection(self):
        """Start the fault injection scenario"""
        scenario_name = rospy.get_param('~scenario', 'camera_delay')
        
        if scenario_name not in self.config['scenarios']:
            rospy.logerr(f"Unknown scenario: {scenario_name}")
            return
        
        self.current_scenario = scenario_name
        self.scenario_config = self.config['scenarios'][scenario_name]
        
        # Verify this is a camera scenario
        if self.scenario_config['component'] != 'camera':
            rospy.logerr(f"Scenario {scenario_name} is not a camera scenario")
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
    
    def image_callback(self, msg):
        """Process incoming camera images"""
        self.messages_processed += 1
        self.last_image = msg
        
        if not self.fault_active:
            # Normal operation - just forward the message
            self.image_pub.publish(msg)
            return
        
        # Apply fault injection
        faulty_msg = self.apply_fault(msg)
        
        if faulty_msg is not None:
            self.image_pub.publish(faulty_msg)
    
    def apply_fault(self, msg):
        """Apply fault injection to an image message"""
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
        """Apply delay fault to image message"""
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
        
        rospy.logdebug(f"Delaying image by {delay:.3f} seconds")
        return None  # Don't publish immediately
    
    def apply_drop_fault(self, msg):
        """Apply drop fault to image message"""
        rospy.logdebug("Dropping camera frame")
        return None  # Drop the message
    
    def apply_corruption_fault(self, msg):
        """Apply corruption fault to image message"""
        try:
            # Convert ROS image data to numpy array
            if msg.encoding == 'bgr8' or msg.encoding == 'rgb8':
                channels = 3
            elif msg.encoding == 'mono8':
                channels = 1
            else:
                # Unsupported encoding, just modify timestamp
                corrupted_msg = msg
                corrupted_msg.header.stamp = rospy.Time.now()
                rospy.logdebug("Unsupported image encoding, using timestamp corruption")
                return corrupted_msg
            
            # Convert raw bytes to numpy array
            img_array = np.frombuffer(msg.data, dtype=np.uint8)
            img_array = img_array.reshape((msg.height, msg.width, channels))
            
            # Make a copy to avoid modifying the original
            corrupted_array = img_array.copy()
            
            # Add 3-5 random black rectangular regions
            num_regions = random.randint(3, 5)
            
            for _ in range(num_regions):
                # Random region size (5-20% of image dimensions)
                region_w = random.randint(msg.width // 20, msg.width // 5)
                region_h = random.randint(msg.height // 20, msg.height // 5)
                
                # Random position
                start_x = random.randint(0, max(0, msg.width - region_w))
                start_y = random.randint(0, max(0, msg.height - region_h))
                
                # Make region black
                corrupted_array[start_y:start_y+region_h, start_x:start_x+region_w] = 0
            
            # Convert back to ROS Image message
            corrupted_msg = Image()
            corrupted_msg.header = msg.header
            corrupted_msg.height = msg.height
            corrupted_msg.width = msg.width
            corrupted_msg.encoding = msg.encoding
            corrupted_msg.is_bigendian = msg.is_bigendian
            corrupted_msg.step = msg.step
            corrupted_msg.data = corrupted_array.tobytes()
            
            rospy.logdebug(f"Added {num_regions} black regions to image")
            return corrupted_msg
            
        except Exception as e:
            rospy.logwarn(f"Camera corruption fault failed: {e}")
            # Fallback - just return original message
            return msg
    
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
            self.image_pub.publish(msg)
        
        # Keep remaining messages
        self.delayed_messages = remaining_messages
    
    def publish_status(self, event):
        """Publish fault injection status"""
        status = FaultStatus()
        status.header = Header()
        status.header.stamp = rospy.Time.now()
        status.header.frame_id = "fault_injection"
        
        status.fault_type = "camera"
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
        injector = CameraFaultInjector()
        injector.run()
    except rospy.ROSInterruptException:
        pass 