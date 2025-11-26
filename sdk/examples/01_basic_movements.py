"""
Example 1: Basic Movement
"""

from poppy_sdk import PoppyRobot

# Connect to robot
poppy = PoppyRobot.connect("poppy-living-room.local")

# Basic movements
poppy.forward(50, speed=30)  # Move 50cm forward at 30% speed
poppy.turn_right(90)         # Turn 90 degrees right
poppy.backward(25)           # Move 25cm backward

# Check battery
battery = poppy.get_battery()
print(f"Battery: {battery}%")
