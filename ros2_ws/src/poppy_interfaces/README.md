# Custom ROS2 Message Definitions for Poppy
This package contains all custom message, service, and action definitions.

## Message Types

### Core Messages
- `RobotState.msg` - Complete robot state (position, battery, mode)
- `SensorData.msg` - Aggregated sensor readings
- `MovementCommand.msg` - Movement instructions

### Vision Messages
- `UserTracking.msg` - User position and tracking status
- `ObjectDetection.msg` - Detected obstacles

### Voice Messages
- `VoiceCommand.msg` - Parsed voice intent
- `WakeWordDetection.msg` - Wake word event

## Service Types

### Control Services
- `SetMode.srv` - Switch locomotion mode (track/leg/hybrid)
- `ExecuteSequence.srv` - Run movement sequence
- `EmergencyStop.srv` - Immediate stop

### Configuration Services
- `Calibrate.srv` - Sensor/motor calibration

## Action Types

- `NavigateToGoal.action` - Navigate to target position
- `TrackUser.action` - Follow user
- `VoiceInteraction.action` - Complete voice interaction

## Building

This package must be built before other packages:
```bash
colcon build --packages-select poppy_interfaces
source install/setup.bash
```
