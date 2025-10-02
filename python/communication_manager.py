#!/usr/bin/env python3
"""
Poppy Robot - Communication Manager
Centralized communication system for all robot components
"""

import time
import threading
import logging
import json
import queue
import socket
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
import websocket
from websocket import create_connection
import smbus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageType(Enum):
    EMERGENCY = "emergency"
    STATUS_UPDATE = "status_update"
    COMMAND = "command"
    SENSOR_DATA = "sensor_data"
    BATTERY_ALERT = "battery_alert"
    MOTOR_CONTROL = "motor_control"
    SYSTEM_SHUTDOWN = "system_shutdown"
    HEARTBEAT = "heartbeat"

class CommunicationChannel(Enum):
    WEBSOCKET = "websocket"
    I2C = "i2c"
    UDP = "udp"
    FILE = "file"
    PIPE = "pipe"

@dataclass
class Message:
    message_type: MessageType
    source: str
    destination: str
    data: Dict[str, Any]
    timestamp: float
    priority: int = 0  # 0 = normal, 1 = high, 2 = critical
    channel: CommunicationChannel = CommunicationChannel.WEBSOCKET
    retry_count: int = 0
    max_retries: int = 3

class CommunicationManager:
    """Centralized communication manager for all robot components"""
    
    def __init__(self):
        self.is_running = False
        self.message_queue = queue.PriorityQueue()
        self.subscribers = {}  # message_type -> list of callbacks
        self.channels = {}
        self.message_history = []
        self.max_history = 1000
        
        # Initialize communication channels
        self._init_websocket_channel()
        self._init_i2c_channel()
        self._init_udp_channel()
        self._init_file_channel()
        
        # Start message processing thread
        self.processing_thread = threading.Thread(target=self._process_messages)
        self.processing_thread.daemon = True
        
        logger.info("Communication Manager initialized")
    
    def _init_websocket_channel(self):
        """Initialize WebSocket communication channel"""
        try:
            self.channels[CommunicationChannel.WEBSOCKET] = {
                'enabled': True,
                'url': 'ws://localhost:9999/socket/',
                'timeout': 5,
                'retry_interval': 1
            }
            logger.info("WebSocket channel initialized")
        except Exception as e:
            logger.error(f"WebSocket channel initialization failed: {e}")
    
    def _init_i2c_channel(self):
        """Initialize I2C communication channel"""
        try:
            self.channels[CommunicationChannel.I2C] = {
                'enabled': True,
                'bus': 1,
                'arduino_address': 0x08,
                'timeout': 1
            }
            logger.info("I2C channel initialized")
        except Exception as e:
            logger.error(f"I2C channel initialization failed: {e}")
    
    def _init_udp_channel(self):
        """Initialize UDP communication channel"""
        try:
            self.channels[CommunicationChannel.UDP] = {
                'enabled': True,
                'host': 'localhost',
                'port': 8888,
                'timeout': 1
            }
            logger.info("UDP channel initialized")
        except Exception as e:
            logger.error(f"UDP channel initialization failed: {e}")
    
    def _init_file_channel(self):
        """Initialize file-based communication channel"""
        try:
            self.channels[CommunicationChannel.FILE] = {
                'enabled': True,
                'status_file': '/tmp/poppy_status.json',
                'command_file': '/tmp/poppy_commands.json',
                'emergency_file': '/tmp/poppy_emergency_status.json'
            }
            logger.info("File channel initialized")
        except Exception as e:
            logger.error(f"File channel initialization failed: {e}")
    
    def start(self):
        """Start the communication manager"""
        self.is_running = True
        self.processing_thread.start()
        logger.info("Communication Manager started")
    
    def stop(self):
        """Stop the communication manager"""
        self.is_running = False
        if self.processing_thread.is_alive():
            self.processing_thread.join(timeout=5)
        logger.info("Communication Manager stopped")
    
    def subscribe(self, message_type: MessageType, callback: Callable[[Message], None]):
        """Subscribe to a specific message type"""
        if message_type not in self.subscribers:
            self.subscribers[message_type] = []
        self.subscribers[message_type].append(callback)
        logger.info(f"Subscribed to {message_type.value} messages")
    
    def unsubscribe(self, message_type: MessageType, callback: Callable[[Message], None]):
        """Unsubscribe from a specific message type"""
        if message_type in self.subscribers:
            if callback in self.subscribers[message_type]:
                self.subscribers[message_type].remove(callback)
                logger.info(f"Unsubscribed from {message_type.value} messages")
    
    def send_message(self, message: Message):
        """Send a message through the communication system"""
        try:
            # Add to message queue with priority
            priority = message.priority
            self.message_queue.put((priority, time.time(), message))
            
            # Store in history
            self.message_history.append(message)
            if len(self.message_history) > self.max_history:
                self.message_history = self.message_history[-self.max_history:]
            
            logger.debug(f"Message queued: {message.message_type.value} from {message.source}")
            
        except Exception as e:
            logger.error(f"Failed to queue message: {e}")
    
    def send_emergency(self, source: str, data: Dict[str, Any]):
        """Send emergency message with highest priority"""
        message = Message(
            message_type=MessageType.EMERGENCY,
            source=source,
            destination="all",
            data=data,
            timestamp=time.time(),
            priority=2,  # Critical priority
            channel=CommunicationChannel.WEBSOCKET
        )
        self.send_message(message)
    
    def send_status_update(self, source: str, status_data: Dict[str, Any]):
        """Send status update message"""
        message = Message(
            message_type=MessageType.STATUS_UPDATE,
            source=source,
            destination="system_integration",
            data=status_data,
            timestamp=time.time(),
            priority=0,
            channel=CommunicationChannel.WEBSOCKET
        )
        self.send_message(message)
    
    def send_command(self, source: str, destination: str, command_data: Dict[str, Any]):
        """Send command message"""
        message = Message(
            message_type=MessageType.COMMAND,
            source=source,
            destination=destination,
            data=command_data,
            timestamp=time.time(),
            priority=1,
            channel=CommunicationChannel.WEBSOCKET
        )
        self.send_message(message)
    
    def _process_messages(self):
        """Process messages from the queue"""
        while self.is_running:
            try:
                if not self.message_queue.empty():
                    priority, timestamp, message = self.message_queue.get_nowait()
                    
                    # Send message through appropriate channel
                    success = self._send_through_channel(message)
                    
                    if not success and message.retry_count < message.max_retries:
                        # Retry with exponential backoff
                        message.retry_count += 1
                        retry_delay = 2 ** message.retry_count
                        time.sleep(retry_delay)
                        self.message_queue.put((priority, time.time(), message))
                    elif not success:
                        logger.error(f"Failed to send message after {message.max_retries} retries")
                    
                    # Notify subscribers
                    self._notify_subscribers(message)
                
                time.sleep(0.01)  # Small delay to prevent busy waiting
                
            except queue.Empty:
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error processing messages: {e}")
                time.sleep(1)
    
    def _send_through_channel(self, message: Message) -> bool:
        """Send message through the specified channel"""
        try:
            if message.channel == CommunicationChannel.WEBSOCKET:
                return self._send_websocket(message)
            elif message.channel == CommunicationChannel.I2C:
                return self._send_i2c(message)
            elif message.channel == CommunicationChannel.UDP:
                return self._send_udp(message)
            elif message.channel == CommunicationChannel.FILE:
                return self._send_file(message)
            else:
                logger.error(f"Unknown communication channel: {message.channel}")
                return False
        except Exception as e:
            logger.error(f"Failed to send through {message.channel.value}: {e}")
            return False
    
    def _send_websocket(self, message: Message) -> bool:
        """Send message via WebSocket"""
        try:
            if not self.channels[CommunicationChannel.WEBSOCKET]['enabled']:
                return False
            
            ws = create_connection(
                self.channels[CommunicationChannel.WEBSOCKET]['url'],
                timeout=self.channels[CommunicationChannel.WEBSOCKET]['timeout']
            )
            
            message_data = {
                'type': message.message_type.value,
                'source': message.source,
                'destination': message.destination,
                'data': message.data,
                'timestamp': message.timestamp,
                'priority': message.priority
            }
            
            ws.send(json.dumps(message_data))
            ws.close()
            return True
            
        except Exception as e:
            logger.warning(f"WebSocket send failed: {e}")
            return False
    
    def _send_i2c(self, message: Message) -> bool:
        """Send message via I2C"""
        try:
            if not self.channels[CommunicationChannel.I2C]['enabled']:
                return False
            
            bus = smbus.SMBus(self.channels[CommunicationChannel.I2C]['bus'])
            address = self.channels[CommunicationChannel.I2C]['arduino_address']
            
            # Convert message to I2C format
            if message.message_type == MessageType.EMERGENCY:
                # Send emergency stop command
                bus.write_byte(address, 0xFF)  # Emergency stop code
            elif message.message_type == MessageType.MOTOR_CONTROL:
                # Send motor control data
                motor_data = message.data
                bus.write_i2c_block_data(address, 0x01, [
                    int(motor_data.get('motor_id', 0)),
                    int(motor_data.get('speed', 0) * 100),
                    int(motor_data.get('direction', 0))
                ])
            
            return True
            
        except Exception as e:
            logger.warning(f"I2C send failed: {e}")
            return False
    
    def _send_udp(self, message: Message) -> bool:
        """Send message via UDP"""
        try:
            if not self.channels[CommunicationChannel.UDP]['enabled']:
                return False
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.channels[CommunicationChannel.UDP]['timeout'])
            
            message_data = json.dumps({
                'type': message.message_type.value,
                'source': message.source,
                'destination': message.destination,
                'data': message.data,
                'timestamp': message.timestamp,
                'priority': message.priority
            })
            
            sock.sendto(message_data.encode(), (
                self.channels[CommunicationChannel.UDP]['host'],
                self.channels[CommunicationChannel.UDP]['port']
            ))
            sock.close()
            return True
            
        except Exception as e:
            logger.warning(f"UDP send failed: {e}")
            return False
    
    def _send_file(self, message: Message) -> bool:
        """Send message via file system"""
        try:
            if not self.channels[CommunicationChannel.FILE]['enabled']:
                return False
            
            file_path = None
            if message.message_type == MessageType.EMERGENCY:
                file_path = self.channels[CommunicationChannel.FILE]['emergency_file']
            elif message.message_type == MessageType.STATUS_UPDATE:
                file_path = self.channels[CommunicationChannel.FILE]['status_file']
            elif message.message_type == MessageType.COMMAND:
                file_path = self.channels[CommunicationChannel.FILE]['command_file']
            else:
                return False
            
            message_data = {
                'type': message.message_type.value,
                'source': message.source,
                'destination': message.destination,
                'data': message.data,
                'timestamp': message.timestamp,
                'priority': message.priority
            }
            
            with open(file_path, 'w') as f:
                json.dump(message_data, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.warning(f"File send failed: {e}")
            return False
    
    def _notify_subscribers(self, message: Message):
        """Notify subscribers of a message"""
        try:
            if message.message_type in self.subscribers:
                for callback in self.subscribers[message.message_type]:
                    try:
                        callback(message)
                    except Exception as e:
                        logger.error(f"Subscriber callback failed: {e}")
        except Exception as e:
            logger.error(f"Failed to notify subscribers: {e}")
    
    def get_message_history(self, message_type: Optional[MessageType] = None, limit: int = 100):
        """Get message history"""
        if message_type:
            filtered = [msg for msg in self.message_history if msg.message_type == message_type]
            return filtered[-limit:]
        return self.message_history[-limit:]
    
    def get_channel_status(self) -> Dict[str, bool]:
        """Get status of all communication channels"""
        return {channel.value: config['enabled'] for channel, config in self.channels.items()}
    
    def enable_channel(self, channel: CommunicationChannel):
        """Enable a communication channel"""
        if channel in self.channels:
            self.channels[channel]['enabled'] = True
            logger.info(f"Enabled {channel.value} channel")
    
    def disable_channel(self, channel: CommunicationChannel):
        """Disable a communication channel"""
        if channel in self.channels:
            self.channels[channel]['enabled'] = False
            logger.info(f"Disabled {channel.value} channel")

# Global communication manager instance
_communication_manager = None

def get_communication_manager() -> CommunicationManager:
    """Get the global communication manager instance"""
    global _communication_manager
    if _communication_manager is None:
        _communication_manager = CommunicationManager()
    return _communication_manager

# Example usage and testing
if __name__ == "__main__":
    def test_message_handler(message: Message):
        print(f"Received message: {message.message_type.value} from {message.source}")
        print(f"Data: {message.data}")
    
    # Initialize communication manager
    comm_manager = get_communication_manager()
    comm_manager.start()
    
    # Subscribe to emergency messages
    comm_manager.subscribe(MessageType.EMERGENCY, test_message_handler)
    
    # Send test messages
    comm_manager.send_emergency("power_management", {
        "battery_voltage": 10.5,
        "battery_percentage": 15.0,
        "action": "immediate_shutdown"
    })
    
    comm_manager.send_status_update("face_detection", {
        "faces_detected": 2,
        "processing_time": 0.05,
        "confidence": 0.95
    })
    
    # Run for a few seconds
    time.sleep(5)
    
    # Stop communication manager
    comm_manager.stop()
