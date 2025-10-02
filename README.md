# Poppy

## What is Poppy?
Poppy is an interactive, educational, and intelligent robot that is able to communicate with users through physical movements and vocal speeches. Our vision is to make today’s smart home systems more interactive and more lively. Instead of having your home assistant like Google Home be fixed in one place, we envision a future where your assistant is able to approach you physically and interact with you with an uniquely natural manner. Poppy will be a palm-sized robot that lives on any surfaces in your home. You will have the option to either use Google Assistant as the answering engine of Poppy. You can talk to Poppy by simply saying “Hey Poppy”, then Poppy will look around 360 degrees to determine your location and approaches you. Poppy is able to effectively walk around obstacles and terminate movement upon approach an edge on the surface. In addition, we also plan to make Poppy educational by allowing users to send movement commands to Poppy to see their code run in action (quite literally!). 

## Main Features
* Remote control through Android and iOS apps
* Programmable and controllable through computer client
* Google Assistant and Amazon Alexa integration
* Advanced facial detection and tracking with Edge AI
* Self-balancing with adaptive PID control
* Spatial awareness and obstacle detection
* Self-docking and autonomous charging
* Real-time computer vision processing
* Multi-channel communication system
* Intelligent power management
* Voice control with unified command processing

## Major Software Components:

### Core System
* **Main System Controller** (`poppy_main.py`) - Central system coordinator with graceful shutdown
* **Communication Manager** (`communication_manager.py`) - Multi-channel communication system
* **System Integration** (`system_integration.py`) - Unified component integration and monitoring

### AI and Computer Vision
* **Advanced Face Detection** (`advanced_face_detection.py`) - Edge AI-powered facial recognition
* **Raspberry Pi Optimizer** (`raspberry_pi_optimizer.py`) - Real-time frame processing with TensorFlow Lite
* **Enhanced Vision Processing** - Multi-algorithm edge detection, motion tracking, lighting analysis

### Voice and Control
* **Google Assistant Integration** (`hotword.py`) - Voice activation and command processing
* **Amazon Alexa Integration** (`alexa_integration.py`) - Multi-platform voice control
* **Unified Voice Control** (`unified_voice_control.py`) - Centralized voice command management

### Hardware and Power Management
* **Power Management System** (`power_management.py`) - Intelligent BMS integration and power optimization
* **BMS Service** (`bms_service.py`) - Real battery management system integration
* **I2C Communication** (`i2c_communication.py`) - Arduino motor control and sensor communication
* **Motor Control** (`arduino/motor_control/`) - Real-time motor control with safety systems

### Control Systems
* **Adaptive PID Control** (`control/pid/`) - Neural network-enhanced PID with self-tuning
* **Spatial Awareness** (`control/spatial/`) - Multi-sensor obstacle detection and edge avoidance
* **Docking System** (`control/docking/`) - Autonomous charging and docking capabilities
* **IMU Integration** (`control/imu/`) - Advanced orientation and heading control

### User Interfaces
* **Java Client** (`src/main/java/`) - Cross-platform desktop application
* **Android App** (`androidapp/`) - Mobile control interface
* **3D Visualizer** (`visualizer/`) - Real-time robot monitoring and control

## Hardware Components:

### Core Computing
* **Raspberry Pi 4** - Main processing unit with GPU acceleration
* **Arduino Uno/Nano** - Real-time motor control and sensor interface
* **Camera Module** - High-resolution camera for computer vision
* **Microphone Array** - Multi-directional voice input
* **Speaker System** - Audio output for voice responses

### Motion and Control
* **2x High-torque Motors** - Precision movement control
* **2x Wheels** - Omni-directional movement capability
* **Dual H-bridge Motor Drivers** - Bidirectional motor control
* **IMU (Inertial Measurement Unit)** - 6-axis orientation sensing
* **Servo Motors** - Additional articulation capabilities

### Sensors and Awareness
* **Ultrasonic Proximity Sensors** (4x) - 360° obstacle detection
* **IR Sensors** (3x) - Docking station detection and alignment
* **Light Sensors** - Ambient lighting detection
* **Temperature Sensors** - System thermal monitoring
* **Battery Management System (BMS)** - Intelligent power monitoring

### Power and Charging
* **Lithium Battery Pack** - High-capacity rechargeable power source
* **Charging Station** - Autonomous docking and charging
* **Power Distribution System** - Smart power management
* **Voltage Regulators** - Stable power delivery to components

### Structure and Enclosure
* **3D Printed Chassis** - Lightweight, durable frame
* **Protective Housing** - Component protection and aesthetics
* **Modular Design** - Easy maintenance and upgrades

## Video DEMO
[![Poppy Video Demonstration](https://img.youtube.com/vi/w4yrwwst9eY/0.jpg)](https://www.youtube.com/embed/w4yrwwst9eY)

## Installation and Setup

### Prerequisites
* Python 3.8+
* OpenCV 4.8+
* TensorFlow Lite 2.10+
* Raspberry Pi OS
* Arduino IDE

### Quick Start
```bash
# Clone the repository
git clone https://github.com/MarkYHZhang/Poppy.git
cd poppy-robot

# Install Python dependencies
pip install -r python/requirements_2025.txt

# Start the main system
python3 python/poppy_main.py
```

### Configuration
1. **Hardware Setup**: Connect all sensors and motors according to the wiring diagram
2. **BMS Configuration**: Configure battery management system parameters
3. **Voice Assistant**: Set up Google Assistant and/or Amazon Alexa credentials
4. **Network**: Configure WebSocket and UDP communication settings

## Advanced Features

### AI and Machine Learning
* **Edge AI Processing**: Real-time inference on Raspberry Pi
* **Adaptive Learning**: Self-improving control algorithms
* **Multi-Modal Recognition**: Combined visual and audio processing
* **Predictive Analytics**: Anticipatory behavior based on user patterns

### Safety and Reliability
* **Emergency Systems**: Multi-channel emergency communication
* **Fault Tolerance**: Graceful degradation on component failure
* **Power Management**: Intelligent battery monitoring and conservation
* **Thermal Management**: Active cooling and performance throttling

### Communication
* **Multi-Protocol Support**: WebSocket, I2C, UDP, and file-based communication
* **Message Routing**: Priority-based message handling with retry logic
* **Real-time Updates**: Live system status and performance monitoring
* **Remote Control**: Secure remote access and control capabilities

## Development Status

### Completed Features
- [x] Spatial awareness with multi-sensor obstacle detection
- [x] Amazon Alexa integration
- [x] iOS app development
- [x] Self-docking and autonomous charging
- [x] Advanced computer vision processing
- [x] Adaptive PID control with neural networks
- [x] Multi-channel communication system
- [x] Intelligent power management
- [x] Real-time performance optimization
- [x] Professional codebase with comprehensive error handling

### In Progress
- [ ] Enhanced machine learning models
- [ ] Advanced user interface improvements
- [ ] Extended sensor integration
- [ ] Performance optimization

### Future Roadmap
- [ ] Swarm robotics capabilities
- [ ] Advanced AI personality system
- [ ] Cloud integration and analytics
- [ ] Extended battery life optimization
- [ ] Advanced security features
