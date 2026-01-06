#!/bin/bash

# Poppy ROS2 Workspace Initialization Script
# This script sets up the complete ROS2 workspace structure

set -e

echo "====================================="
echo "  Poppy ROS2 Workspace Setup"
echo "====================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROS2_WS="${PROJECT_ROOT}/ros2_ws"

echo -e "${BLUE}Project root: ${PROJECT_ROOT}${NC}"

# Create ROS2 workspace structure
echo -e "\n${GREEN}[1/5] Creating ROS2 workspace structure...${NC}"
mkdir -p "${ROS2_WS}/src"
mkdir -p "${ROS2_WS}/build"
mkdir -p "${ROS2_WS}/install"
mkdir -p "${ROS2_WS}/log"

# Create ROS2 packages
echo -e "\n${GREEN}[2/5] Creating ROS2 packages...${NC}"

cd "${ROS2_WS}/src"

# Package 1: poppy_interfaces (messages, services, actions)
echo "  - Creating poppy_interfaces (C++/ament_cmake)"
ros2 pkg create --build-type ament_cmake poppy_interfaces \
    --dependencies rosidl_default_generators

# Package 2: poppy_core (Python)
echo "  - Creating poppy_core (Python)"
ros2 pkg create --build-type ament_python poppy_core \
    --dependencies rclpy std_msgs sensor_msgs geometry_msgs

# Package 3: poppy_hardware (Python)
echo "  - Creating poppy_hardware (Python)"
ros2 pkg create --build-type ament_python poppy_hardware \
    --dependencies rclpy serial

# Package 4: poppy_navigation (Python)
echo "  - Creating poppy_navigation (Python)"
ros2 pkg create --build-type ament_python poppy_navigation \
    --dependencies rclpy geometry_msgs nav_msgs tf2_ros

# Package 5: poppy_vision (Python)
echo "  - Creating poppy_vision (Python)"
ros2 pkg create --build-type ament_python poppy_vision \
    --dependencies rclpy sensor_msgs cv_bridge

# Package 6: poppy_voice (Python)
echo "  - Creating poppy_voice (Python)"
ros2 pkg create --build-type ament_python poppy_voice \
    --dependencies rclpy std_msgs audio_common_msgs

# Package 7: poppy_sdk_server (Python)
echo "  - Creating poppy_sdk_server (Python)"
ros2 pkg create --build-type ament_python poppy_sdk_server \
    --dependencies rclpy

# Package 8: poppy_bringup (Python - launch files only)
echo "  - Creating poppy_bringup (Python)"
ros2 pkg create --build-type ament_python poppy_bringup \
    --dependencies rclpy

# Create additional directories
echo -e "\n${GREEN}[3/5] Creating additional project directories...${NC}"
mkdir -p "${PROJECT_ROOT}/firmware/motor_control"
mkdir -p "${PROJECT_ROOT}/firmware/sensor_drivers"
mkdir -p "${PROJECT_ROOT}/firmware/communication"

mkdir -p "${PROJECT_ROOT}/sdk/poppy_sdk"
mkdir -p "${PROJECT_ROOT}/sdk/examples"

mkdir -p "${PROJECT_ROOT}/dashboard/src"
mkdir -p "${PROJECT_ROOT}/dashboard/public"

mkdir -p "${PROJECT_ROOT}/docker"
mkdir -p "${PROJECT_ROOT}/docs"
mkdir -p "${PROJECT_ROOT}/tools/scripts"
mkdir -p "${PROJECT_ROOT}/tools/calibration"

mkdir -p "${PROJECT_ROOT}/.github/workflows"

# Create configuration files
echo -e "\n${GREEN}[4/5] Creating configuration files...${NC}"

# Create .gitignore
cat > "${PROJECT_ROOT}/.gitignore" << 'EOF'
# ROS2
ros2_ws/build/
ros2_ws/install/
ros2_ws/log/
*.pyc
__pycache__/

# Python
*.egg-info/
dist/
*.so
.Python
venv/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# Firmware
firmware/**/.pio
firmware/**/platformio.ini.backup

# Node
dashboard/node_modules/
dashboard/build/

# Docker
*.log

# Secrets
.env
secrets/
*.pem
*.key
EOF

# Create Docker Compose
cat > "${PROJECT_ROOT}/docker-compose.yml" << 'EOF'
version: '3.8'

services:
  mqtt_broker:
    image: eclipse-mosquitto:2
    ports:
      - "1883:1883"
      - "9001:9001"
    volumes:
      - ./docker/mosquitto/config:/mosquitto/config
      - mqtt_data:/mosquitto/data
      - mqtt_logs:/mosquitto/log

  dashboard:
    build:
      context: ./dashboard
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_MQTT_BROKER=ws://localhost:9001
      - REACT_APP_API_URL=http://localhost:8000
    depends_on:
      - mqtt_broker

  influxdb:
    image: influxdb:2.7
    ports:
      - "8086:8086"
    volumes:
      - influx_data:/var/lib/influxdb2
    environment:
      - DOCKER_INFLUXDB_INIT_MODE=setup
      - DOCKER_INFLUXDB_INIT_USERNAME=admin
      - DOCKER_INFLUXDB_INIT_PASSWORD=poppyadmin2024
      - DOCKER_INFLUXDB_INIT_ORG=poppy
      - DOCKER_INFLUXDB_INIT_BUCKET=telemetry

volumes:
  mqtt_data:
  mqtt_logs:
  influx_data:
EOF

echo -e "\n${GREEN}[5/5] Building workspace...${NC}"
cd "${ROS2_WS}"
colcon build --symlink-install

echo -e "\n${GREEN}================================================${NC}"
echo -e "${GREEN}  [OK] ROS2 workspace initialized successfully!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Source the workspace: source ${ROS2_WS}/install/setup.bash"
echo "  2. Start implementing nodes in ros2_ws/src/"
echo "  3. Build with: cd ${ROS2_WS} && colcon build"
echo ""
