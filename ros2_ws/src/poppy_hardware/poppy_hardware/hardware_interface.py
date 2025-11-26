"""
Hardware Interface Node for ESP32 Communication
Manages serial communication with ESP32 motor controller
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from poppy_interfaces.msg import RobotState, MovementCommand
import serial
import json
from typing import Optional
import struct


class HardwareInterface(Node):
    """Main hardware interface node for ESP32 communication"""

    def __init__(self):
        super().__init__('hardware_interface')
        
        # Parameters
        self.declare_parameter('serial_port', '/dev/ttyUSB0')
        self.declare_parameter('baud_rate', 115200)
        self.declare_parameter('update_rate', 50.0)  # Hz
        
        port = self.get_parameter('serial_port').value
        baud = self.get_parameter('baud_rate').value
        
        # Serial connection
        try:
            self.serial = serial.Serial(port, baud, timeout=0.1)
            self.get_logger().info(f'Connected to ESP32 on {port} at {baud} baud')
        except serial.SerialException as e:
            self.get_logger().error(f'Failed to open serial port: {e}')
            self.serial = None
        
        # Publishers
        self.state_pub = self.create_publisher(RobotState, 'robot_state', 10)
        
        # Subscribers
        self.cmd_sub = self.create_subscription(
            MovementCommand,
            'movement_command',
            self.movement_command_callback,
            10
        )
        self.twist_sub = self.create_subscription(
            Twist,
            'cmd_vel',
            self.twist_callback,
            10
        )
        
        # State variables
        self.current_mode = 0  # TRACK mode
        self.battery_voltage = 0.0
        self.emergency_stop = False
        
        # Timers
        rate = self.get_parameter('update_rate').value
        self.create_timer(1.0 / rate, self.update_loop)
        self.create_timer(0.1, self.publish_state)
        
    def movement_command_callback(self, msg: MovementCommand):
        """Handle high-level movement commands"""
        if self.serial is None:
            return
            
        command = {
            'type': 'movement',
            'cmd_type': msg.command_type,
            'distance': msg.distance_cm,
            'angle': msg.angle_degrees,
            'speed': msg.speed_percent,
            'target_mode': msg.target_mode,
            'emergency': msg.is_emergency
        }
        
        self.send_command(command)
        
    def twist_callback(self, msg: Twist):
        """Handle velocity commands (ROS2 standard)"""
        if self.serial is None:
            return
            
        command = {
            'type': 'velocity',
            'linear_x': msg.linear.x,
            'linear_y': msg.linear.y,
            'angular_z': msg.angular.z
        }
        
        self.send_command(command)
        
    def send_command(self, command: dict):
        """Send JSON command to ESP32"""
        try:
            json_str = json.dumps(command) + '\n'
            self.serial.write(json_str.encode('utf-8'))
        except Exception as e:
            self.get_logger().error(f'Failed to send command: {e}')
            
    def update_loop(self):
        """Read sensor data from ESP32"""
        if self.serial is None or not self.serial.is_open:
            return
            
        try:
            if self.serial.in_waiting > 0:
                line = self.serial.readline().decode('utf-8').strip()
                if line:
                    self.process_sensor_data(line)
        except Exception as e:
            self.get_logger().error(f'Error reading serial: {e}')
            
    def process_sensor_data(self, data: str):
        """Process sensor data from ESP32"""
        try:
            sensor_dict = json.loads(data)
            
            # Update internal state
            self.battery_voltage = sensor_dict.get('battery_voltage', 0.0)
            self.current_mode = sensor_dict.get('locomotion_mode', 0)
            self.emergency_stop = sensor_dict.get('emergency_stop', False)
            
            # Log sensor readings periodically
            if hasattr(self, '_log_counter'):
                self._log_counter += 1
            else:
                self._log_counter = 0
                
            if self._log_counter % 50 == 0:  # Every 50 updates
                self.get_logger().info(
                    f'Battery: {self.battery_voltage:.2f}V, '
                    f'Mode: {self.current_mode}, '
                    f'E-Stop: {self.emergency_stop}'
                )
                
        except json.JSONDecodeError:
            self.get_logger().warn(f'Invalid JSON from ESP32: {data}')
            
    def publish_state(self):
        """Publish complete robot state"""
        msg = RobotState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'
        
        msg.locomotion_mode = self.current_mode
        msg.battery_voltage = self.battery_voltage
        msg.battery_percentage = self.voltage_to_percentage(self.battery_voltage)
        msg.emergency_stop_active = self.emergency_stop
        msg.current_activity = 'idle'
        
        self.state_pub.publish(msg)
        
    @staticmethod
    def voltage_to_percentage(voltage: float) -> float:
        """Convert battery voltage to percentage (3S LiPo: 9.0V - 12.6V)"""
        min_voltage = 9.0
        max_voltage = 12.6
        
        if voltage <= min_voltage:
            return 0.0
        elif voltage >= max_voltage:
            return 100.0
        else:
            return ((voltage - min_voltage) / (max_voltage - min_voltage)) * 100.0
            
    def destroy_node(self):
        """Cleanup on shutdown"""
        if self.serial and self.serial.is_open:
            self.serial.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = HardwareInterface()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
