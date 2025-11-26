# MovementCommand.msg
# Command for robot movement

std_msgs/Header header

# Movement type
uint8 TYPE_FORWARD = 0
uint8 TYPE_BACKWARD = 1
uint8 TYPE_TURN_LEFT = 2
uint8 TYPE_TURN_RIGHT = 3
uint8 TYPE_STOP = 4
uint8 TYPE_TRANSFORM = 5  # Switch locomotion mode
uint8 command_type

# Parameters
float32 distance_cm        # For linear movement
float32 angle_degrees      # For rotational movement
float32 speed_percent      # 0-100, speed as percentage of max

# Mode specification (for TYPE_TRANSFORM)
uint8 target_mode  # MODE_TRACK, MODE_LEG, or MODE_HYBRID

# Priority
bool is_emergency  # Emergency commands bypass queue
