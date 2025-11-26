# UserTracking.msg
# User detection and tracking information

std_msgs/Header header

# Detection status
bool user_detected
float32 confidence  # 0.0-1.0

# User position (camera frame)
geometry_msgs/Point position_camera_frame  # x, y, z in meters

# User position (robot base frame)
geometry_msgs/Point position_base_frame

# Bounding box (normalized 0-1)
float32 bbox_x
float32 bbox_y
float32 bbox_width
float32 bbox_height

# Tracking quality
uint8 QUALITY_LOST = 0
uint8 QUALITY_LOW = 1
uint8 QUALITY_GOOD = 2
uint8 QUALITY_EXCELLENT = 3
uint8 tracking_quality

# Distance and angle to user
float32 distance_meters
float32 angle_degrees  # Relative to robot's forward direction

#Velocity (if available)
geometry_msgs/Vector3 velocity  # User's movement velocity
