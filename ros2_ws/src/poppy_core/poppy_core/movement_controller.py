"""
Movement Controller Node
Manages hybrid locomotion and mode transformations
"""

import rclpy
from rclpy.node import Node
from poppy_interfaces.msg import MovementCommand, RobotState
from poppy_interfaces.srv import SetMode
from geometry_msgs.msg import Twist
import math


class MovementController(Node):
    """High-level movement control and mode management"""

    def __init__(self):
        super().__init__('movement_controller')
        
        # Parameters
        self.declare_parameter('max_linear_speed', 0.5)  # m/s
        self.declare_parameter('max_angular_speed', 1.5)  # rad/s
        self.declare_parameter('track_to_leg_time', 3.0)  # seconds
        
        # State
        self.current_mode = 0  # TRACK
        self.transforming = False
        
        # Publishers
        self.cmd_pub = self.create_publisher(MovementCommand, 'movement_command', 10)
        self.vel_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        
        # Subscribers
        self.state_sub = self.create_subscription(
            RobotState,
            'robot_state',
            self.state_callback,
            10
        )
        
        # Services
        self.mode_service = self.create_service(
            SetMode,
            'set_mode',
            self.handle_set_mode
        )
        
        self.get_logger().info('Movement controller initialized')
        
    def state_callback(self, msg: RobotState):
        """Update internal state from robot"""
        self.current_mode = msg.locomotion_mode
        
    def handle_set_mode(self, request, response):
        """Handle mode change requests"""
        start_time = self.get_clock().now()
        
        if request.desired_mode == self.current_mode:
            response.success = True
            response.message = 'Already in requested mode'
            response.current_mode = self.current_mode
            response.transformation_duration_sec = 0.0
            return response
        
        # Send transformation command
        cmd = MovementCommand()
        cmd.header.stamp = self.get_clock().now().to_msg()
        cmd.command_type = 5  # TYPE_TRANSFORM
        cmd.target_mode = request.desired_mode
        cmd.is_emergency = False
        
        self.cmd_pub.publish(cmd)
        self.get_logger().info(
            f'Transforming from mode {self.current_mode} to {request.desired_mode}'
        )
        
        # Wait for transformation (simplified - production would monitor state)
        transform_time = self.get_parameter('track_to_leg_time').value
        duration = (self.get_clock().now() - start_time).nanoseconds / 1e9
        
        response.success = True
        response.message = f'Mode changed to {request.desired_mode}'
        response.current_mode = request.desired_mode
        response.transformation_duration_sec = duration
        
        return response
        
    def forward(self, distance_cm: float, speed_percent: float = 50.0):
        """Move forward by distance"""
        cmd = MovementCommand()
        cmd.header.stamp = self.get_clock().now().to_msg()
        cmd.command_type = 0  # TYPE_FORWARD
        cmd.distance_cm = distance_cm
        cmd.speed_percent = speed_percent
        cmd.is_emergency = False
        
        self.cmd_pub.publish(cmd)
        
    def turn(self, angle_degrees: float, speed_percent: float = 50.0):
        """Turn by angle (positive = left, negative = right)"""
        cmd = MovementCommand()
        cmd.header.stamp = self.get_clock().now().to_msg()
        cmd.command_type = 2 if angle_degrees > 0 else 3  # LEFT or RIGHT
        cmd.angle_degrees = abs(angle_degrees)
        cmd.speed_percent = speed_percent
        cmd.is_emergency = False
        
        self.cmd_pub.publish(cmd)
        
    def stop(self, emergency: bool = False):
        """Stop all movement"""
        cmd = MovementCommand()
        cmd.header.stamp = self.get_clock().now().to_msg()
        cmd.command_type = 4  # TYPE_STOP
        cmd.is_emergency = emergency
        
        self.cmd_pub.publish(cmd)
        
        # Also publish zero velocity for immediate effect
        twist = Twist()
        self.vel_pub.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = MovementController()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
