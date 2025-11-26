"""
Navigation Node with DWA Algorithm
Dynamic obstacle avoidance and path planning
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, Pose2D
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry
from poppy_interfaces.msg import RobotState
import numpy as np
import math


class DWANavigator(Node):
    """Dynamic Window Approach navigation"""

    def __init__(self):
        super().__init__('dwa_navigator')
        
        # Robot parameters
        self.max_speed = 0.5  # m/s
        self.min_speed = -0.2  # m/s
        self.max_yaw_rate = 1.5  # rad/s
        self.max_accel = 0.5  # m/s²
        self.max_yaw_accel = 1.0  # rad/s²
        
        # DWA parameters
        self.dt = 0.1  # Time step
        self.predict_time = 2.0  # Prediction horizon  
        self.heading_weight = 0.3
        self.clearance_weight = 0.2
        self.velocity_weight = 0.5
        
        # State
        self.current_pose = Pose2D()
        self.current_velocity = Twist()
        self.goal_pose = Pose2D()
        self.obstacles = []
        self.emergency_stop = False
        
        # Publishers
        self.cmd_vel_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        
        # Subscribers
        self.odom_sub = self.create_subscription(
            Odometry,
            'odom',
            self.odom_callback,
            10
        )
        
        self.scan_sub = self.create_subscription(
            LaserScan,
            'scan',
            self.scan_callback,
            10
        )
        
        self.state_sub = self.create_subscription(
            RobotState,
            'robot_state',
            self.state_callback,
            10
        )
        
        # Navigation timer
        self.create_timer(self.dt, self.navigate)
        
        self.get_logger().info('DWA Navigator initialized')
        
    def odom_callback(self, msg: Odometry):
        """Update current pose from odometry"""
        self.current_pose.x = msg.pose.pose.position.x
        self.current_pose.y = msg.pose.pose.position.y
        
        # Extract yaw from quaternion
        q = msg.pose.pose.orientation
        self.current_pose.theta = math.atan2(
            2.0 * (q.w * q.z + q.x * q.y),
            1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        )
        
        self.current_velocity = msg.twist.twist
        
    def scan_callback(self, msg: LaserScan):
        """Process laser scan for obstacles"""
        self.obstacles = []
        
        for i, distance in enumerate(msg.ranges):
            if math.isfinite(distance) and distance < msg.range_max:
                angle = msg.angle_min + i * msg.angle_increment
                
                # Convert to Cartesian coordinates
                x = distance * math.cos(angle)
                y = distance * math.sin(angle)
                
                self.obstacles.append((x, y))
                
    def state_callback(self, msg: RobotState):
        """Update emergency stop status"""
        self.emergency_stop = msg.emergency_stop_active
        
    def navigate(self):
        """Main navigation loop using DWA"""
        if self.emergency_stop:
            # Publish stop command
            self.cmd_vel_pub.publish(Twist())
            return
            
        if not self.has_goal():
            return
            
        # Calculate dynamic window
        dw = self.calc_dynamic_window()
        
        # Evaluate trajectories
        best_v, best_w = self.calc_control_and_trajectory(dw)
        
        # Publish velocity command
        cmd = Twist()
        cmd.linear.x = best_v
        cmd.angular.z = best_w
        
        self.cmd_vel_pub.publish(cmd)
        
    def calc_dynamic_window(self):
        """Calculate dynamic window based on current velocity and constraints"""
        # Dynamic window from robot dynamics
        vs = [
            self.current_velocity.linear.x - self.max_accel * self.dt,
            self.current_velocity.linear.x + self.max_accel * self.dt,
            self.min_speed,
            self.max_speed
        ]
        
        ws = [
            self.current_velocity.angular.z - self.max_yaw_accel * self.dt,
            self.current_velocity.angular.z + self.max_yaw_accel * self.dt,
            -self.max_yaw_rate,
            self.max_yaw_rate
        ]
        
        dw = [
            max(vs[0], vs[2]),
            min(vs[1], vs[3]),
            max(ws[0], ws[2]),
            min(ws[1], ws[3])
        ]
        
        return dw
        
    def calc_control_and_trajectory(self, dw):
        """Evaluate trajectories and select best control"""
        min_cost = float('inf')
        best_v = 0.0
        best_w = 0.0
        
        # Sample velocities
        v_resolution = 0.05
        w_resolution = 0.1
        
        for v in np.arange(dw[0], dw[1], v_resolution):
            for w in np.arange(dw[2], dw[3], w_resolution):
                # Predict trajectory
                trajectory = self.predict_trajectory(v, w)
                
                # Calculate cost
                heading_cost = self.calc_heading_cost(trajectory)
                clearance_cost = self.calc_clearance_cost(trajectory)
                velocity_cost = self.calc_velocity_cost(v)
                
                total_cost = (
                    self.heading_weight * heading_cost +
                    self.clearance_weight * clearance_cost +
                    self.velocity_weight * velocity_cost
                )
                
                if total_cost < min_cost:
                    min_cost = total_cost
                    best_v = v
                    best_w = w
                    
        return best_v, best_w
        
    def predict_trajectory(self, v, w):
        """Predict trajectory for given velocities"""
        trajectory = []
        x, y, theta = self.current_pose.x, self.current_pose.y, self.current_pose.theta
        
        time = 0.0
        while time <= self.predict_time:
            x += v * math.cos(theta) * self.dt
            y += v * math.sin(theta) * self.dt
            theta += w * self.dt
            time += self.dt
            
            trajectory.append((x, y, theta))
            
        return trajectory
        
    def calc_heading_cost(self, trajectory):
        """Cost based on heading toward goal"""
        if not trajectory:
            return float('inf')
            
        final_x, final_y, final_theta = trajectory[-1]
        
        # Angle to goal
        dx = self.goal_pose.x - final_x
        dy = self.goal_pose.y - final_y
        goal_angle = math.atan2(dy, dx)
        
        # Angular difference
        angle_diff = abs(self.normalize_angle(goal_angle - final_theta))
        
        return angle_diff
        
    def calc_clearance_cost(self, trajectory):
        """Cost based on clearance from obstacles"""
        if not self.obstacles:
            return 0.0  # No obstacles
            
        min_clearance = float('inf')
        
        for x, y, _ in trajectory:
            for ox, oy in self.obstacles:
                dist = math.hypot(x - ox, y - oy)
                min_clearance = min(min_clearance, dist)
                
        # Higher cost for closer obstacles
        if min_clearance < 0.2:  # Danger zone
            return 1.0
        else:
            return 1.0 / (min_clearance + 0.1)
            
    def calc_velocity_cost(self, v):
        """Cost based on forward velocity (prefer faster)"""
        return (self.max_speed - abs(v)) / self.max_speed
        
    @staticmethod
    def normalize_angle(angle):
        """Normalize angle to [-pi, pi]"""
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle
        
    def has_goal(self):
        """Check if there's a valid goal"""
        return self.goal_pose.x != 0 or self.goal_pose.y != 0
        
    def set_goal(self, x: float, y: float):
        """Set navigation goal"""
        self.goal_pose.x = x
        self.goal_pose.y = y
        self.get_logger().info(f'New goal set: ({x:.2f}, {y:.2f})')


def main(args=None):
    rclpy.init(args=args)
    node = DWANavigator()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
