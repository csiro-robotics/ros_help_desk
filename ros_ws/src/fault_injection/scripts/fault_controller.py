#!/usr/bin/env python3
"""
Fault Controller for PenguinPi Educational System
================================================

This script provides a simple controller for managing fault injection scenarios.

Features:
- Start/stop fault injection scenarios
- View system status
- Basic educational information

Usage:
    rosrun fault_injection fault_controller.py
"""

import rospy
import os
import yaml
import threading
from std_msgs.msg import String
from fault_injection.msg import FaultStatus, FaultReport


class FaultController:
    def __init__(self):
        # Initialize ROS node
        rospy.init_node('fault_controller', anonymous=True)
        
        # Load configuration
        self.load_config()
        
        # Controller state
        self.current_scenario = None
        self.fault_processes = {}
        
        # Setup communication
        self.setup_communication()
        
        # Start interactive interface
        self.start_interface()
        
        rospy.loginfo("Fault Controller initialized")
    
    def load_config(self):
        """Load fault injection configuration"""
        try:
            # Get package path
            import rospkg
            pkg_path = rospkg.RosPack().get_path('fault_injection')
            
            # Load scenarios
            scenarios_path = os.path.join(pkg_path, 'config', 'scenarios.yaml')
            with open(scenarios_path, 'r') as f:
                self.config = yaml.safe_load(f)
            
            rospy.loginfo(f"Loaded {len(self.config['scenarios'])} scenarios")
            
        except Exception as e:
            rospy.logwarn(f"Failed to load config: {e}")
            # Default scenarios
            self.config = {
                'scenarios': {
                    'keyboard_delay': {
                        'name': 'Keyboard Delay Fault',
                        'description': 'Learn to debug delayed keyboard responses',
                        'difficulty': 'beginner',
                        'duration': 300,
                        'component': 'keyboard',
                        'fault_type': 'delay'
                    },
                    'camera_delay': {
                        'name': 'Camera Delay Fault',
                        'description': 'Learn to debug delayed camera frames',
                        'difficulty': 'beginner',
                        'duration': 300,
                        'component': 'camera',
                        'fault_type': 'delay'
                    }
                }
            }
    
    def setup_communication(self):
        """Setup ROS communication"""
        # Subscribe to fault status updates
        self.keyboard_status_sub = rospy.Subscriber(
            '/fault_injection/keyboard_status',
            FaultStatus,
            self.keyboard_status_callback
        )
        
        self.camera_status_sub = rospy.Subscriber(
            '/fault_injection/camera_status',
            FaultStatus,
            self.camera_status_callback
        )
        
        # Subscribe to fault reports
        self.report_sub = rospy.Subscriber(
            '/fault_injection/fault_report',
            FaultReport,
            self.report_callback
        )
        
        # Publisher for control commands
        self.control_pub = rospy.Publisher(
            '/fault_injection/control',
            String,
            queue_size=10
        )
        
        # Store latest status
        self.keyboard_status = None
        self.camera_status = None
        self.latest_report = None
    
    def keyboard_status_callback(self, msg):
        """Handle keyboard status updates"""
        self.keyboard_status = msg
    
    def camera_status_callback(self, msg):
        """Handle camera status updates"""
        self.camera_status = msg
    
    def report_callback(self, msg):
        """Handle fault reports"""
        self.latest_report = msg
    
    def start_interface(self):
        """Start the interactive interface"""
        # Start interface thread
        self.interface_thread = threading.Thread(target=self.interface_loop)
        self.interface_thread.daemon = True
        self.interface_thread.start()
    
    def interface_loop(self):
        """Main interface loop"""
        self.display_welcome()
        
        while not rospy.is_shutdown():
            try:
                self.display_menu()
                choice = input("\nEnter your choice (1-5): ").strip()
                
                if choice == '1':
                    self.list_scenarios()
                elif choice == '2':
                    self.start_scenario()
                elif choice == '3':
                    self.stop_scenario()
                elif choice == '4':
                    self.view_status()
                elif choice == '5':
                    self.shutdown()
                    break
                else:
                    print("Invalid choice. Please enter 1-5.")
                
                input("\nPress Enter to continue...")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
                input("\nPress Enter to continue...")
    
    def display_welcome(self):
        """Display welcome message"""
        os.system('clear')
        print("="*70)
        print("PENGUINPI FAULT INJECTION EDUCATIONAL SYSTEM")
        print("="*70)
        print("Welcome to the PenguinPi Fault Injection System!")
        print()
        print("This system helps you learn to debug robotic systems by")
        print("introducing controlled faults that you must identify and fix.")
        print()
        print("Each scenario focuses on one component with one fault type.")
        print()
        input("Press Enter to continue...")
    
    def display_menu(self):
        """Display the main menu"""
        os.system('clear')
        print("="*70)
        print("FAULT INJECTION CONTROLLER")
        print("="*70)
        
        if self.current_scenario:
            scenario_config = self.config['scenarios'][self.current_scenario]
            print(f"Current Scenario: {scenario_config['name']}")
            print()
        
        print("1. List available scenarios")
        print("2. Start a fault injection scenario")
        print("3. Stop current scenario")
        print("4. View system status")
        print("5. Exit")
    
    def list_scenarios(self):
        """List all available scenarios"""
        os.system('clear')
        print("="*70)
        print("AVAILABLE SCENARIOS")
        print("="*70)
        
        for i, (scenario_key, scenario_config) in enumerate(self.config['scenarios'].items(), 1):
            print(f"{i}. {scenario_config['name']}")
            print(f"   Component: {scenario_config['component'].title()}")
            print(f"   Fault Type: {scenario_config['fault_type'].title()}")
            print(f"   Difficulty: {scenario_config['difficulty'].title()}")
            print(f"   Description: {scenario_config['description']}")
            print()
    
    def start_scenario(self):
        """Start a fault injection scenario"""
        os.system('clear')
        print("="*70)
        print("START FAULT INJECTION SCENARIO")
        print("="*70)
        
        if self.current_scenario:
            print("A scenario is already running. Stop it first.")
            return
        
        # List scenarios with numbers
        scenarios = list(self.config['scenarios'].items())
        for i, (scenario_key, scenario_config) in enumerate(scenarios, 1):
            print(f"{i}. {scenario_config['name']}")
        
        # Get user choice
        try:
            choice = int(input("\nEnter scenario number: "))
            if 1 <= choice <= len(scenarios):
                scenario_key = scenarios[choice - 1][0]
                self.execute_scenario(scenario_key)
            else:
                print("Invalid scenario number.")
        except ValueError:
            print("Please enter a valid number.")
    
    def execute_scenario(self, scenario_key):
        """Execute a fault injection scenario"""
        scenario_config = self.config['scenarios'][scenario_key]
        print(f"\nStarting scenario: {scenario_config['name']}")
        print(f"Component: {scenario_config['component']}")
        print(f"Fault Type: {scenario_config['fault_type']}")
        
        # Confirm execution
        confirm = input("Start this scenario? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Scenario start cancelled.")
            return
        
        # Start the appropriate fault injector
        if scenario_config['component'] == 'keyboard':
            self.start_keyboard_injector(scenario_key)
        elif scenario_config['component'] == 'camera':
            self.start_camera_injector(scenario_key)
        
        self.current_scenario = scenario_key
        print("Scenario started successfully!")
        print("Use 'rostopic echo /fault_injection/keyboard_status' to monitor faults")
        print("Use 'rostopic echo /fault_injection/camera_status' to monitor faults")
        print("Use 'rostopic hz /PenguinPi/cmd_vel' to check message rates")
        print("Use 'rqt_image_view' to view camera feed")
    
    def start_keyboard_injector(self, scenario_key):
        """Start keyboard fault injector"""
        import subprocess
        
        try:
            # Start keyboard fault injector
            cmd = [
                'rosrun', 'fault_injection', 'keyboard_fault_injector.py',
                f'_scenario:={scenario_key}'
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.fault_processes['keyboard'] = process
            print("  Keyboard fault injector started")
            
        except Exception as e:
            print(f"  Failed to start keyboard injector: {e}")
    
    def start_camera_injector(self, scenario_key):
        """Start camera fault injector"""
        import subprocess
        
        try:
            # Start camera fault injector
            cmd = [
                'rosrun', 'fault_injection', 'camera_fault_injector.py',
                f'_scenario:={scenario_key}'
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.fault_processes['camera'] = process
            print("  Camera fault injector started")
            
        except Exception as e:
            print(f"  Failed to start camera injector: {e}")
    
    def stop_scenario(self):
        """Stop the current fault injection scenario"""
        os.system('clear')
        print("="*70)
        print("STOP FAULT INJECTION SCENARIO")
        print("="*70)
        
        if not self.current_scenario:
            print("No scenario is currently running.")
            return
        
        scenario_config = self.config['scenarios'][self.current_scenario]
        print(f"Current scenario: {scenario_config['name']}")
        
        # Confirm stop
        confirm = input("Stop current scenario? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Stop cancelled.")
            return
        
        # Stop all fault injectors
        print("\nStopping fault injectors...")
        
        for component, process in self.fault_processes.items():
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"  Stopped {component} injector")
            except Exception as e:
                print(f"  Failed to stop {component} injector: {e}")
        
        # Clear state
        self.fault_processes.clear()
        self.current_scenario = None
        
        print("All fault injectors stopped.")
    
    def view_status(self):
        """View system status"""
        os.system('clear')
        print("="*70)
        print("SYSTEM STATUS")
        print("="*70)
        
        # Current scenario
        if self.current_scenario:
            scenario_config = self.config['scenarios'][self.current_scenario]
            print(f"Current Scenario: {scenario_config['name']}")
            print(f"   Component: {scenario_config['component'].title()}")
            print(f"   Fault Type: {scenario_config['fault_type'].title()}")
        else:
            print("No scenario running")
        
        print()
        
        # Fault status
        print("Fault Status:")
        if self.keyboard_status:
            status = self.keyboard_status
            print(f"  Keyboard: {'ACTIVE' if status.is_active else 'NORMAL'}")
            if status.is_active:
                print(f"      Mode: {status.fault_mode}")
                print(f"      Rate: {status.fault_rate*100:.1f}%")
                print(f"      Messages affected: {status.messages_affected}/{status.total_messages}")
        
        if self.camera_status:
            status = self.camera_status
            print(f"  Camera: {'ACTIVE' if status.is_active else 'NORMAL'}")
            if status.is_active:
                print(f"      Mode: {status.fault_mode}")
                print(f"      Rate: {status.fault_rate*100:.1f}%")
                print(f"      Messages affected: {status.messages_affected}/{status.total_messages}")
        
        if not self.keyboard_status and not self.camera_status:
            print("  No fault status available")
        
        print()
        print("Debugging Tips:")
        print("  • Use 'rostopic hz /PenguinPi/cmd_vel' to check message rates")
        print("  • Use 'rostopic echo /PenguinPi/cmd_vel' to check message content")
        print("  • Use 'rqt_image_view' to view camera feed")
        print("  • Use 'rqt_graph' to visualize system connections")
    
    def shutdown(self):
        """Shutdown the controller"""
        print("\nShutting down fault controller...")
        
        # Stop any running scenarios
        if self.current_scenario:
            print("  Stopping current scenario...")
            for component, process in self.fault_processes.items():
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except:
                    pass
        
        print("Fault controller shutdown complete.")
        rospy.signal_shutdown("User requested shutdown")
    
    def run(self):
        """Main run loop"""
        try:
            rospy.spin()
        except KeyboardInterrupt:
            self.shutdown()


if __name__ == '__main__':
    try:
        controller = FaultController()
        controller.run()
    except rospy.ROSInterruptException:
        pass 