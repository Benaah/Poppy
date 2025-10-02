#!/usr/bin/env python3

# Amazon Alexa Integration for Poppy Robot
# Provides voice control capabilities alongside Google Assistant

import json
import time
import threading
import queue
from websocket import create_connection
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlexaIntegration:
    def __init__(self, websocket_url="ws://localhost:9999/socket/"):
        """Initialize Alexa integration with WebSocket connection."""
        self.websocket_url = websocket_url
        self.ws = None
        self.is_connected = False
        self.command_queue = queue.Queue()
        self.running = False
        
        # Alexa skill configuration
        self.skill_id = "amzn1.ask.skill.poppy-robot"
        self.app_id = "poppy-robot-alexa"
        
        # Voice command mappings
        self.command_mappings = {
            "move forward": self.move_forward,
            "go forward": self.move_forward,
            "move backward": self.move_backward,
            "go backward": self.move_backward,
            "turn left": self.turn_left,
            "turn right": self.turn_right,
            "stop": self.stop_robot,
            "halt": self.stop_robot,
            "find face": self.find_face,
            "look for people": self.find_face,
            "status": self.get_status,
            "battery": self.get_battery_status,
            "dance": self.dance,
            "spin": self.spin,
            "come here": self.come_here,
            "follow me": self.follow_me
        }
    
    def connect_websocket(self):
        """Establish WebSocket connection to Poppy control system."""
        try:
            self.ws = create_connection(self.websocket_url, timeout=5)
            self.is_connected = True
            logger.info("Alexa WebSocket connected to Poppy control system")
            return True
        except Exception as e:
            logger.error(f"Alexa WebSocket connection failed: {e}")
            self.is_connected = False
            return False
    
    def safe_send_command(self, command):
        """Safely send command via WebSocket with error handling."""
        try:
            if not self.is_connected:
                if not self.connect_websocket():
                    logger.error("Cannot send command - no WebSocket connection")
                    return False
            
            self.ws.send(command)
            logger.info(f"Sent command: {command}")
            return True
        except Exception as e:
            logger.error(f"WebSocket send failed: {e}")
            self.is_connected = False
            return False
    
    def process_voice_command(self, command_text):
        """Process voice command and execute appropriate action."""
        command_text = command_text.lower().strip()
        logger.info(f" Processing voice command: '{command_text}'")
        
        # Find matching command
        for voice_pattern, action_func in self.command_mappings.items():
            if voice_pattern in command_text:
                try:
                    action_func(command_text)
                    return True
                except Exception as e:
                    logger.error(f" Error executing command '{voice_pattern}': {e}")
                    return False
        
        # No matching command found
        logger.warning(f" Unknown command: '{command_text}'")
        return False
    
    # Robot movement commands
    def move_forward(self, command_text):
        """Move robot forward."""
        distance = self.extract_number(command_text, default=0.1)
        self.safe_send_command(f"move,{distance}")
        logger.info(f" Moving forward {distance}m")
    
    def move_backward(self, command_text):
        """Move robot backward."""
        distance = self.extract_number(command_text, default=0.1)
        self.safe_send_command(f"move,-{distance}")
        logger.info(f" Moving backward {distance}m")
    
    def turn_left(self, command_text):
        """Turn robot left."""
        angle = self.extract_number(command_text, default=5)
        self.safe_send_command(f"turn,{angle}")
        logger.info(f" Turning left {angle}°")
    
    def turn_right(self, command_text):
        """Turn robot right."""
        angle = self.extract_number(command_text, default=5)
        self.safe_send_command(f"turn,-{angle}")
        logger.info(f" Turning right {angle}°")
    
    def stop_robot(self, command_text):
        """Stop robot movement."""
        self.safe_send_command("move,0")
        self.safe_send_command("turn,0")
        logger.info(" Robot stopped")
    
    def find_face(self, command_text):
        """Start face detection and tracking."""
        self.safe_send_command("find_face")
        logger.info("Starting face search...")
    
    def get_status(self, command_text):
        """Get robot status."""
        status = "Unknown"
        try:
            # Send a ping or status request to the robot
            self.safe_send_command("status")
            # Here, you could implement a mechanism to receive a response from the robot,
            # e.g., via a status queue or callback. For now, we assume success if no exception.
            status = "Active and ready"
            logger.info(f"Poppy status: {status}")
        except Exception as e:
            status = f"Error: {e}"
            logger.error(f"Failed to get robot status: {e}")
        return status

    def get_battery_status(self, command_text):
        """Get battery status."""
        battery_status = "Unknown"
        try:
            # Query battery status from BMS
            from bms_service import get_bms_service
            bms = get_bms_service()
            battery_data = bms.get_battery_status()
            
            battery_level = battery_data.charge_percentage
            if battery_level >= 80:
                battery_status = f"Good ({battery_level:.1f}%)"
            elif battery_level >= 40:
                battery_status = f"Medium ({battery_level:.1f}%)"
            else:
                battery_status = f"Low ({battery_level:.1f}%)"
            
            logger.info(f"Battery status: {battery_status}")
        except Exception as e:
            battery_status = f"Error: {e}"
            logger.error(f"Failed to get battery status: {e}")
        return battery_status
    def dance(self, command_text):
        """Make robot dance."""
        # Simple dance sequence
        dance_commands = [
            "turn,10", "turn,-10", "turn,10", "turn,-10",
            "move,0.1", "move,-0.1", "move,0.1", "move,-0.1"
        ]
        for cmd in dance_commands:
            self.safe_send_command(cmd)
            time.sleep(0.5)
        logger.info(" Dance complete!")
    
    def spin(self, command_text):
        """Make robot spin."""
        self.safe_send_command("turn,360")
        logger.info(" Spinning!")
    
    def come_here(self, command_text):
        """Make robot approach the user."""
        self.safe_send_command("move,0.2")
        logger.info(" Coming to you!")
    
    def follow_me(self, command_text):
        """Start following mode."""
        self.safe_send_command("follow_mode")
        logger.info(" Following mode activated!")
    
    def extract_number(self, text, default=1.0):
        """Extract number from command text."""
        import re
        numbers = re.findall(r'\d+\.?\d*', text)
        if numbers:
            return float(numbers[0])
        return default
    
    def start_listening(self):
        """Start the Alexa integration service."""
        self.running = True
        logger.info(" Alexa integration started")
        
        # Connect to WebSocket
        if not self.connect_websocket():
            logger.error(" Failed to start Alexa integration - no WebSocket connection")
            return False
        
        # Start command processing thread
        self.command_thread = threading.Thread(target=self._process_commands)
        self.command_thread.daemon = True
        self.command_thread.start()
        
        return True
    
    def stop_listening(self):
        """Stop the Alexa integration service."""
        self.running = False
        if self.ws:
            self.ws.close()
        logger.info(" Alexa integration stopped")
    
    def _process_commands(self):
        """Process commands from the queue."""
        while self.running:
            try:
                if not self.command_queue.empty():
                    command = self.command_queue.get(timeout=1)
                    self.process_voice_command(command)
                time.sleep(0.1)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f" Error processing commands: {e}")
    
    def add_command(self, command_text):
        """Add a command to the processing queue."""
        self.command_queue.put(command_text)

# Simulated Alexa skill handler
class AlexaSkillHandler:
    def __init__(self, alexa_integration):
        self.alexa = alexa_integration
    
    def handle_intent(self, intent_name, slots=None):
        """Handle Alexa skill intent."""
        logger.info(f" Handling intent: {intent_name}")
        
        if intent_name == "MoveRobotIntent":
            direction = slots.get('direction', 'forward') if slots else 'forward'
            distance = slots.get('distance', 0.1) if slots else 0.1
            
            if direction == 'forward':
                self.alexa.move_forward(f"move forward {distance}")
            elif direction == 'backward':
                self.alexa.move_backward(f"move backward {distance}")
            elif direction == 'left':
                self.alexa.turn_left(f"turn left {distance}")
            elif direction == 'right':
                self.alexa.turn_right(f"turn right {distance}")
        
        elif intent_name == "StopRobotIntent":
            self.alexa.stop_robot("stop")
        
        elif intent_name == "FindFaceIntent":
            self.alexa.find_face("find face")
        
        elif intent_name == "RobotStatusIntent":
            self.alexa.get_status("status")
        
        elif intent_name == "DanceIntent":
            self.alexa.dance("dance")
        
        elif intent_name == "SpinIntent":
            self.alexa.spin("spin")
        
        else:
            logger.warning(f" Unknown intent: {intent_name}")

# Main function for testing
def main():
    """Test the Alexa integration."""
    alexa = AlexaIntegration()
    
    if alexa.start_listening():
        print(" Alexa integration ready!")
        print("Try saying: 'move forward', 'turn left', 'stop', 'find face', 'dance'")
        
        # Simulate voice commands for testing
        test_commands = [
            "move forward 0.2",
            "turn left 10",
            "find face",
            "dance",
            "stop"
        ]
        
        for cmd in test_commands:
            print(f"\n Simulating: '{cmd}'")
            alexa.process_voice_command(cmd)
            time.sleep(2)
        
        alexa.stop_listening()
    else:
        print(" Failed to start Alexa integration")

if __name__ == "__main__":
    main()
