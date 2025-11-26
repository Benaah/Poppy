"""
User Tracking Node using MediaPipe
Detects and tracks users with camera
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from poppy_interfaces.msg import UserTracking
from cv_bridge import CvBridge
import cv2
import mediapipe as mp
import numpy as np
from geometry_msgs.msg import Point, Vector3


class UserTrackingNode(Node):
    """Vision-based user detection and tracking"""

    def __init__(self):
        super().__init__('user_tracking')
        
        # Parameters
        self.declare_parameter('camera_topic', '/camera/image_raw')
        self.declare_parameter('confidence_threshold', 0.5)
        self.declare_parameter('camera_fov_horizontal', 62.2)  # degrees
        self.declare_parameter('camera_height', 0.15)  # meters
        
        # MediaPipe setup
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        self.bridge = CvBridge()
        self.latest_image = None
        
        # Publishers
        self.tracking_pub = self.create_publisher(UserTracking, 'user_tracking', 10)
        self.debug_image_pub = self.create_publisher(Image, 'tracking/debug_image', 10)
        
        # Subscribers
        camera_topic = self.get_parameter('camera_topic').value
        self.image_sub = self.create_subscription(
            Image,
            camera_topic,
            self.image_callback,
            10
        )
        
        # Processing timer
        self.create_timer(0.1, self.process_frame)  # 10 Hz
        
        self.get_logger().info('User tracking node initialized')
        
    def image_callback(self, msg: Image):
        """Store latest image"""
        self.latest_image = msg
        
    def process_frame(self):
        """Process image for person detection"""
        if self.latest_image is None:
            return
            
        try:
            # Convert ROS image to OpenCV
            cv_image = self.bridge.imgmsg_to_cv2(self.latest_image, 'bgr8')
            
            # Convert to RGB for MediaPipe
            rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            
            # Process with MediaPipe
            results = self.pose.process(rgb_image)
            
            # Create tracking message
            tracking_msg = UserTracking()
            tracking_msg.header.stamp = self.get_clock().now().to_msg()
            tracking_msg.header.frame_id = 'camera_link'
            
            if results.pose_landmarks:
                # Person detected
                tracking_msg.user_detected = True
                tracking_msg.confidence = 0.9  # Simplified
                
                # Calculate bounding box from landmarks
                landmarks = results.pose_landmarks.landmark
                xs = [lm.x for lm in landmarks]
                ys = [lm.y for lm in landmarks]
                
                tracking_msg.bbox_x = min(xs)
                tracking_msg.bbox_y = min(ys)
                tracking_msg.bbox_width = max(xs) - min(xs)
                tracking_msg.bbox_height = max(ys) - min(ys)
                
                # Calculate center position
                center_x = (min(xs) + max(xs)) / 2.0
                center_y = (min(ys) + max(ys)) / 2.0
                
                # Estimate distance and angle
                tracking_msg.distance_meters = self.estimate_distance(
                    tracking_msg.bbox_height
                )
                tracking_msg.angle_degrees = self.pixel_to_angle(
                    center_x, 
                    cv_image.shape[1]
                )
                
                # Quality based on bbox size
                if tracking_msg.bbox_width * tracking_msg.bbox_height > 0.15:
                    tracking_msg.tracking_quality = 3  # EXCELLENT
                elif tracking_msg.bbox_width * tracking_msg.bbox_height > 0.08:
                    tracking_msg.tracking_quality = 2  # GOOD
                else:
                    tracking_msg.tracking_quality = 1  # LOW
                    
                # Draw on debug image
                if self.debug_image_pub.get_subscription_count() > 0:
                    debug_image = cv_image.copy()
                    
                    # Draw bounding box
                    h, w = debug_image.shape[:2]
                    x1 = int(tracking_msg.bbox_x * w)
                    y1 = int(tracking_msg.bbox_y * h)
                    x2 = int((tracking_msg.bbox_x + tracking_msg.bbox_width) * w)
                    y2 = int((tracking_msg.bbox_y + tracking_msg.bbox_height) * h)
                    
                    cv2.rectangle(debug_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    # Draw info
                    cv2.putText(
                        debug_image,
                        f'Distance: {tracking_msg.distance_meters:.2f}m',
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1.0,
                        (0, 255, 0),
                        2
                    )
                    cv2.putText(
                        debug_image,
                        f'Angle: {tracking_msg.angle_degrees:.1f}deg',
                        (10, 65),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1.0,
                        (0, 255, 0),
                        2
                    )
                    
                    # Publish debug image
                    debug_msg = self.bridge.cv2_to_imgmsg(debug_image, 'bgr8')
                    self.debug_image_pub.publish(debug_msg)
                
            else:
                # No person detected
                tracking_msg.user_detected = False
                tracking_msg.tracking_quality = 0  # LOST
                tracking_msg.confidence = 0.0
            
            # Publish tracking data
            self.tracking_pub.publish(tracking_msg)
            
        except Exception as e:
            self.get_logger().error(f'Error processing frame: {e}')
            
    def estimate_distance(self, bbox_height: float) -> float:
        """
        Estimate distance based on bounding box height
        Simplified inverse relationship
        """
        if bbox_height > 0.01:
            # Rough estimation: larger bbox = closer
            # Calibrate this based on actual measurements
            return max(0.5, min(3.0, 1.5 / bbox_height))
        return 3.0
        
    def pixel_to_angle(self, normalized_x: float, image_width: int) -> float:
        """
        Convert pixel position to angle relative to camera center
        normalized_x: 0.0 (left) to 1.0 (right)
        Returns: angle in degrees (+left, -right)
        """
        fov = self.get_parameter('camera_fov_horizontal').value
        
        # Center is at 0.5
        offset_from_center = normalized_x - 0.5
        
        # Convert to angle
        angle = offset_from_center * fov
        
        return angle
        
    def destroy_node(self):
        """Cleanup"""
        self.pose.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = UserTrackingNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
