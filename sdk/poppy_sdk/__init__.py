"""
Poppy Python SDK - Educational Programming Interface
"""

import rclpy
from rclpy.node import Node
from poppy_interfaces.msg import Movement Command, RobotState
from poppy_interfaces.srv import SetMode
import time
from typing import Optional, Callable
import requests


class PoppyRobot:
    """Main SDK class for controlling Poppy robot"""
    
    def __init__(self, robot_address: str = "localhost", port: int = 8000):
        """
        Initialize connection to Poppy robot
        
        Args:
            robot_address: IP address or hostname of robot
            port: REST API port
        """
        self.api_url = f"http://{robot_address}:{port}/api"
        self.robot_address = robot_address
        self.connected = False
        
        # Event handlers
        self._obstacle_handler: Optional[Callable] = None
        self._battery_low_handler: Optional[Callable] = None
        
        # Internal state
        self._current_mode = 0
        self._battery_percentage = 100.0
        
    @classmethod
    def connect(cls, address: str = "poppy-robot.local"):
        """
        Connect to a Poppy robot
        
        Args:
            address: Robot hostname or IP
            
        Returns:
            PoppyRobot instance
            
        Example:
            >>> poppy = PoppyRobot.connect("poppy-living-room.local")
        """
        robot = cls(address)
        robot._establish_connection()
        return robot
        
    def _establish_connection(self):
        """Establish connection to robot"""
        try:
            response = requests.get(f"{self.api_url}/status", timeout=5)
            if response.status_code == 200:
                self.connected = True
                print(f"[OK] Connected to Poppy at {self.robot_address}")
            else:
                raise ConnectionError(f"Robot returned status {response.status_code}")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to robot: {e}")
            
    def forward(self, distance: float, speed: float = 50.0):
        """
        Move forward by specified distance
        
        Args:
            distance: Distance in centimeters
            speed: Speed as percentage (0-100)
            
        Example:
            >>> poppy.forward(50, speed=30)  # Move 50cm at 30% speed
        """
        self._send_movement_command("forward", distance=distance, speed=speed)
        
    def backward(self, distance: float, speed: float = 50.0):
        """Move backward by specified distance"""
        self._send_movement_command("backward", distance=distance, speed=speed)
        
    def turn_left(self, degrees: float, speed: float = 50.0):
        """Turn left by specified degrees"""
        self._send_movement_command("turn_left", angle=degrees, speed=speed)
        
    def turn_right(self, degrees: float, speed: float = 50.0):
        """Turn right by specified degrees"""
        self._send_movement_command("turn_right", angle=degrees, speed=speed)
        
    def spin(self, degrees: float, speed: float = 50.0):
        """Spin in place (360° for full rotation)"""
        if degrees > 0:
            self.turn_left(degrees, speed)
        else:
            self.turn_right(abs(degrees), speed)
            
    def stop(self):
        """Immediately stop all movement"""
        self._send_movement_command("stop")
        
    def look_at_me(self, timeout: float = 5.0):
        """
        Trigger user detection and tracking
        
        Args:
            timeout: Maximum time to search for user (seconds)
        """
        response = requests.post(
            f"{self.api_url}/track_user",
            json={"timeout": timeout}
        )
        return response.json()
        
    def set_mode(self, mode: str):
        """
        Change locomotion mode
        
        Args:
            mode: "track", "leg", or "hybrid"
            
        Example:
            >>> poppy.set_mode("leg")  # Switch to leg mode for stairs
        """
        mode_map = {"track": 0, "leg": 1, "hybrid": 2}
        mode_id = mode_map.get(mode.lower())
        
        if mode_id is None:
            raise ValueError(f"Invalid mode: {mode}. Use 'track', 'leg', or 'hybrid'")
            
        response = requests.post(
            f"{self.api_url}/set_mode",
            json={"mode": mode_id}
        )
        
        if response.status_code == 200:
            self._current_mode = mode_id
            print(f"[OK] Switched to {mode} mode")
        
    def get_status(self) -> dict:
        """Get current robot status"""
        response = requests.get(f"{self.api_url}/status")
        return response.json()
        
    def get_battery(self) -> float:
        """Get battery percentage"""
        status = self.get_status()
        return status.get("battery_percentage", 0.0)
        
    def sequence(self, name: str):
        """
        Create a movement sequence
        
        Example:
            >>> with poppy.sequence("dance") as seq:
            ...     seq.forward(20)
            ...     seq.spin(360)
            ...     seq.backward(20)
            >>> poppy.execute("dance", repeat=2)
        """
        return SequenceBuilder(self, name)
        
    def execute(self, sequence_name: str, repeat: int = 1):
        """Execute a saved sequence"""
        for _ in range(repeat):
            response = requests.post(
                f"{self.api_url}/execute_sequence",
                json={"name": sequence_name}
            )
            time.sleep(0.1)  # Brief delay between repetitions
            
    def on_obstacle(self, handler: Callable):
        """
        Register obstacle detection callback
        
        Example:
            >>> @poppy.on_obstacle
            ... def handle_obstacle(distance):
            ...     print(f"Obstacle at {distance}cm!")
            ...     poppy.stop()
        """
        self._obstacle_handler = handler
        return handler
        
    def on_battery_low(self, handler: Callable):
        """Register low battery callback"""
        self._battery_low_handler = handler
        return handler
        
    def _send_movement_command(self, command: str, **kwargs):
        """Internal: Send movement command to robot"""
        payload = {"command": command, **kwargs}
        
        try:
            response = requests.post(
                f"{self.api_url}/move",
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"[WARN] Command failed: {response.text}")
                
        except requests.exceptions.Timeout:
            print("[WARN] Command timed out")
        except Exception as e:
            print(f"[WARN] Error sending command: {e}")


class SequenceBuilder:
    """Helper class for building movement sequences"""
    
    def __init__(self, robot: PoppyRobot, name: str):
        self.robot = robot
        self.name = name
        self.commands = []
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Save sequence to robot
        requests.post(
            f"{self.robot.api_url}/save_sequence",
            json={"name": self.name, "commands": self.commands}
        )
        
    def forward(self, distance: float, speed: float = 50.0):
        """Add forward movement to sequence"""
        self.commands.append({"action": "forward", "distance": distance, "speed": speed})
        return self
        
    def backward(self, distance: float, speed: float = 50.0 ):
        """Add backward movement to sequence"""
        self.commands.append({"action": "backward", "distance": distance, "speed": speed})
        return self
        
    def turn_left(self, degrees: float, speed: float = 50.0):
        """Add left turn to sequence"""
        self.commands.append({"action": "turn_left", "angle": degrees, "speed": speed})
        return self
        
    def turn_right(self, degrees: float, speed: float = 50.0):
        """Add right turn to sequence"""
        self.commands.append({"action": "turn_right", "angle": degrees, "speed": speed})
        return self
        
    def spin(self, degrees: float, speed: float = 50.0):
        """Add spin to sequence"""
        action = "turn_left" if degrees > 0 else "turn_right"
        self.commands.append({"action": action, "angle": abs(degrees), "speed": speed})
        return self
        
    def wait(self, seconds: float):
        """Add wait/pause to sequence"""
        self.commands.append({"action": "wait", "duration": seconds})
        return self
