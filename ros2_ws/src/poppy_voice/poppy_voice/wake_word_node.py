"""
Wake Word Detection Node using Picovoice Porcupine
Listens for "Hey Poppy" wake word
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool
import pvporcupine
import pyaudio
import struct
import numpy as np


class WakeWordNode(Node):
    """Offline wake word detection"""

    def __init__(self):
        super().__init__('wake_word_detection')
        
        # Parameters
        self.declare_parameter('access_key', '')  # Picovoice access key
        self.declare_parameter('keyword', 'hey poppy')
        self.declare_parameter('sensitivity', 0.75)
        
        # Publishers
        self.wake_detected_pub = self.create_publisher(Bool, 'wake_word_detected', 10)
        self.transcript_pub = self.create_publisher(String, 'voice/transcript', 10)
        
        # Initialize Porcupine
        access_key = self.get_parameter('access_key').value
        sensitivity = self.get_parameter('sensitivity').value
        
        try:
            # For production, use custom wake word model
            # This is a placeholder using built-in keyword
            self.porcupine = pvporcupine.create(
                access_key=access_key if access_key else None,
                keywords=['porcupine'],  # Replace with custom "hey poppy" model
                sensitivities=[sensitivity]
            )
            
            self.get_logger().info(f'Porcupine initialized with frame length: {self.porcupine.frame_length}')
            
        except Exception as e:
            self.get_logger().error(f'Failed to initialize Porcupine: {e}')
            self.porcupine = None
            return
        
        # Audio setup
        self.pa = pyaudio.PyAudio()
        
        try:
            self.audio_stream = self.pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )
            
            self.get_logger().info('Audio stream opened')
            
        except Exception as e:
            self.get_logger().error(f'Failed to open audio stream: {e}')
            self.audio_stream = None
            return
        
        # Timer for audio processing
        # Calculate timer period based on frame length and sample rate
        timer_period = self.porcupine.frame_length / self.porcupine.sample_rate
        self.create_timer(timer_period, self.process_audio)
        
        self.get_logger().info('Wake word detection ready - listening for "Hey Poppy"')
        
    def process_audio(self):
        """Process audio frames for wake word detection"""
        if not self.porcupine or not self.audio_stream:
            return
            
        try:
            # Read audio frame
            pcm = self.audio_stream.read(self.porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
            
            # Process with Porcupine
            keyword_index = self.porcupine.process(pcm)
            
            if keyword_index >= 0:
                # Wake word detected!
                self.get_logger().info('🎙️  Wake word detected!')
                
                # Publish wake event
                wake_msg = Bool()
                wake_msg.data = True
                self.wake_detected_pub.publish(wake_msg)
                
                # Trigger voice assistant (would connect to Google Assistant)
                self.handle_wake_word()
                
        except Exception as e:
            self.get_logger().error(f'Error processing audio: {e}')
            
    def handle_wake_word(self):
        """Handle wake word detection - trigger user location scan"""
        # In production, this would:
        # 1. Trigger 360° camera scan
        # 2. Locate user
        # 3. Activate Google Assistant
        # 4. Process voice command
        
        self.get_logger().info('Initiating user location scan...')
        
        # Publish event for other nodes to handle
        msg = String()
        msg.data = 'wake_word_detected'
        self.transcript_pub.publish(msg)
        
    def destroy_node(self):
        """Cleanup on shutdown"""
        if self.audio_stream:
            self.audio_stream.close()
        if self.pa:
            self.pa.terminate()
        if self.porcupine:
            self.porcupine.delete()
            
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = WakeWordNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
