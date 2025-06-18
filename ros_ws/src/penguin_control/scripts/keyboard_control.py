#!/usr/bin/env python3

# Keyboard control for PenguinPi robot using ROS topics

import rospy
import numpy as np
import cv2
import os
import time
import math

# ROS imports
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Image
from nav_msgs.msg import Odometry

# GUI packages
import pygame
import sys

class PenguinKeyboardControl:
    def __init__(self):
        # Initialize ROS node
        rospy.init_node('penguin_keyboard_control', anonymous=True)
        
        # ROS publishers and subscribers
        self.cmd_vel_pub = rospy.Publisher('/PenguinPi/cmd_vel_clean', Twist, queue_size=10)
        self.image_sub = rospy.Subscriber('/picam/camera/image_raw_dev', Image, self.image_callback)
        self.odom_sub = rospy.Subscriber('/PenguinPi/odom', Odometry, self.odom_callback)
        
        
        # Robot state
        self.current_image = None
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        
        # Control command
        self.command = {'motion': [0, 0]}  # [linear, angular]
        self.last_command = [0, 0]  # Track last sent command to avoid duplicate publishing
        self.quit = False
        self.notification = 'Teleoperate the PenguinPi with keyboard'
        
        # Speed parameters 
        self.linear_speed = 0.3  # m/s
        self.angular_speed = 0.8  # rad/s
        
        # Image saving
        self.image_id = 0
        self.save_image_flag = False
        # Use absolute path to avoid working directory issues
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.folder = os.path.join(script_dir, 'penguin_images/')
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)
            rospy.loginfo(f"Created image folder: {self.folder}")
        else:
            rospy.loginfo(f"Using existing image folder: {self.folder}")
        
        # Debug info
        rospy.loginfo(f"Image save folder: {self.folder}")
        rospy.loginfo(f"Camera topic: /picam/camera/image_raw")
        
        # Load background image if available
        try:
            self.bg = pygame.image.load('pics/gui_mask.jpg')
        except:
            # Create a simple background if image not found
            self.bg = pygame.Surface((700, 660))
            self.bg.fill((50, 50, 50))
        
        rospy.loginfo("PenguinPi Keyboard Control initialized")
    
    def image_callback(self, msg):
        try:
            # Direct conversion from ROS Image message to numpy array
            self.current_image = self._ros_image_to_numpy(msg)
            rospy.loginfo_once(f"First image received: {msg.width}x{msg.height}, encoding: {msg.encoding}")
        except Exception as e:
            rospy.logwarn_once(f"Image processing error: {e}")
            # Fallback - create placeholder image
            self.current_image = self._create_placeholder_image(f"Image Error: {str(e)[:30]}")
    
    def _ros_image_to_numpy(self, msg):
        """Convert ROS Image message directly to numpy array without cv_bridge"""
        height, width = msg.height, msg.width
        step = msg.step  # Row stride in bytes
        
        # Convert image data based on encoding
        if msg.encoding == "rgb8":
            # RGB 8-bit per channel
            if step == width * 3:
                # No padding - direct reshape
                np_arr = np.frombuffer(msg.data, dtype=np.uint8)
                image = np_arr.reshape((height, width, 3))
            else:
                # Handle row padding
                np_arr = np.frombuffer(msg.data, dtype=np.uint8)
                padded_image = np_arr.reshape((height, step))
                image = padded_image[:, :width*3].reshape((height, width, 3))
            return image
            
        elif msg.encoding == "bgr8":
            # BGR 8-bit per channel - convert to RGB
            if step == width * 3:
                # No padding - direct reshape
                np_arr = np.frombuffer(msg.data, dtype=np.uint8)
                bgr_image = np_arr.reshape((height, width, 3))
            else:
                # Handle row padding
                np_arr = np.frombuffer(msg.data, dtype=np.uint8)
                padded_image = np_arr.reshape((height, step))
                bgr_image = padded_image[:, :width*3].reshape((height, width, 3))
            
            # Convert BGR to RGB by swapping channels
            rgb_image = bgr_image[:, :, [2, 1, 0]]  # Swap B and R channels
            return rgb_image
            
        elif msg.encoding == "mono8":
            # Grayscale 8-bit - convert to RGB
            if step == width:
                # No padding
                np_arr = np.frombuffer(msg.data, dtype=np.uint8)
                gray_image = np_arr.reshape((height, width))
            else:
                # Handle row padding
                np_arr = np.frombuffer(msg.data, dtype=np.uint8)
                padded_image = np_arr.reshape((height, step))
                gray_image = padded_image[:, :width]
            
            # Convert to RGB by duplicating channels
            rgb_image = np.stack([gray_image, gray_image, gray_image], axis=2)
            return rgb_image
            
        elif msg.encoding == "rgba8":
            # RGBA 8-bit per channel - extract RGB
            if step == width * 4:
                np_arr = np.frombuffer(msg.data, dtype=np.uint8)
                rgba_image = np_arr.reshape((height, width, 4))
            else:
                np_arr = np.frombuffer(msg.data, dtype=np.uint8)
                padded_image = np_arr.reshape((height, step))
                rgba_image = padded_image[:, :width*4].reshape((height, width, 4))
            
            # Extract only RGB channels (ignore alpha)
            rgb_image = rgba_image[:, :, :3]
            return rgb_image
            
        elif msg.encoding in ["16UC1", "mono16"]:
            # 16-bit grayscale - convert to 8-bit RGB
            expected_step = width * 2  # 2 bytes per pixel
            if step == expected_step:
                np_arr = np.frombuffer(msg.data, dtype=np.uint16)
                gray_image = np_arr.reshape((height, width))
            else:
                np_arr = np.frombuffer(msg.data, dtype=np.uint8)
                padded_image = np_arr.reshape((height, step))
                gray_bytes = padded_image[:, :width*2]
                gray_image = np.frombuffer(gray_bytes.tobytes(), dtype=np.uint16).reshape((height, width))
            
            # Scale from 16-bit to 8-bit
            gray_8bit = (gray_image / 256).astype(np.uint8)
            # Convert to RGB
            rgb_image = np.stack([gray_8bit, gray_8bit, gray_8bit], axis=2)
            return rgb_image
            
        else:
            rospy.logwarn_once(f"Unsupported image encoding: {msg.encoding}")
            return self._create_placeholder_image(f"Unsupported: {msg.encoding}")
    
    def _create_placeholder_image(self, text="No Camera"):
        """Create a placeholder image with text"""
        # Create black image
        image = np.zeros((240, 320, 3), dtype=np.uint8)
        try:
            # Try cv2.putText first if available
            cv2.putText(image, text[:20], (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        except:
            # Fallback: Create visual pattern without text
            # Create a border and some basic shapes
            image[10:30, 10:310] = [255, 255, 255]  # Top border
            image[210:230, 10:310] = [255, 255, 255]  # Bottom border  
            image[10:230, 10:30] = [255, 255, 255]  # Left border
            image[10:230, 290:310] = [255, 255, 255]  # Right border
            
            # Add some pattern to indicate this is an error image
            for i in range(0, 240, 20):
                for j in range(0, 320, 20):
                    if (i // 20 + j // 20) % 2 == 0:
                        image[i:i+10, j:j+10] = [100, 100, 100]
            
        return image
    
    def odom_callback(self, msg):
        """Callback for odometry data"""
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y
        
        # Extract yaw from quaternion
        q = msg.pose.pose.orientation
        self.theta = math.atan2(2.0 * (q.w * q.z + q.x * q.y), 
                               1.0 - 2.0 * (q.y * q.y + q.z * q.z))
    
    def control(self):
        """Send velocity commands to robot - only when command changes"""
        try:
            current_command = [self.command['motion'][0], self.command['motion'][1]]
            
            # Only publish if command has changed
            if current_command != self.last_command:
                twist = Twist()
                twist.linear.x = current_command[0] * self.linear_speed
                twist.angular.z = current_command[1] * self.angular_speed
                self.cmd_vel_pub.publish(twist)
                self.last_command = current_command.copy()
                
                # Log the command change (optional - can be removed for less verbose output)
                if current_command == [0, 0]:
                    rospy.logdebug("Robot stopped")
                else:
                    rospy.loginfo(f"Command changed: linear={current_command[0]}, angular={current_command[1]}")
                    
        except Exception as e:
            rospy.logwarn(f"Error sending command: {e}")
    
    def save_current_image(self):
        """Save current camera image"""
        if self.save_image_flag:
            rospy.loginfo("Save image flag is True")
            
            if self.current_image is None:
                self.notification = 'No camera image available'
                rospy.logwarn("Cannot save: current_image is None")
                rospy.logwarn("Check if camera topic /picam/camera/image_raw is publishing")
                self.save_image_flag = False
                return
            
            try:
                filename = os.path.join(self.folder, f'img_{self.image_id}.png')
                rospy.loginfo(f"Attempting to save image to: {filename}")
                saved = False
                try:
                    # Image is already in RGB format from our direct processing
                    # Convert RGB to BGR for OpenCV saving
                    img_bgr = self.current_image[:, :, [2, 1, 0]]  # Swap R and B channels
                    rospy.loginfo(f"Image shape: {self.current_image.shape}")
                    result = cv2.imwrite(filename, img_bgr)
                    if result:
                        saved = True
                        rospy.loginfo("cv2.imwrite successful")
                    else:
                        rospy.logwarn("cv2.imwrite returned False")
                except Exception as e:
                    rospy.logwarn(f"cv2.imwrite failed: {e}")
                
                # Method 2: Fallback to PIL if cv2 fails
                if not saved:
                    try:
                        from PIL import Image as PILImage
                        pil_image = PILImage.fromarray(self.current_image, 'RGB')
                        pil_image.save(filename)
                        saved = True
                        rospy.loginfo("PIL save successful")
                    except ImportError:
                        rospy.logwarn("PIL not available for image saving")
                    except Exception as e:
                        rospy.logwarn(f"PIL save failed: {e}")
                
                # Method 3: Final fallback - save raw numpy array
                if not saved:
                    try:
                        np_filename = filename.replace('.png', '.npy')
                        np.save(np_filename, self.current_image)
                        filename = np_filename
                        saved = True
                        rospy.loginfo(f"NumPy save successful: {np_filename}")
                    except Exception as e:
                        rospy.logwarn(f"Numpy save failed: {e}")
                
                if saved:
                    self.image_id += 1
                    self.notification = f'Image saved: img_{self.image_id-1}.png'
                    rospy.loginfo(f"Image saved successfully: {filename}")
                else:
                    self.notification = 'Failed to save image - all methods failed'
                    rospy.logerr("All image save methods failed")
                    
            except Exception as e:
                self.notification = f'Error saving image: {e}'
                rospy.logerr(f"Exception in save_current_image: {e}")
            finally:
                self.save_image_flag = False
    
    def draw(self, canvas):
        """Draw the GUI"""
        canvas.blit(self.bg, (0, 0))
        text_colour = (220, 220, 220)
        v_pad = 40
        h_pad = 20
        
        # Display camera image
        if self.current_image is not None:
            try:
                # Resize image using numpy-based method instead of cv2.resize
                robot_view = self._resize_image(self.current_image, (320, 240))
                self.draw_pygame_window(canvas, robot_view, position=(h_pad, v_pad))
            except Exception as e:
                rospy.logwarn_once(f"Error displaying image: {e}")
        
        # Add captions
        self.put_caption(canvas, caption='PenguinPi Camera', position=(h_pad, v_pad))
        
        # Control Instructions (right side of camera)
        instructions_x = h_pad + 350
        instructions_y = v_pad + 20
        
        # Title
        title_surface = TITLE_FONT.render("=== Controls ===", False, (255, 255, 0))
        canvas.blit(title_surface, (instructions_x, instructions_y))
        
        # Instructions
        instructions = [
            "↑ : Move forward",
            "↓ : Move backward", 
            "← : Turn left",
            "→ : Turn right",
            "SPACE : Stop",
            "I : Save image",
            "ESC : Quit"
        ]
        
        for i, instruction in enumerate(instructions):
            y_pos = instructions_y + 40 + (i * 25)
            text_surface = TEXT_FONT.render(instruction, False, text_colour)
            canvas.blit(text_surface, (instructions_x, y_pos))
        
        # Status information
        status_text = f"Position: ({self.x:.2f}, {self.y:.2f}) | Angle: {math.degrees(self.theta):.1f}°"
        status_surface = TEXT_FONT.render(status_text, False, text_colour)
        canvas.blit(status_surface, (h_pad, 300))
        
        # Control information
        control_text = f"Linear: {self.command['motion'][0]} | Angular: {self.command['motion'][1]}"
        control_surface = TEXT_FONT.render(control_text, False, text_colour)
        canvas.blit(control_surface, (h_pad, 330))
        
        # Notification
        notification_surface = TEXT_FONT.render(self.notification, False, text_colour)
        canvas.blit(notification_surface, (h_pad + 10, 596))
        
        return canvas
    
    def _resize_image(self, image, target_size):
        """Resize image using numpy (fallback if cv2.resize fails)"""
        try:
            # Try cv2.resize first (fastest)
            return cv2.resize(image, target_size)
        except:
            # Fallback to simple numpy-based nearest neighbor resizing
            target_width, target_height = target_size
            orig_height, orig_width = image.shape[:2]
            
            # Calculate step sizes
            step_x = orig_width / target_width
            step_y = orig_height / target_height
            
            # Create coordinate arrays
            y_coords = np.arange(target_height) * step_y
            x_coords = np.arange(target_width) * step_x
            
            # Round to nearest integers
            y_coords = np.clip(y_coords.astype(int), 0, orig_height - 1)
            x_coords = np.clip(x_coords.astype(int), 0, orig_width - 1)
            
            # Sample the image
            resized = image[np.ix_(y_coords, x_coords)]
            
            return resized
    
    @staticmethod
    def draw_pygame_window(canvas, cv2_img, position):
        """Draw OpenCV image on pygame canvas"""
        cv2_img = np.rot90(cv2_img)
        view = pygame.surfarray.make_surface(cv2_img)
        view = pygame.transform.flip(view, True, False)
        canvas.blit(view, position)
    
    @staticmethod
    def put_caption(canvas, caption, position, text_colour=(200, 200, 200)):
        """Put caption text on canvas"""
        caption_surface = TITLE_FONT.render(caption, False, text_colour)
        canvas.blit(caption_surface, (position[0], position[1] - 25))
    
    def update_keyboard(self):
        """Handle keyboard input - continuous key state checking"""
        # Handle discrete events (like quit)
        for event in pygame.event.get():
            # Save image
            if event.type == pygame.KEYDOWN and event.key == pygame.K_i:
                self.save_image_flag = True
                self.notification = "Saving image..."
                rospy.loginfo("I key pressed - saving image")
            # Quit
            elif event.type == pygame.QUIT:
                self.quit = True
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.quit = True
        
        # Check continuous key states for movement
        keys = pygame.key.get_pressed()
        
        # Reset motion command
        linear = 0
        angular = 0
        
        # Don't override save/error notifications with movement messages
        update_movement_notification = not (self.save_image_flag or 
                                          "saved" in self.notification.lower() or 
                                          "error" in self.notification.lower() or
                                          "failed" in self.notification.lower())
        
        # Check movement keys - only move while held down
        if keys[pygame.K_UP]:
            linear = 1
            if update_movement_notification:
                self.notification = "Moving forward"
        elif keys[pygame.K_DOWN]:
            linear = -1
            if update_movement_notification:
                self.notification = "Moving backward"
        
        if keys[pygame.K_LEFT]:
            angular = 1
            if update_movement_notification:
                self.notification = "Turning left"
        elif keys[pygame.K_RIGHT]:
            angular = -1
            if update_movement_notification:
                self.notification = "Turning right"
        
        # Handle diagonal movement (forward/back + turn)
        if (keys[pygame.K_UP] or keys[pygame.K_DOWN]) and (keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]):
            if update_movement_notification:
                if keys[pygame.K_UP] and keys[pygame.K_LEFT]:
                    self.notification = "Moving forward left"
                elif keys[pygame.K_UP] and keys[pygame.K_RIGHT]:
                    self.notification = "Moving forward right"
                elif keys[pygame.K_DOWN] and keys[pygame.K_LEFT]:
                    self.notification = "Moving backward left"
                elif keys[pygame.K_DOWN] and keys[pygame.K_RIGHT]:
                    self.notification = "Moving backward right"
        
        # Stop command (space bar for manual stop, but not required)
        if keys[pygame.K_SPACE]:
            linear = 0
            angular = 0
            if update_movement_notification:
                self.notification = "Manual stop"
        
        # Update motion command
        self.command['motion'] = [linear, angular]
        
        # Update notification if no movement (only if not showing save/error messages)
        if linear == 0 and angular == 0 and not keys[pygame.K_SPACE]:
            if update_movement_notification:
                self.notification = "Robot stopped (release keys)"
        
        if self.quit:
            # Send stop command before quitting - force publish even if it was the last command
            stop_twist = Twist()
            self.cmd_vel_pub.publish(stop_twist)
            rospy.loginfo("Sending final stop command before exit")
            pygame.quit()
            rospy.signal_shutdown("User requested shutdown")
            sys.exit()

def main():
    """Main function"""
    # Declare global variables first
    global TITLE_FONT, TEXT_FONT
    
    try:
        # Initialize pygame
        pygame.init()
        pygame.font.init()
        
        # Load fonts (with fallback)
        try:
            TITLE_FONT = pygame.font.Font('pics/8-BitMadness.ttf', 35)
            TEXT_FONT = pygame.font.Font('pics/8-BitMadness.ttf', 25)
        except:
            TITLE_FONT = pygame.font.Font(None, 35)
            TEXT_FONT = pygame.font.Font(None, 25)
        
        # Setup display
        width, height = 700, 660
        canvas = pygame.display.set_mode((width, height))
        pygame.display.set_caption('PenguinPi Keyboard Control')
        
        try:
            pygame.display.set_icon(pygame.image.load('pics/8bit/pibot5.png'))
        except:
            pass  # Ignore if icon not found
        
        canvas.fill((0, 0, 0))
        pygame.display.update()
        
        # Initialize controller
        controller = PenguinKeyboardControl()
        
        # Main control loop
        clock = pygame.time.Clock()
        
        print("\n=== PenguinPi Keyboard Control ===")
        print("Controls:")
        print("  ↑ : Move forward")
        print("  ↓ : Move backward") 
        print("  ← : Turn left")
        print("  → : Turn right")
        print("  SPACE : Stop")
        print("  I : Save image")
        print("  ESC : Quit")
        print("====================================\n")
        
        while not rospy.is_shutdown() and not controller.quit:
            # Handle events
            controller.update_keyboard()
            
            # Send control commands
            controller.control()
            
            # Save image if requested
            controller.save_current_image()
            
            # Update display
            controller.draw(canvas)
            pygame.display.update()
            
            # Control loop rate
            clock.tick(30)  # 30 FPS
        
    except rospy.ROSInterruptException:
        rospy.loginfo("ROS interrupted")
    except Exception as e:
        rospy.logerr(f"Error in main: {e}")
    finally:
        # Cleanup
        try:
            pygame.quit()
        except:
            pass

if __name__ == "__main__":
    main() 