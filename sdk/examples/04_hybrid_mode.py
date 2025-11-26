"""
Example 4: Hybrid Mode Demonstration
"""

from poppy_sdk import PoppyRobot
import time

poppy = PoppyRobot.connect()

print("Demonstrating hybrid locomotion...")

# Start in track mode (default)
print("Track mode: fast movement on flat surface")
poppy.forward(100, speed=70)
time.sleep(1)

# Switch to leg mode for obstacles
print("Switching to leg mode for obstacle...")
poppy.set_mode("leg")
poppy.forward(30, speed=40)  # Slower but can climb
time.sleep(1)

# Hybrid mode for maximum traction
print("Hybrid mode: tracks + legs for incline")
poppy.set_mode("hybrid")
poppy.forward(50, speed=50)

# Return to track mode
poppy.set_mode("track")
print("Back to track mode")
