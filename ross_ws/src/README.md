# ROS2 Packages Source Directory

This directory will contain all ROS2 packages for the Poppy robot.

## Planned Packages

1. **poppy_interfaces** - Custom message and service definitions
2. **poppy_core** - Core functionality and robot state management
3. **poppy_hardware** - Hardware interface and drivers
  4. **poppy_navigation** - Navigation, pathfinding, obstacle avoidance
5. **poppy_vision** - Computer vision and tracking
6. **poppy_voice** - Wake word detection and voice assistant
7. **poppy_sdk_server** - REST API server for Python SDK
8. **poppy_bringup** - Launch files and system configuration

Create packages using:
```bash
ros2 pkg create --build-type ament_python <package_name> --dependencies rclpy
# or for C++
ros2 pkg create --build-type ament_cmake <package_name> --dependencies rclcpp
```
