#!/usr/bin/env python3

# Unified Voice Control System for Poppy Robot
# Supports both Google Assistant and Amazon Alexa

import json
import time
import threading
import queue
import logging
from enum import Enum
from typing import Dict, Callable, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceProvider(Enum):
    GOOGLE_ASSISTANT = "google_assistant"
    ALEXA = "alexa"
    BOTH = "both"

class UnifiedVoiceControl:
    def __init__(self, websocket_url="ws://localhost:9999/socket/"):
        """Initialize unified voice control system."""
        self.websocket_url = websocket_url
        self.ws = None
        self.is_connected = False
        self.running = False
        self.active_providers = set()
        
        # Command processing
        self.command_queue = queue.Queue()
        self.command_history = []
        
        # Voice command mappings
        self.command_mappings = {
            # Movement commands
            "move forward": self.move_forward,
            "go forward": self.move_forward,
            "move backward": self.move_backward,
            "go backward": self.move_backward,
            "turn left": self.turn_left,
            "turn right": self.turn_right,
            "stop": self.stop_robot,
            "halt": self.stop_robot,
            "pause": self.stop_robot,
            
            # Navigation commands
            "find face": self.find_face,
            "look for people": self.find_face,
            "search for faces": self.find_face,
            "come here": self.come_here,
            "follow me": self.follow_me,
            "go home": self.go_home,
            
            # Docking commands
            "dock": self.dock_robot,
            "go to charging station": self.dock_robot,
            "undock": self.undock_robot,
            "leave charging station": self.undock_robot,
            "charge": self.dock_robot,
            
            # Status commands
            "status": self.get_status,
            "battery": self.get_battery_status,
            "health": self.get_health_status,
            "battery status": self.get_battery_status,
            "system status": self.get_system_status,
            
            # Entertainment commands
            "dance": self.dance,
            "spin": self.spin,
            "wave": self.wave,
            "nod": self.nod,
            
            # System commands
            "restart": self.restart_robot,
            "calibrate": self.calibrate_sensors,
            "test": self.run_tests,
            "emergency stop": self.emergency_stop,
            "calibrate imu": self.calibrate_imu,
            "calibrate spatial": self.calibrate_spatial,
            "calibrate docking": self.calibrate_docking,
            "test motors": self.test_motors,
            
            # Feature toggles
            "enable spatial awareness": self.enable_spatial_awareness,
            "disable spatial awareness": self.disable_spatial_awareness,
            "enable adaptive pid": self.enable_adaptive_pid,
            "disable adaptive pid": self.disable_adaptive_pid,
            "enable voice control": self.enable_voice_control,
            "disable voice control": self.disable_voice_control
        }
        
        # Provider-specific configurations
        self.provider_configs = {
            VoiceProvider.GOOGLE_ASSISTANT: {
                "wake_words": ["hey google", "ok google"],
                "response_prefix": "[Google Assistant]:"
            },
            VoiceProvider.ALEXA: {
                "wake_words": ["alexa", "amazon"],
                "response_prefix": "[Alexa]:"
            }
        }
    
    def connect_websocket(self):
        """Establish WebSocket connection to Poppy control system."""
        try:
            from websocket import create_connection
            self.ws = create_connection(self.websocket_url, timeout=5)
            self.is_connected = True
            logger.info("[OK] WebSocket connected to Poppy control system")
            return True
        except Exception as e:
            logger.error(f"[ERROR] WebSocket connection failed: {e}")
            self.is_connected = False
            return False
    
    def safe_send_command(self, command, provider=None):
        """Safely send command via WebSocket with error handling."""
        try:
            if not self.is_connected:
                if not self.connect_websocket():
                    logger.error("[ERROR] Cannot send command - no WebSocket connection")
                    return False
            
            self.ws.send(command)
            prefix = self.provider_configs.get(provider, {}).get("response_prefix", "[Robot]")
            logger.info(f"{prefix} Sent command: {command}")
            return True
        except Exception as e:
            logger.error(f"[ERROR] WebSocket send failed: {e}")
            self.is_connected = False
            return False
    
    def process_voice_command(self, command_text, provider=None):
        """Process voice command and execute appropriate action."""
        command_text = command_text.lower().strip()
        logger.info(f"[VOICE] Processing voice command: '{command_text}' (Provider: {provider})")
        
        # Add to command history
        self.command_history.append({
            "command": command_text,
            "provider": provider,
            "timestamp": time.time()
        })
        
        # Keep only last 100 commands
        if len(self.command_history) > 100:
            self.command_history = self.command_history[-100:]
        
        # Find matching command
        for voice_pattern, action_func in self.command_mappings.items():
            if voice_pattern in command_text:
                try:
                    action_func(command_text, provider)
                    return True
                except Exception as e:
                    logger.error(f"[ERROR] Error executing command '{voice_pattern}': {e}")
                    return False
        
        # No matching command found
        logger.warning(f"[WARN]  Unknown command: '{command_text}'")
        return False
    
    # Robot movement commands
    def move_forward(self, command_text, provider=None):
        """Move robot forward."""
        distance = self.extract_number(command_text, default=0.1)
        self.safe_send_command(f"move,{distance}", provider)
        logger.info(f"[Robot] Moving forward {distance}m")
    
    def move_backward(self, command_text, provider=None):
        """Move robot backward."""
        distance = self.extract_number(command_text, default=0.1)
        self.safe_send_command(f"move,-{distance}", provider)
        logger.info(f"[Robot] Moving backward {distance}m")
    
    def turn_left(self, command_text, provider=None):
        """Turn robot left."""
        angle = self.extract_number(command_text, default=5)
        self.safe_send_command(f"turn,{angle}", provider)
        logger.info(f"[Robot] Turning left {angle}°")
    
    def turn_right(self, command_text, provider=None):
        """Turn robot right."""
        angle = self.extract_number(command_text, default=5)
        self.safe_send_command(f"turn,-{angle}", provider)
        logger.info(f"[Robot] Turning right {angle}°")
    
    def stop_robot(self, command_text, provider=None):
        """Stop robot movement."""
        self.safe_send_command("move,0", provider)
        self.safe_send_command("turn,0", provider)
        logger.info("[Robot] Robot stopped")
    
    def find_face(self, command_text, provider=None):
        """Start face detection and tracking."""
        self.safe_send_command("find_face", provider)
        logger.info("[Robot] Starting face search...")
    
    def come_here(self, command_text, provider=None):
        """Make robot approach the user."""
        self.safe_send_command("move,0.2", provider)
        logger.info("[Robot] Coming to you!")
    
    def follow_me(self, command_text, provider=None):
        """Start following mode."""
        self.safe_send_command("follow_mode", provider)
        logger.info("[Robot] Following mode activated!")
    
    def go_home(self, command_text, provider=None):
        """Return robot to home position."""
        self.safe_send_command("go_home", provider)
        logger.info("[Robot] Returning to home position...")
    
    def get_status(self, command_text, provider=None):
        """Get robot status."""
        logger.info("[Robot] Poppy status: Active and ready")
        # Could implement actual status checking here
    
    def get_battery_status(self, command_text, provider=None):
        """Get battery status."""
        logger.info("[Robot] Battery status: Good")
        # Could implement actual battery checking here
    
    def get_health_status(self, command_text, provider=None):
        """Get robot health status."""
        logger.info("[Robot] Health status: All systems operational")
        # Could implement actual health checking here
    
    def dance(self, command_text, provider=None):
        """Make robot dance."""
        # Simple dance sequence
        dance_commands = [
            "turn,10", "turn,-10", "turn,10", "turn,-10",
            "move,0.1", "move,-0.1", "move,0.1", "move,-0.1"
        ]
        for cmd in dance_commands:
            self.safe_send_command(cmd, provider)
            time.sleep(0.5)
        logger.info("[Robot] Dance complete!")
    
    def spin(self, command_text, provider=None):
        """Make robot spin."""
        self.safe_send_command("turn,360", provider)
        logger.info("[Robot] Spinning!")
    
    def wave(self, command_text, provider=None):
        """Make robot wave."""
        # Simple wave motion
        wave_commands = ["turn,5", "turn,-5", "turn,5", "turn,-5"]
        for cmd in wave_commands:
            self.safe_send_command(cmd, provider)
            time.sleep(0.3)
        logger.info("[Robot] Wave complete!")
    
    def nod(self, command_text, provider=None):
        """Make robot nod."""
        # Simple nod motion (tilt forward and back)
        nod_commands = ["tilt,10", "tilt,-10", "tilt,0"]
        for cmd in nod_commands:
            self.safe_send_command(cmd, provider)
            time.sleep(0.5)
        logger.info("[Robot] Nod complete!")
    
    def restart_robot(self, command_text, provider=None):
        """Restart robot systems."""
        self.safe_send_command("restart", provider)
        logger.info("[Robot] Restarting robot systems...")
    
    def calibrate_sensors(self, command_text, provider=None):
        """Calibrate robot sensors."""
        self.safe_send_command("calibrate", provider)
        logger.info("[Robot] Calibrating sensors...")
    
    def run_tests(self, command_text, provider=None):
        """Run system tests."""
        self.safe_send_command("test", provider)
        logger.info("[Robot] Running system tests...")
    
    # Docking commands
    def dock_robot(self, command_text, provider=None):
        """Start docking sequence."""
        self.safe_send_command("docking_start", provider)
        logger.info("[Robot] Starting docking sequence...")
    
    def undock_robot(self, command_text, provider=None):
        """Stop docking and undock."""
        self.safe_send_command("docking_stop", provider)
        logger.info("[Robot] Undocking from charging station...")
    
    # Enhanced status commands
    def get_system_status(self, command_text, provider=None):
        """Get comprehensive system status."""
        self.safe_send_command("system_status", provider)
        logger.info("[Robot] Getting system status...")
    
    # Emergency commands
    def emergency_stop(self, command_text, provider=None):
        """Emergency stop all systems."""
        self.safe_send_command("emergency_stop", provider)
        logger.info("[STOP] EMERGENCY STOP ACTIVATED")
    
    # Calibration commands
    def calibrate_imu(self, command_text, provider=None):
        """Calibrate IMU sensors."""
        self.safe_send_command("imu_calibrate", provider)
        logger.info("[Robot] Calibrating IMU sensors...")
    
    def calibrate_spatial(self, command_text, provider=None):
        """Calibrate spatial awareness system."""
        self.safe_send_command("spatial_calibrate", provider)
        logger.info("[Robot] Calibrating spatial awareness...")
    
    def calibrate_docking(self, command_text, provider=None):
        """Calibrate docking system."""
        self.safe_send_command("docking_calibrate", provider)
        logger.info("[Robot] Calibrating docking system...")
    
    def test_motors(self, command_text, provider=None):
        """Test motor functionality."""
        self.safe_send_command("motor_test", provider)
        logger.info("[Robot] Testing motors...")
    
    # Feature toggle commands
    def enable_spatial_awareness(self, command_text, provider=None):
        """Enable spatial awareness system."""
        self.safe_send_command("spatial_awareness_on", provider)
        logger.info("[Robot] Spatial awareness enabled")
    
    def disable_spatial_awareness(self, command_text, provider=None):
        """Disable spatial awareness system."""
        self.safe_send_command("spatial_awareness_off", provider)
        logger.info("[Robot] Spatial awareness disabled")
    
    def enable_adaptive_pid(self, command_text, provider=None):
        """Enable adaptive PID control."""
        self.safe_send_command("adaptive_pid_on", provider)
        logger.info("[Robot] Adaptive PID enabled")
    
    def disable_adaptive_pid(self, command_text, provider=None):
        """Disable adaptive PID control."""
        self.safe_send_command("adaptive_pid_off", provider)
        logger.info("[Robot] Adaptive PID disabled")
    
    def enable_voice_control(self, command_text, provider=None):
        """Enable voice control system."""
        self.safe_send_command("voice_control_on", provider)
        logger.info("[Robot] Voice control enabled")
    
    def disable_voice_control(self, command_text, provider=None):
        """Disable voice control system."""
        self.safe_send_command("voice_control_off", provider)
        logger.info("[Robot] Voice control disabled")
    
    def extract_number(self, text, default=1.0):
        """Extract number from command text."""
        import re
        numbers = re.findall(r'\d+\.?\d*', text)
        if numbers:
            return float(numbers[0])
        return default
    
    def start_voice_control(self, providers=None):
        """Start the unified voice control system."""
        if providers is None:
            providers = [VoiceProvider.GOOGLE_ASSISTANT, VoiceProvider.ALEXA]
        
        self.active_providers = set(providers)
        self.running = True
        
        logger.info(f"[VOICE] Unified voice control started with providers: {[p.value for p in self.active_providers]}")
        
        # Connect to WebSocket
        if not self.connect_websocket():
            logger.error("[ERROR] Failed to start voice control - no WebSocket connection")
            return False
        
        # Start command processing thread
        self.command_thread = threading.Thread(target=self._process_commands)
        self.command_thread.daemon = True
        self.command_thread.start()
        
        return True
    
    def stop_voice_control(self):
        """Stop the unified voice control system."""
        self.running = False
        if self.ws:
            self.ws.close()
        logger.info("[STOP] Unified voice control stopped")
    
    def _process_commands(self):
        """Process commands from the queue."""
        while self.running:
            try:
                if not self.command_queue.empty():
                    command_data = self.command_queue.get(timeout=1)
                    command_text = command_data.get("command", "")
                    provider = command_data.get("provider")
                    self.process_voice_command(command_text, provider)
                time.sleep(0.1)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"[ERROR] Error processing commands: {e}")
    
    def add_command(self, command_text, provider=None):
        """Add a command to the processing queue."""
        self.command_queue.put({
            "command": command_text,
            "provider": provider
        })
    
    def get_command_history(self, limit=10):
        """Get recent command history."""
        return self.command_history[-limit:] if self.command_history else []
    
    def get_available_commands(self):
        """Get list of available voice commands."""
        return list(self.command_mappings.keys())

# Main function for testing
def main():
    """Test the unified voice control system."""
    voice_control = UnifiedVoiceControl()
    
    if voice_control.start_voice_control():
        print("[VOICE] Unified voice control ready!")
        print("Available commands:", voice_control.get_available_commands())
        
        # Simulate voice commands for testing
        test_commands = [
            ("move forward 0.2", VoiceProvider.GOOGLE_ASSISTANT),
            ("turn left 10", VoiceProvider.ALEXA),
            ("find face", VoiceProvider.GOOGLE_ASSISTANT),
            ("dance", VoiceProvider.ALEXA),
            ("stop", VoiceProvider.GOOGLE_ASSISTANT)
        ]
        
        for cmd, provider in test_commands:
            print(f"\n[VOICE] Simulating: '{cmd}' ({provider.value})")
            voice_control.process_voice_command(cmd, provider)
            time.sleep(2)
        
        # Show command history
        print("\n[HISTORY] Command History:")
        for cmd in voice_control.get_command_history(5):
            print(f"  {cmd['timestamp']}: {cmd['command']} ({cmd['provider']})")
        
        voice_control.stop_voice_control()
    else:
        print("[ERROR] Failed to start unified voice control")

if __name__ == "__main__":
    main()
