#!/usr/bin/env python3
"""
Poppy Robot - I2C Communication System
Communication between Raspberry Pi and Arduino for motor control
"""

import smbus
import time
import threading
import logging
import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CommandType(Enum):
    MOVE = "MOVE"
    STOP = "STOP"
    EMERGENCY = "EMERGENCY"
    RESET = "RESET"
    PID_TUNE = "PID_TUNE"
    STATUS_REQUEST = "STATUS_REQUEST"

@dataclass
class MotorCommand:
    command_type: CommandType
    left_speed: float = 0.0
    right_speed: float = 0.0
    kp: float = 0.0
    ki: float = 0.0
    kd: float = 0.0

@dataclass
class ArduinoStatus:
    left_speed: float
    right_speed: float
    battery_voltage: float
    emergency_stop: bool
    timestamp: float

class I2CCommunication:
    def __init__(self, i2c_bus=1, arduino_address=0x08):
        self.i2c_bus = i2c_bus
        self.arduino_address = arduino_address
        self.bus = smbus.SMBus(i2c_bus)
        
        # Communication state
        self.is_connected = False
        self.last_status = None
        self.status_callbacks = []
        
        # Command queue
        self.command_queue = []
        self.command_lock = threading.Lock()
        
        # Status monitoring
        self.status_thread = None
        self.is_monitoring = False
        
        # Initialize communication
        self.init_communication()
    
    def init_communication(self):
        """Initialize I2C communication with Arduino"""
        try:
            # Test communication by reading a byte
            self.bus.read_byte(self.arduino_address)
            self.is_connected = True
            logger.info(f"✓ I2C communication established with Arduino at address 0x{self.arduino_address:02X}")
        except Exception as e:
            logger.error(f"Failed to initialize I2C communication: {e}")
            self.is_connected = False
    
    def send_command(self, command: MotorCommand):
        """Send command to Arduino via I2C"""
        if not self.is_connected:
            logger.warning("Not connected to Arduino, cannot send command")
            return False
        
        try:
            with self.command_lock:
                self.command_queue.append(command)
            
            # Process command immediately
            self._process_command(command)
            return True
            
        except Exception as e:
            logger.error(f"Failed to send command: {e}")
            return False
    
    def _process_command(self, command: MotorCommand):
        """Process a single command"""
        try:
            if command.command_type == CommandType.MOVE:
                self._send_move_command(command)
            elif command.command_type == CommandType.STOP:
                self._send_stop_command()
            elif command.command_type == CommandType.EMERGENCY:
                self._send_emergency_command()
            elif command.command_type == CommandType.RESET:
                self._send_reset_command()
            elif command.command_type == CommandType.PID_TUNE:
                self._send_pid_tune_command(command)
            elif command.command_type == CommandType.STATUS_REQUEST:
                self._request_status()
                
        except Exception as e:
            logger.error(f"Failed to process command {command.command_type}: {e}")
    
    def _send_move_command(self, command: MotorCommand):
        """Send movement command to Arduino"""
        # Convert speeds to Arduino format (-255 to 255)
        left_speed = int(max(-255, min(255, command.left_speed * 255)))
        right_speed = int(max(-255, min(255, command.right_speed * 255)))
        
        # Send command: MOVE,left_speed,right_speed
        command_str = f"MOVE,{left_speed},{right_speed}"
        self._send_string(command_str)
        logger.info(f"Sent move command: {command_str}")
    
    def _send_stop_command(self):
        """Send stop command to Arduino"""
        self._send_string("STOP")
        logger.info("Sent stop command")
    
    def _send_emergency_command(self):
        """Send emergency stop command to Arduino"""
        self._send_string("EMERGENCY")
        logger.info("Sent emergency stop command")
    
    def _send_reset_command(self):
        """Send reset command to Arduino"""
        self._send_string("RESET")
        logger.info("Sent reset command")
    
    def _send_pid_tune_command(self, command: MotorCommand):
        """Send PID tuning command to Arduino"""
        command_str = f"PID_TUNE,{command.kp},{command.ki},{command.kd}"
        self._send_string(command_str)
        logger.info(f"Sent PID tune command: {command_str}")
    
    def _request_status(self):
        """Request status from Arduino"""
        try:
            # Request status data
            data = self.bus.read_i2c_block_data(self.arduino_address, 0x00, 16)
            
            # Parse status data (simplified parsing)
            if len(data) >= 16:
                left_speed = (data[0] << 8 | data[1]) / 1000.0
                right_speed = (data[2] << 8 | data[3]) / 1000.0
                battery_voltage = (data[4] << 8 | data[5]) / 1000.0
                emergency_stop = bool(data[6])
                
                status = ArduinoStatus(
                    left_speed=left_speed,
                    right_speed=right_speed,
                    battery_voltage=battery_voltage,
                    emergency_stop=emergency_stop,
                    timestamp=time.time()
                )
                
                self.last_status = status
                self._notify_status_callbacks(status)
                
        except Exception as e:
            logger.error(f"Failed to request status: {e}")
    
    def _send_string(self, message: str):
        """Send string message to Arduino"""
        try:
            # Convert string to bytes
            message_bytes = message.encode('utf-8')
            
            # Send length first
            self.bus.write_byte(self.arduino_address, len(message_bytes))
            time.sleep(0.01)  # Small delay
            
            # Send message
            for byte in message_bytes:
                self.bus.write_byte(self.arduino_address, byte)
                time.sleep(0.001)  # Small delay between bytes
            
        except Exception as e:
            logger.error(f"Failed to send string '{message}': {e}")
            raise
    
    def add_status_callback(self, callback: Callable[[ArduinoStatus], None]):
        """Add callback for status updates"""
        self.status_callbacks.append(callback)
    
    def _notify_status_callbacks(self, status: ArduinoStatus):
        """Notify all status callbacks"""
        for callback in self.status_callbacks:
            try:
                callback(status)
            except Exception as e:
                logger.error(f"Status callback error: {e}")
    
    def start_status_monitoring(self, interval=1.0):
        """Start continuous status monitoring"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.status_thread = threading.Thread(target=self._status_monitoring_loop, args=(interval,))
        self.status_thread.daemon = True
        self.status_thread.start()
        logger.info("Status monitoring started")
    
    def stop_status_monitoring(self):
        """Stop status monitoring"""
        self.is_monitoring = False
        if self.status_thread:
            self.status_thread.join()
        logger.info("Status monitoring stopped")
    
    def _status_monitoring_loop(self, interval):
        """Status monitoring loop"""
        while self.is_monitoring:
            try:
                self._request_status()
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Status monitoring error: {e}")
                time.sleep(5)
    
    def move_motors(self, left_speed: float, right_speed: float):
        """Move motors with specified speeds"""
        command = MotorCommand(
            command_type=CommandType.MOVE,
            left_speed=left_speed,
            right_speed=right_speed
        )
        return self.send_command(command)
    
    def stop_motors(self):
        """Stop all motors"""
        command = MotorCommand(command_type=CommandType.STOP)
        return self.send_command(command)
    
    def emergency_stop(self):
        """Emergency stop all motors"""
        command = MotorCommand(command_type=CommandType.EMERGENCY)
        return self.send_command(command)
    
    def reset_system(self):
        """Reset Arduino system"""
        command = MotorCommand(command_type=CommandType.RESET)
        return self.send_command(command)
    
    def tune_pid(self, kp: float, ki: float, kd: float):
        """Tune PID parameters"""
        command = MotorCommand(
            command_type=CommandType.PID_TUNE,
            kp=kp,
            ki=ki,
            kd=kd
        )
        return self.send_command(command)
    
    def get_status(self) -> Optional[ArduinoStatus]:
        """Get last received status"""
        return self.last_status
    
    def is_arduino_connected(self) -> bool:
        """Check if Arduino is connected"""
        return self.is_connected
    
    def get_connection_status(self) -> Dict:
        """Get connection status information"""
        return {
            'connected': self.is_connected,
            'arduino_address': f"0x{self.arduino_address:02X}",
            'i2c_bus': self.i2c_bus,
            'monitoring': self.is_monitoring,
            'last_status': self.last_status.timestamp if self.last_status else None
        }

# Example usage and testing
if __name__ == "__main__":
    try:
        # Initialize I2C communication
        i2c = I2CCommunication()
        
        # Add status callback
        def status_callback(status: ArduinoStatus):
            print(f"Status: L={status.left_speed:.2f}, R={status.right_speed:.2f}, "
                  f"Battery={status.battery_voltage:.2f}V, Emergency={status.emergency_stop}")
        
        i2c.add_status_callback(status_callback)
        
        # Start status monitoring
        i2c.start_status_monitoring(interval=1.0)
        
        # Test commands
        print("Testing motor commands...")
        
        # Move forward
        i2c.move_motors(0.5, 0.5)
        time.sleep(2)
        
        # Turn left
        i2c.move_motors(-0.3, 0.3)
        time.sleep(2)
        
        # Stop
        i2c.stop_motors()
        time.sleep(1)
        
        # Test PID tuning
        i2c.tune_pid(2.0, 5.0, 1.0)
        time.sleep(1)
        
        # Stop monitoring
        i2c.stop_status_monitoring()
        
    except KeyboardInterrupt:
        print("I2C communication test stopped by user")
    except Exception as e:
        print(f"I2C communication test error: {e}")
