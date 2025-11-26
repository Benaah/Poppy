"""
Example 2: Dance Sequence
"""

from poppy_sdk import PoppyRobot

poppy = PoppyRobot.connect()

# Create a dance sequence
with poppy.sequence("dance") as seq:
    seq.forward(20)
    seq.spin(360, speed=40)
    seq.backward(20)
    seq.turn_left(180)
    seq.forward(30)
    seq.spin(-360, speed=40)

# Execute the sequence multiple times
poppy.execute("dance", repeat=2)

print("Dance complete!")
