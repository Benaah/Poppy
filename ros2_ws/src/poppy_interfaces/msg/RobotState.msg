# RobotState.msg
# Complete state information for the Poppy robot

# Header
std_msgs/Header header

# Position and orientation
geometry_msgs/Pose2D pose
geometry_msgs/Twist velocity

# Locomotion mode
uint8 MODE_TRACK = 0
uint8 MODE_LEG = 1
uint8 MODE_HYBRID = 2
uint8 locomotion_mode

# Battery status
float32 battery_voltage      # Volts
float32 battery_percentage   # 0-100
bool charging

# Sensor health
bool[] sensor_status  # [front_tof, left_tof, right_tof, cliff_left, cliff_right, imu]

# System status
bool emergency_stop_active
bool user_tracking_active
bool voice_assistant_ready

# Current activity
string current_activity  # "idle", "navigating", "tracking_user", "listening", etc.
