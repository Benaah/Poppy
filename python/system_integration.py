#!/usr/bin/env python3
"""
Poppy Robot - System Integration
Unified system that integrates all hardware solutions for 2025 challenges
"""

import time
import threading
import logging
import json
from typing import Dict, List, Optional
from dataclasses import dataclass

# Import all system components
from advanced_face_detection import AdvancedFaceDetection
from power_management import SmartPowerManager, PowerMode
from raspberry_pi_optimizer import RaspberryPiOptimizer
from i2c_communication import I2CCommunication, MotorCommand, CommandType
from unified_voice_control import UnifiedVoiceControl
from communication_manager import get_communication_manager, MessageType, Message

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SystemStatus:
    face_detection_active: bool
    power_mode: str
    battery_percentage: float
    arduino_connected: bool
    motor_speeds: Dict[str, float]
    lighting_mode: str
    system_performance: Dict[str, float]
    timestamp: float

class PoppySystemIntegration:
    def __init__(self):
        # Initialize all system components
        self.face_detection = AdvancedFaceDetection()
        self.power_manager = SmartPowerManager()
        self.pi_optimizer = RaspberryPiOptimizer()
        self.i2c_comm = I2CCommunication()
        self.voice_control = UnifiedVoiceControl()
        
        # Initialize communication manager
        self.comm_manager = get_communication_manager()
        self._setup_communication_handlers()
        
        # System state
        self.is_running = False
        self.system_status = None
        self.monitoring_thread = None
        
        # Performance tracking
        self.performance_history = []
        
        # Initialize all systems
        self.initialize_systems()
    
    def _setup_communication_handlers(self):
        """Setup communication message handlers"""
        # Subscribe to emergency messages
        self.comm_manager.subscribe(MessageType.EMERGENCY, self._handle_emergency_message)
        
        # Subscribe to status updates
        self.comm_manager.subscribe(MessageType.STATUS_UPDATE, self._handle_status_message)
        
        # Subscribe to commands
        self.comm_manager.subscribe(MessageType.COMMAND, self._handle_command_message)
        
        # Subscribe to battery alerts
        self.comm_manager.subscribe(MessageType.BATTERY_ALERT, self._handle_battery_alert)
        
        logger.info("Communication handlers setup complete")
    
    def _handle_emergency_message(self, message: Message):
        """Handle emergency messages"""
        try:
            logger.critical(f"EMERGENCY MESSAGE RECEIVED from {message.source}")
            logger.critical(f"Emergency data: {message.data}")
            
            # Immediate system shutdown
            if message.data.get("action") == "immediate_shutdown":
                self._emergency_shutdown()
            
            # Update system status
            self.system_status.emergency = True
            
        except Exception as e:
            logger.error(f"Failed to handle emergency message: {e}")
    
    def _handle_status_message(self, message: Message):
        """Handle status update messages"""
        try:
            logger.debug(f"Status update from {message.source}: {message.data}")
            
            # Update system status based on source
            if message.source == "power_management":
                self._update_power_status(message.data)
            elif message.source == "face_detection":
                self._update_face_detection_status(message.data)
            elif message.source == "raspberry_pi_optimizer":
                self._update_performance_status(message.data)
            
        except Exception as e:
            logger.error(f"Failed to handle status message: {e}")
    
    def _handle_command_message(self, message: Message):
        """Handle command messages"""
        try:
            logger.info(f"Command received from {message.source}: {message.data}")
            
            command = message.data.get("command")
            if command == "start_face_detection":
                self.start_face_detection()
            elif command == "stop_face_detection":
                self.stop_face_detection()
            elif command == "emergency_stop":
                self._emergency_shutdown()
            elif command == "system_restart":
                self.restart_system()
            
        except Exception as e:
            logger.error(f"Failed to handle command message: {e}")
    
    def _handle_battery_alert(self, message: Message):
        """Handle battery alert messages"""
        try:
            alert_type = message.data.get("alert_type")
            current_value = message.data.get("current_value")
            recommended_action = message.data.get("recommended_action")
            
            logger.warning(f"Battery alert: {alert_type} - {current_value}% - {recommended_action}")
            
            # Take appropriate action based on alert type
            if alert_type == "critical_battery":
                self._initiate_docking_sequence()
            elif alert_type == "low_battery":
                self._reduce_power_consumption()
            
        except Exception as e:
            logger.error(f"Failed to handle battery alert: {e}")
    
    def _emergency_shutdown(self):
        """Perform emergency system shutdown"""
        try:
            logger.critical("INITIATING EMERGENCY SHUTDOWN")
            
            # Stop all motors immediately
            self.i2c_comm.send_command(MotorCommand(
                command_type=CommandType.EMERGENCY_STOP,
                motor_id=0,
                value=0.0,
                priority=1
            ))
            
            # Disable all non-essential components
            self.power_manager.emergency_shutdown()
            
            # Stop all processing
            self.pi_optimizer.stop_monitoring()
            self.face_detection.stop_detection()
            
            # Set system status
            self.system_status.emergency = True
            
            logger.critical("EMERGENCY SHUTDOWN COMPLETE")
            
        except Exception as e:
            logger.error(f"Emergency shutdown failed: {e}")
    
    def _initiate_docking_sequence(self):
        """Initiate automatic docking sequence"""
        try:
            logger.info("Initiating docking sequence due to low battery")
            
            # Send docking command
            self.comm_manager.send_command(
                source="system_integration",
                destination="docking_system",
                command_data={"action": "start_docking", "reason": "low_battery"}
            )
            
        except Exception as e:
            logger.error(f"Failed to initiate docking sequence: {e}")
    
    def _reduce_power_consumption(self):
        """Reduce power consumption for low battery"""
        try:
            logger.info("Reducing power consumption due to low battery")
            
            # Disable non-essential components
            self.power_manager.disable_component("camera")
            self.power_manager.disable_component("speakers")
            self.power_manager.disable_component("leds")
            
            # Reduce processing frequency
            self.pi_optimizer.throttle_performance()
            
        except Exception as e:
            logger.error(f"Failed to reduce power consumption: {e}")
    
    def initialize_systems(self):
        """Initialize all system components"""
        try:
            logger.info("Initializing Poppy Robot System...")
            
            # Start power management
            self.power_manager.start_monitoring()
            logger.info("[OK] Power management started")
            
            # Start Raspberry Pi optimization
            self.pi_optimizer.start_monitoring()
            logger.info("[OK] Raspberry Pi optimization started")
            
            # Start I2C communication
            self.i2c_comm.start_status_monitoring()
            logger.info("[OK] I2C communication started")
            
            # Initialize voice control
            self.voice_control.initialize()
            logger.info("[OK] Voice control initialized")
            
            logger.info("[OK] All systems initialized successfully")
            
        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            raise
    
    def start_system(self):
        """Start the complete system"""
        if self.is_running:
            logger.warning("System is already running")
            return
        
        self.is_running = True
        self.monitoring_thread = threading.Thread(target=self._system_monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        logger.info(" Poppy Robot System started")
    
    def stop_system(self):
        """Stop the complete system"""
        self.is_running = False
        
        if self.monitoring_thread:
            self.monitoring_thread.join()
        
        # Stop all subsystems
        self.power_manager.stop_monitoring()
        self.pi_optimizer.stop_monitoring()
        self.i2c_comm.stop_status_monitoring()
        self.face_detection.cleanup()
        self.pi_optimizer.cleanup()
        
        logger.info(" Poppy Robot System stopped")
    
    def _system_monitoring_loop(self):
        """Main system monitoring loop"""
        while self.is_running:
            try:
                # Update system status
                self._update_system_status()
                
                # Check for emergency conditions
                self._check_emergency_conditions()
                
                # Optimize system performance
                self._optimize_system_performance()
                
                # Log system status
                self._log_system_status()
                
                time.sleep(1)  # Monitor every second
                
            except Exception as e:
                logger.error(f"System monitoring error: {e}")
                time.sleep(5)
    
    def _update_system_status(self):
        """Update current system status"""
        try:
            # Get power status
            power_status = self.power_manager.get_power_status()
            
            # Get Arduino status
            arduino_status = self.i2c_comm.get_status()
            
            # Get face detection stats
            face_stats = self.face_detection.get_detection_stats()
            
            # Get Raspberry Pi performance
            pi_performance = self.pi_optimizer.get_performance_summary()
            
            # Create system status
            self.system_status = SystemStatus(
                face_detection_active=face_stats['is_running'] if face_stats else False,
                power_mode=power_status['power_mode'],
                battery_percentage=power_status['battery']['charge_percentage'],
                arduino_connected=self.i2c_comm.is_arduino_connected(),
                motor_speeds={
                    'left': arduino_status.left_speed if arduino_status else 0.0,
                    'right': arduino_status.right_speed if arduino_status else 0.0
                },
                lighting_mode=face_stats['lighting_mode'] if face_stats else 'UNKNOWN',
                system_performance=pi_performance if pi_performance else {},
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"Failed to update system status: {e}")
    
    def _check_emergency_conditions(self):
        """Check for emergency conditions and respond"""
        if not self.system_status:
            return
        
        # Check battery level
        if self.system_status.battery_percentage < 10:
            logger.warning(" Low battery - initiating emergency shutdown")
            self.emergency_shutdown()
            return
        
        # Check Arduino emergency stop
        arduino_status = self.i2c_comm.get_status()
        if arduino_status and arduino_status.emergency_stop:
            logger.warning(" Arduino emergency stop activated")
            self.handle_emergency_stop()
            return
        
        # Check system performance
        if self.system_status.system_performance:
            cpu_usage = self.system_status.system_performance.get('cpu_usage_avg', 0)
            memory_usage = self.system_status.system_performance.get('memory_usage_avg', 0)
            
            if cpu_usage > 90 or memory_usage > 90:
                logger.warning(" High system resource usage detected")
                self.optimize_performance()
    
    def _optimize_system_performance(self):
        """Optimize system performance based on current conditions"""
        if not self.system_status:
            return
        
        # Optimize based on power mode
        if self.system_status.power_mode == "LOW_POWER":
            # Disable non-essential features
            self.power_manager.disable_component('leds')
            self.power_manager.disable_component('speaker')
        elif self.system_status.power_mode == "HIGH":
            # Enable all features
            self.power_manager.enable_component('leds')
            self.power_manager.enable_component('speaker')
        
        # Optimize based on lighting conditions
        if self.system_status.lighting_mode == "DARK":
            # Adjust face detection parameters for dark conditions
            pass  # This would be handled by the face detection system
        elif self.system_status.lighting_mode == "BRIGHT":
            # Adjust for bright conditions
            pass
    
    def _log_system_status(self):
        """Log current system status"""
        if not self.system_status:
            return
        
        logger.info(f"System Status - Power: {self.system_status.power_mode} "
                   f"({self.system_status.battery_percentage:.1f}%), "
                   f"Arduino: {'Connected' if self.system_status.arduino_connected else 'Disconnected'}, "
                   f"Lighting: {self.system_status.lighting_mode}, "
                   f"Motors: L={self.system_status.motor_speeds['left']:.2f}, "
                   f"R={self.system_status.motor_speeds['right']:.2f}")
    
    def emergency_shutdown(self):
        """Emergency shutdown sequence"""
        logger.critical(" EMERGENCY SHUTDOWN INITIATED")
        
        # Stop all motors immediately
        self.i2c_comm.emergency_stop()
        
        # Set power to emergency mode
        self.power_manager.emergency_shutdown()
        
        # Stop face detection
        self.face_detection.cleanup()
        
        logger.critical(" EMERGENCY SHUTDOWN COMPLETE")
    
    def handle_emergency_stop(self):
        """Handle Arduino emergency stop"""
        logger.warning("Handling Arduino emergency stop")
        
        # Stop all movement
        self.i2c_comm.stop_motors()
        
        # Wait for manual reset
        time.sleep(5)
        
        # Reset Arduino
        self.i2c_comm.reset_system()
    
    def optimize_performance(self):
        """Optimize system performance"""
        logger.info("Optimizing system performance...")
        
        # The individual components handle their own optimization
        # This is a high-level coordination function
        pass
    
    def move_robot(self, left_speed: float, right_speed: float):
        """Move robot with specified speeds"""
        if not self.i2c_comm.is_arduino_connected():
            logger.warning("Arduino not connected, cannot move robot")
            return False
        
        return self.i2c_comm.move_motors(left_speed, right_speed)
    
    def stop_robot(self):
        """Stop robot movement"""
        return self.i2c_comm.stop_motors()
    
    def find_face(self):
        """Start face detection and tracking"""
        try:
            detection_thread = self.face_detection.start_detection()
            return detection_thread
        except Exception as e:
            logger.error(f"Failed to start face detection: {e}")
            return None
    
    def get_system_status(self) -> Optional[SystemStatus]:
        """Get current system status"""
        return self.system_status
    
    def export_system_data(self, filename: str):
        """Export system data to JSON file"""
        try:
            data = {
                'system_status': {
                    'face_detection_active': self.system_status.face_detection_active,
                    'power_mode': self.system_status.power_mode,
                    'battery_percentage': self.system_status.battery_percentage,
                    'arduino_connected': self.system_status.arduino_connected,
                    'motor_speeds': self.system_status.motor_speeds,
                    'lighting_mode': self.system_status.lighting_mode,
                    'system_performance': self.system_status.system_performance,
                    'timestamp': self.system_status.timestamp
                },
                'power_data': self.power_manager.get_power_status(),
                'performance_data': self.pi_optimizer.get_performance_summary(),
                'export_time': time.time()
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"System data exported to {filename}")
        except Exception as e:
            logger.error(f"Failed to export system data: {e}")

# Example usage
if __name__ == "__main__":
    try:
        # Initialize and start the complete system
        poppy_system = PoppySystemIntegration()
        poppy_system.start_system()
        
        # Run for 60 seconds
        time.sleep(60)
        
        # Export data
        poppy_system.export_system_data("poppy_system_data.json")
        
        # Stop system
        poppy_system.stop_system()
        
    except KeyboardInterrupt:
        logger.info("Poppy system stopped by user")
    except Exception as e:
        logger.error(f"Poppy system error: {e}")
