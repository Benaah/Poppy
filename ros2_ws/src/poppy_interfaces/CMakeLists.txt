cmake_minimum_required(VERSION 3.8)
project(poppy_interfaces)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)

# Declare message files
set(msg_files
  "msg/RobotState.msg"
  "msg/MovementCommand.msg"
  "msg/UserTracking.msg"
  "msg/VoiceCommand.msg"
  "msg/SensorData.msg"
)

# Declare service files
set(srv_files
  "srv/SetMode.srv"
  "srv/ExecuteSequence.srv"
  "srv/EmergencyStop.srv"
)

# Declare action files
set(action_files
  "action/NavigateToGoal.action"
  "action/TrackUser.action"
)

# Generate interfaces
rosidl_generate_interfaces(${PROJECT_NAME}
  ${msg_files}
  ${srv_files}
  ${action_files}
  DEPENDENCIES std_msgs geometry_msgs sensor_msgs
)

ament_package()
