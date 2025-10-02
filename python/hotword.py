#!/usr/bin/env python

# Copyright (C) 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#	 http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Edge AI Processing for Real-time Machine Vision

from __future__ import print_function

import argparse
import json
import os.path
import pathlib2 as pathlib
import numpy as np
import cv2
import tensorflow as tf
from tensorflow.lite.python.interpreter import Interpreter
import threading
import time
import queue

import google.oauth2.credentials

from google.assistant.library import Assistant
from google.assistant.library.event import EventType
from google.assistant.library.file_helpers import existing_file
from google.assistant.library.device_helpers import register_device

# Import advanced face detection system
from advanced_face_detection import AdvancedFaceDetection

###################POPPY - Enhanced Edge AI######################
from websocket import create_connection

# Global variables for edge AI processing
ws = None
pic = ()
frames = queue.Queue(1)
connection_retry_count = 0
max_retries = 5

def connect_websocket():
	"""Establish WebSocket connection with retry logic."""
	global ws, connection_retry_count
	try:
		ws = create_connection("ws://localhost:9999/socket/", timeout=5)
		connection_retry_count = 0
		print("✓ WebSocket connected to Poppy control system")
		return True
	except Exception as e:
		connection_retry_count += 1
		print(f" WebSocket connection failed (attempt {connection_retry_count}): {e}")
		if connection_retry_count < max_retries:
			print(f" Retrying in 5 seconds...")
			time.sleep(5)
			return connect_websocket()
		else:
			print(" Max retries reached. WebSocket connection failed.")
			return False

def safe_ws_send(message):
	"""Safely send message via WebSocket with error handling."""
	global ws
	try:
		if ws is None:
			if not connect_websocket():
				print(" Cannot send message - no WebSocket connection")
				return False
		ws.send(message)
		return True
	except Exception as e:
		print(f" WebSocket send failed: {e}")
		ws = None
		return False

# Enhanced Vision Processing with Advanced Face Detection
class EnhancedVisionProcessor:
	def __init__(self):
		# Initialize advanced face detection system
		self.face_detector = AdvancedFaceDetection()
		
		# Performance metrics
		self.processing_times = []
		self.frame_count = 0
		
		# Obstacle detection (simplified for integration)
		self.obstacle_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")  # Fallback
		
		print("✓ Enhanced Vision Processor initialized with advanced face detection")
	
	def detect_faces(self, frame):
		"""Detect faces using advanced face detection system"""
		try:
			detection_result = self.face_detector.detect_faces(frame)
			return detection_result['faces']
		except Exception as e:
			print(f"Advanced face detection failed: {e}")
			# Fallback to simple OpenCV
			gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
			return self.obstacle_cascade.detectMultiScale(gray, 1.1, 4)
	
	def detect_obstacles(self, frame):
		"""Detect obstacles using traditional computer vision"""
		try:
			gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
			edges = cv2.Canny(gray, 50, 150)
			contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
			
			obstacles = []
			for contour in contours:
				area = cv2.contourArea(contour)
				if area > 1000:  # Filter small contours
					x, y, w, h = cv2.boundingRect(contour)
					obstacles.append((x, y, w, h))
			
			return obstacles
		except Exception as e:
			print(f"Obstacle detection failed: {e}")
			return []
	
	def detect_edges(self, frame):
		"""Detect surface edges for navigation safety"""
		try:
			gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
			blurred = cv2.GaussianBlur(gray, (5, 5), 0)
			edges = cv2.Canny(blurred, 50, 150)
			
			# Detect horizontal lines (potential surface edges)
			lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=100, maxLineGap=10)
			
			edge_lines = []
			if lines is not None:
				for line in lines:
					x1, y1, x2, y2 = line[0]
					# Check if line is roughly horizontal
					if abs(y2 - y1) < 20:
						edge_lines.append((x1, y1, x2, y2))
			
			return edge_lines
		except Exception as e:
			print(f"Edge detection failed: {e}")
			return []
	
	def process_frame(self, frame):
		"""Main processing function for each frame"""
		start_time = time.time()
		
		try:
			# Use advanced face detection
			detection_result = self.face_detector.detect_faces(frame)
			faces = detection_result['faces']
			lighting_mode = detection_result['lighting_mode']
			processing_time = detection_result['processing_time']
		except Exception as e:
			print(f"Advanced processing failed: {e}")
			# Fallback processing
			faces = self.detect_faces(frame)
			lighting_mode = "UNKNOWN"
			processing_time = time.time() - start_time
		
		# Detect obstacles and edges
		obstacles = self.detect_obstacles(frame)
		edges = self.detect_edges(frame)
		
		# Update performance metrics
		self.processing_times.append(processing_time)
		self.frame_count += 1
		
		# Keep only last 100 processing times for average
		if len(self.processing_times) > 100:
			self.processing_times = self.processing_times[-100:]
		
		return {
			'faces': faces,
			'obstacles': obstacles,
			'edges': edges,
			'lighting_mode': lighting_mode,
			'processing_time': processing_time,
			'avg_processing_time': np.mean(self.processing_times) if self.processing_times else 0
		}
	
	def get_detection_stats(self):
		"""Get detection performance statistics"""
		return self.face_detector.get_detection_stats()

# Initialize enhanced vision processor
vision_processor = EnhancedVisionProcessor()

class StartCameraStream(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.cam = cv2.VideoCapture(0)
		# Optimize camera settings for better performance
		self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
		self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
		self.cam.set(cv2.CAP_PROP_FPS, 30)
		self.cam.set(cv2.CAP_PROP_BRIGHTNESS, 0.5)
		self.cam.set(cv2.CAP_PROP_CONTRAST, 0.5)
		self.cam.set(cv2.CAP_PROP_SATURATION, 0.5)

	def run(self):
		global frames, pic
		while True:
			ret, frame = self.cam.read()
			if ret:
				pic = frame
				# Process frame with enhanced vision processor
				results = vision_processor.process_frame(frame)
				frames.put((frame, results))
			time.sleep(0.033)  # ~30 FPS
			
##############################################

try:
	FileNotFoundError
except NameError:
	FileNotFoundError = IOError


WARNING_NOT_REGISTERED = """
	This device is not registered. This means you will not be able to use
	Device Actions or see your device in Assistant Settings. In order to
	register this device follow instructions at:

	https://developers.google.com/assistant/sdk/guides/library/python/embed/register-device
"""


def process_event(event):
	"""Enhanced event processing with better error handling and logging.

	Prints all events that occur with two spaces between each new
	conversation and a single space between turns of a conversation.

	Args:
		event(event.Event): The current event to process.
	"""
	if event.type == EventType.ON_CONVERSATION_TURN_STARTED:
		print()
		print("✓ Conversation started")

	print(event)

	if (event.type == EventType.ON_CONVERSATION_TURN_FINISHED and
			event.args and not event.args['with_follow_on_turn']):
		print()
		print("✓ Conversation finished")
	
	if event.type == EventType.ON_DEVICE_ACTION:
		print("✓ Device action received:")
		for command, params in event.actions:
			print(f"  Command: {command}")
			print(f"  Params: {params}")
			# Process specific commands for Poppy
			process_poppy_command(command, params)
	
	if event.type == EventType.ON_RECOGNIZING_SPEECH_FINISHED:
		print(f"✓ Speech recognized: {event.args['text']}")
	
	if event.type == EventType.ON_RESPONDING_STARTED:
		print("💭 Assistant responding...")
	
	if event.type == EventType.ON_RESPONDING_FINISHED:
		print("✓ Response complete")

def process_poppy_command(command, params):
	"""Process specific commands for Poppy robot control."""
	try:
		if command == "move_forward":
			distance = params.get('distance', 0.1)
			if safe_ws_send(f"move,{distance}"):
				print(f"Moving forward {distance}m")
		
		elif command == "turn_left":
			angle = params.get('angle', 5)
			if safe_ws_send(f"turn,{angle}"):
				print(f"Turning left {angle}°")
		
		elif command == "turn_right":
			angle = params.get('angle', 5)
			if safe_ws_send(f"turn,-{angle}"):
				print(f"Turning right {angle}°")
		
		elif command == "stop":
			safe_ws_send("move,0")
			safe_ws_send("turn,0")
			print("Stopping")
		
		elif command == "find_face":
			print("Starting face search...")
			# This will be handled in the main event loop
		
		elif command == "status":
			print("Poppy status: Active and ready")
			# Could send status request to robot
		
		else:
			print(f"Unknown command: {command}")
	
	except Exception as e:
		print(f"Error processing command {command}: {e}")


def main():
	global pic
	parser = argparse.ArgumentParser(
		formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('--device-model-id', '--device_model_id', type=str,
						metavar='DEVICE_MODEL_ID', required=False,
						help='the device model ID registered with Google')
	parser.add_argument('--project-id', '--project_id', type=str,
						metavar='PROJECT_ID', required=False,
						help='the project ID used to register this device')
	parser.add_argument('--device-config', type=str,
						metavar='DEVICE_CONFIG_FILE',
						default=os.path.join(
							os.path.expanduser('~/.config'),
							'googlesamples-assistant',
							'device_config_library.json'
						),
						help='path to store and read device configuration')
	parser.add_argument('--credentials', type=existing_file,
						metavar='OAUTH2_CREDENTIALS_FILE',
						default=os.path.join(
							os.path.expanduser('~/.config'),
							'google-oauthlib-tool',
							'credentials.json'
						),
						help='path to store and read OAuth2 credentials')
	parser.add_argument('-v', '--version', action='version',
						version='%(prog)s ' + Assistant.__version_str__())

	args = parser.parse_args()
	with open(args.credentials, 'r') as f:
		credentials = google.oauth2.credentials.Credentials(token=None,
															**json.load(f))

	device_model_id = None
	last_device_id = None
	try:
		with open(args.device_config) as f:
			device_config = json.load(f)
			device_model_id = device_config['model_id']
			last_device_id = device_config.get('last_device_id', None)
	except FileNotFoundError:
		pass

	if not args.device_model_id and not device_model_id:
		raise Exception('Missing --device-model-id option')

	# Re-register if "device_model_id" is given by the user and it differs
	# from what we previously registered with.
	should_register = (
		args.device_model_id and args.device_model_id != device_model_id)

	device_model_id = args.device_model_id or device_model_id

	# Initialize WebSocket connection
	if not connect_websocket():
		print(" Warning: WebSocket connection failed. Some features may not work.")

	with Assistant(credentials, device_model_id) as assistant:
		events = assistant.start()

		device_id = assistant.device_id
		print('device_model_id:', device_model_id)
		print('device_id:', device_id + '\n')
		print("✓ Google Assistant ready. Say 'Hey Google' to start!")

		# Re-register if "device_id" is different from the last "device_id":
		if should_register or (device_id != last_device_id):
			if args.project_id:
				register_device(args.project_id, credentials,
								device_model_id, device_id)
				pathlib.Path(os.path.dirname(args.device_config)).mkdir(
					exist_ok=True)
				with open(args.device_config, 'w') as f:
					json.dump({
						'last_device_id': device_id,
						'model_id': device_model_id,
					}, f)
			else:
				print(WARNING_NOT_REGISTERED)

				for event in events:
					if event.type == EventType.ON_CONVERSATION_TURN_STARTED:
						print("✓ AI Face Detection Started")
						run = True
						search_count = 0
						max_search_attempts = 50  # Prevent infinite search
						
						while run and search_count < max_search_attempts:
							if not frames.empty():
								frame, results = frames.get()
								
								# Use enhanced vision processing with lighting adaptation
								faces = results['faces']
								obstacles = results['obstacles']
								edges = results['edges']
								lighting_mode = results['lighting_mode']
								
								print(f"🔍 Enhanced AI Processing - Faces: {len(faces)}, Obstacles: {len(obstacles)}, Edges: {len(edges)}")
								print(f"⚡ Processing Time: {results['processing_time']:.3f}s (Avg: {results['avg_processing_time']:.3f}s)")
								print(f"💡 Lighting Mode: {lighting_mode}")
								
								# Check for obstacles and edges for safety
								if obstacles:
									print(" Obstacles detected - adjusting path")
									safe_ws_send("turn,10")  # Turn away from obstacles
								
								if edges:
									print(" Surface edges detected - avoiding")
									safe_ws_send("move,-0.1")  # Move away from edge
								
								# Look for faces with enhanced detection
								if faces:
									print("✓ Face found with Enhanced AI!")
									# Calculate face position for better tracking
									largest_face = max(faces, key=lambda f: f[2] * f[3])  # Largest face by area
									x, y, w, h = largest_face
									center_x = x + w // 2
									frame_center = frame.shape[1] // 2
									
									# Adjust movement based on face position and lighting
									if center_x < frame_center - 50:
										safe_ws_send("turn,-5")  # Turn left
									elif center_x > frame_center + 50:
										safe_ws_send("turn,5")   # Turn right
									else:
										# Adjust movement speed based on lighting conditions
										if lighting_mode == "DARK":
											safe_ws_send("move,0.1")  # Slower movement in dark
										elif lighting_mode == "BRIGHT":
											safe_ws_send("move,0.3")  # Faster movement in bright light
										else:
											safe_ws_send("move,0.2")  # Normal movement
									
									run = False
									break
								else:
									print("Searching for face...")
									# Adjust search pattern based on lighting
									if lighting_mode == "DARK":
										safe_ws_send("turn,3")  # Slower search in dark
									else:
										safe_ws_send("turn,5")  # Normal search
							
							search_count += 1
							time.sleep(0.1)  # Small delay to prevent excessive CPU usage
						
						if search_count >= max_search_attempts:
							print(" Face search timeout - continuing with conversation")
					
					process_event(event)

			
cameraStream = StartCameraStream()
cameraStream.start()

if __name__ == '__main__':
	main()
	
