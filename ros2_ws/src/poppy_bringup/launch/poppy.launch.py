"""
Main launch file for Poppy robot system
Starts all essential nodes
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    return LaunchDescription([
        # Launch arguments
        DeclareLaunchArgument(
            'robot_name',
            default_value='poppy',
            description='Name of the robot'
        ),
        
        DeclareLaunchArgument(
            'serial_port',
            default_value='/dev/ttyUSB0',
            description='ESP32 serial port'
        ),
        
        # Hardware interface node
        Node(
            package='poppy_hardware',
            executable='hardware_interface',
            name='hardware_interface',
            parameters=[{
                'serial_port': LaunchConfiguration('serial_port'),
                'baud_rate': 115200,
                'update_rate': 50.0
            }],
            output='screen'
        ),
        
        # Movement controller
        Node(
            package='poppy_core',
            executable='movement_controller',
            name='movement_controller',
            parameters=[{
                'max_linear_speed': 0.5,
                'max_angular_speed': 1.5
            }],
            output='screen'
        ),
        
        # Navigation node
        Node(
            package='poppy_navigation',
            executable='dwa_navigator',
            name='dwa_navigator',
            output='screen'
        ),
        
        # Vision - User tracking
        Node(
            package='poppy_vision',
            executable='user_tracking',
            name='user_tracking',
            parameters=[{
                'camera_topic': '/camera/image_raw',
                'confidence_threshold': 0.5
            }],
            output='screen'
        ),
        
        # Voice - Wake word detection
        Node(
            package='poppy_voice',
            executable='wake_word_node',
            name='wake_word_detection',
            parameters=[{
                'access_key': '',  # Set in environment
                'sensitivity': 0.75
            }],
            output='screen'
        ),
        
        # SDK Server (REST API)
        Node(
            package='poppy_sdk_server',
            executable='api_server',
            name='sdk_api_server',
            parameters=[{
                'port': 8000
            }],
            output='screen'
        ),
    ])
