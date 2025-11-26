# Poppy Robot - Command Reference

## Overview
This document provides a comprehensive reference for all available commands in the Poppy robot system, including mobile app commands, voice commands, and direct control commands.

##  Mobile App Commands

### iOS App Commands
The iOS app provides both basic movement controls and advanced system management through the `RobotConnection` class.

#### Movement Commands
- `sendMovementCommand(forward: Double, turn: Double)` - Send combined movement command
- `sendTurnCommand(angle: Double)` - Send turn command
- `sendStopCommand()` - Stop all movement

#### System Commands
- `sendDockingCommand()` - Start autonomous docking
- `sendUndockingCommand()` - Stop docking and undock
- `sendCalibrationCommand()` - General system calibration
- `sendEmergencyStop()` - Emergency stop all systems
- `sendBatteryStatusRequest()` - Get battery information
- `sendSystemStatusRequest()` - Get comprehensive system status

#### Feature Toggle Commands
- `sendSpatialAwarenessToggle(enabled: Bool)` - Enable/disable spatial awareness
- `sendAdaptivePIDToggle(enabled: Bool)` - Enable/disable adaptive PID
- `sendVoiceControlToggle(enabled: Bool)` - Enable/disable voice control

#### Calibration Commands
- `sendIMUCalibration()` - Calibrate IMU sensors
- `sendSpatialCalibration()` - Calibrate spatial awareness
- `sendDockingCalibration()` - Calibrate docking system
- `sendMotorTest()` - Test motor functionality

### Android App Commands
The Android app provides similar functionality through button-based interface.

#### Available Button Commands
- **Find Face** - `find_face`
- **Dance** - `dance`
- **Dock** - `docking_start`
- **Stop** - `stop`
- **IMU Calibration** - `imu_calibrate`
- **Spatial Calibration** - `spatial_calibrate`
- **Battery Status** - `battery_status`
- **System Status** - `system_status`
- **Emergency Stop** - `emergency_stop`

##  Voice Commands

### Google Assistant & Amazon Alexa
Both voice assistants support the same command set through the unified voice control system.

#### Movement Commands
- "move forward" / "go forward"
- "move backward" / "go backward"
- "turn left"
- "turn right"
- "stop" / "halt" / "pause"

#### Navigation Commands
- "find face" / "look for people" / "search for faces"
- "come here"
- "follow me"
- "go home"

#### Docking Commands
- "dock" / "go to charging station" / "charge"
- "undock" / "leave charging station"

#### Status Commands
- "status"
- "battery" / "battery status"
- "health"
- "system status"

#### Entertainment Commands
- "dance"
- "spin"
- "wave"
- "nod"

#### System Commands
- "restart"
- "calibrate"
- "test"
- "emergency stop"

#### Calibration Commands
- "calibrate imu"
- "calibrate spatial"
- "calibrate docking"
- "test motors"

#### Feature Toggle Commands
- "enable spatial awareness" / "disable spatial awareness"
- "enable adaptive pid" / "disable adaptive pid"
- "enable voice control" / "disable voice control"

##  Direct Control Commands

### WebSocket Commands
These commands are sent directly to the robot control system via WebSocket.

#### Movement Commands
- `move,<value>` - Move forward/backward (positive/negative value)
- `turn,<angle>` - Turn left/right (positive/negative angle)

#### System Commands
- `find_face` - Start face detection and tracking
- `dance` - Execute dance sequence
- `stop` - Stop all movement
- `calibrate` - General system calibration
- `emergency_stop` - Emergency stop all systems

#### Docking Commands
- `docking_start` - Start autonomous docking sequence
- `docking_stop` - Stop docking and undock

#### Status Commands
- `battery_status` - Get battery information
- `system_status` - Get comprehensive system status

#### Calibration Commands
- `imu_calibrate` - Calibrate IMU sensors
- `spatial_calibrate` - Calibrate spatial awareness system
- `docking_calibrate` - Calibrate docking system
- `motor_test` - Test motor functionality

#### Feature Toggle Commands
- `spatial_awareness_on` / `spatial_awareness_off`
- `adaptive_pid_on` / `adaptive_pid_off`
- `voice_control_on` / `voice_control_off`

##  Command Categories

### 1. Movement Control
- **Basic Movement**: Forward, backward, left turn, right turn
- **Precise Control**: Slider-based movement with speed control
- **Emergency Stop**: Immediate halt of all movement

### 2. Navigation & AI
- **Face Detection**: Find and track human faces
- **Spatial Awareness**: Obstacle detection and avoidance
- **Voice Control**: Natural language command processing

### 3. System Management
- **Calibration**: IMU, spatial, and docking system calibration
- **Status Monitoring**: Battery, system health, and performance metrics
- **Feature Toggles**: Enable/disable various system features

### 4. Autonomous Operations
- **Docking**: Automatic charging station detection and docking
- **Charging**: Battery management and charging control
- **Safety**: Emergency stop and safety system management

### 5. Entertainment
- **Dance**: Pre-programmed dance sequences
- **Gestures**: Wave, nod, spin movements
- **Interactive**: Voice-controlled entertainment features

##  Command Flow

### Mobile App → Robot
1. User taps button in mobile app
2. App sends command via WebSocket
3. Robot control system processes command
4. Appropriate action is executed
5. Status feedback is sent back to app

### Voice → Robot
1. User speaks command to voice assistant
2. Voice assistant processes speech
3. Command is mapped to robot function
4. Command is sent via WebSocket
5. Robot executes action
6. Confirmation is provided via voice

### Direct Control → Robot
1. Command is sent directly via WebSocket
2. Robot control system processes command
3. Action is executed immediately
4. Status is logged to console

##  Safety Considerations

### Emergency Commands
- **Emergency Stop**: Immediately halts all movement and systems
- **Safety Override**: Bypasses normal safety checks in emergency situations

### Safety Systems
- **Spatial Awareness**: Prevents collision with obstacles
- **Edge Detection**: Prevents falling off surfaces
- **Battery Monitoring**: Automatic docking when battery is low
- **System Health**: Continuous monitoring of all subsystems

### Command Validation
- All commands are validated before execution
- Invalid commands are logged and ignored
- Safety checks are performed before any movement
- Emergency stop can override any other command

##  Command Status Codes

### Success Codes
- `200` - Command executed successfully
- `201` - Command queued for execution
- `202` - Command accepted, processing

### Error Codes
- `400` - Invalid command format
- `401` - Command not authorized
- `403` - Safety check failed
- `404` - Command not found
- `500` - Internal system error

### Warning Codes
- `300` - Command executed with warnings
- `301` - Low battery warning
- `302` - Obstacle detected
- `303` - System calibration needed

##  Advanced Usage

### Custom Commands
The system supports custom commands with parameters:
```python
robot_connection.sendCustomCommand("custom_action", {
    "parameter1": "value1",
    "parameter2": 123
})
```

### Command Chaining
Multiple commands can be chained for complex behaviors:
```python
# Dance sequence
robot_connection.sendCommand("dance")
time.sleep(5)
robot_connection.sendCommand("wave")
time.sleep(2)
robot_connection.sendCommand("stop")
```

### Batch Commands
Send multiple commands at once:
```python
commands = ["find_face", "dance", "dock"]
for cmd in commands:
    robot_connection.sendCommand(cmd)
    time.sleep(1)
```

##  Implementation Notes

### WebSocket Protocol
- Commands are sent as UTF-8 encoded strings
- Responses are sent back as JSON objects
- Connection is maintained with heartbeat messages
- Automatic reconnection on connection loss

### Error Handling
- All commands include error handling
- Failed commands are logged with error details
- Automatic retry for transient failures
- Graceful degradation when systems are unavailable

### Performance
- Commands are processed in real-time
- Response time is typically <100ms
- Batch commands are optimized for efficiency
- System resources are monitored and managed

This command reference provides complete coverage of all available commands and their usage patterns in the Poppy robot system.
