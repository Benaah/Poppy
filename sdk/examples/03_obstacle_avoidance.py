"""
Example 3: Obstacle Avoidance with Events
"""

from poppy_sdk import PoppyRobot

poppy = PoppyRobot.connect()

# Register event handlers
@poppy.on_obstacle
def handle_obstacle(distance):
    print(f"[WARN] Obstacle detected at {distance}cm!")
    poppy.stop()
    poppy.backward(10)
    poppy.turn_right(45)
    print("Obstacle avoided, continuing...")

@poppy.on_battery_low
def handle_battery():
    print("[BATTERY] Battery low, returning to base...")
    # Add navigation to charging dock

# Navigate around
poppy.forward(100)
