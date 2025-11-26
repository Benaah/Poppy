# Poppy ROS2 Workspace

This directory contains the ROS2 Humble workspace for the Poppy interactive robot.

## Package Structure

- `poppy_core` - Core robot functionality and launch files
- `poppy_navigation` - Navigation, pathfinding, and obstacle avoidance
- `poppy_vision` - Computer vision and user tracking
- `poppy_voice` - Wake word detection and voice assistant integration
- `poppy_interfaces` - Custom message and service definitions
- `poppy_bringup` - Launch files and configuration

## Building

```bash
cd ros2_ws
colcon build --symlink-install
source install/setup.bash
```

## Running

```bash
# Launch all systems
ros2 launch poppy_bringup poppy.launch.py

# Launch individual subsystems
ros2 launch poppy_voice voice_system.launch.py
ros2 launch poppy_vision tracking_system.launch.py
ros2 launch poppy_navigation nav_system.launch.py
```

## Testing

```bash
colcon test
colcon test-result --verbose
```
