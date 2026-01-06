#!/usr/bin/env python3
"""
Poppy Robot - Advanced Facial Detection System
Optimized for complex lighting conditions with 2025 edge AI technology
"""

import cv2
import numpy as np
import tensorflow as tf
from tensorflow.lite.python.interpreter import Interpreter
import threading
import time
import queue
from collections import deque
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedFaceDetection:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = None
        self.is_running = False
        
        # Performance monitoring
        self.fps_counter = 0
        self.last_fps_time = time.time()
        self.processing_times = deque(maxlen=30)
        
        # Lighting adaptation
        self.lighting_history = deque(maxlen=10)
        self.adaptive_threshold = 0.5
        self.lighting_mode = "AUTO"  # AUTO, BRIGHT, DARK, MIXED
        
        # Multi-scale detection
        self.scale_factors = [1.1, 1.2, 1.3, 1.4]
        self.min_neighbors = [3, 4, 5, 6]
        
        # Initialize models
        self.load_models()
        
        # Initialize camera
        self.init_camera()
        
    def load_models(self):
        """Load optimized models for different lighting conditions"""
        try:
            # Primary face detection model (TensorFlow Lite)
            self.face_model = Interpreter(model_path="models/face_detection_quantized.tflite")
            self.face_model.allocate_tensors()
            
            # Lighting classification model
            self.lighting_model = Interpreter(model_path="models/lighting_classifier.tflite")
            self.lighting_model.allocate_tensors()
            
            # Fallback OpenCV cascade
            self.face_cascade = cv2.CascadeClassifier("face.xml")
            
            logger.info("[OK] AI models loaded successfully")
            
        except Exception as e:
            logger.warning(f"Could not load AI models: {e}")
            logger.info("Falling back to OpenCV cascade classifier")
            self.face_model = None
            self.lighting_model = None
            self.face_cascade = cv2.CascadeClassifier("face.xml")
    
    def init_camera(self):
        """Initialize camera with optimal settings"""
        self.cap = cv2.VideoCapture(self.camera_index)
        
        if not self.cap.isOpened():
            raise Exception("Could not open camera")
        
        # Optimize camera settings for face detection
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, 0.5)
        self.cap.set(cv2.CAP_PROP_CONTRAST, 0.5)
        self.cap.set(cv2.CAP_PROP_SATURATION, 0.5)
        
        logger.info("[OK] Camera initialized with optimized settings")
    
    def analyze_lighting_conditions(self, frame):
        """Analyze lighting conditions and adapt detection parameters"""
        # Convert to different color spaces for analysis
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Calculate lighting metrics
        brightness = np.mean(gray)
        contrast = np.std(gray)
        saturation = np.mean(hsv[:, :, 1])
        
        # Store lighting history
        lighting_data = {
            'brightness': brightness,
            'contrast': contrast,
            'saturation': saturation,
            'timestamp': time.time()
        }
        self.lighting_history.append(lighting_data)
        
        # Classify lighting conditions
        if brightness > 150 and contrast > 50:
            self.lighting_mode = "BRIGHT"
        elif brightness < 80 and contrast < 30:
            self.lighting_mode = "DARK"
        elif contrast > 60 and saturation > 100:
            self.lighting_mode = "MIXED"
        else:
            self.lighting_mode = "AUTO"
        
        # Adjust adaptive threshold based on lighting
        if self.lighting_mode == "DARK":
            self.adaptive_threshold = 0.3
        elif self.lighting_mode == "BRIGHT":
            self.adaptive_threshold = 0.7
        else:
            self.adaptive_threshold = 0.5
        
        return lighting_data
    
    def preprocess_frame(self, frame):
        """Preprocess frame based on lighting conditions"""
        # Apply lighting compensation
        if self.lighting_mode == "DARK":
            # Enhance brightness and contrast for dark conditions
            frame = cv2.convertScaleAbs(frame, alpha=1.2, beta=30)
            # Apply CLAHE for better contrast
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            enhanced = clahe.apply(gray)
            frame = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
            
        elif self.lighting_mode == "BRIGHT":
            # Reduce brightness and enhance contrast for bright conditions
            frame = cv2.convertScaleAbs(frame, alpha=0.8, beta=-20)
            
        elif self.lighting_mode == "MIXED":
            # Apply adaptive histogram equalization
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            lab[:, :, 0] = clahe.apply(lab[:, :, 0])
            frame = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        return frame
    
    def detect_faces_ai(self, frame):
        """Detect faces using TensorFlow Lite model"""
        if self.face_model is None:
            return self.detect_faces_opencv(frame)
        
        try:
            # Preprocess frame for AI model
            input_details = self.face_model.get_input_details()
            output_details = self.face_model.get_output_details()
            
            # Resize and normalize frame
            input_shape = input_details[0]['shape']
            resized = cv2.resize(frame, (input_shape[2], input_shape[1]))
            input_data = np.expand_dims(resized, axis=0).astype(np.uint8)
            
            # Run inference
            self.face_model.set_tensor(input_details[0]['index'], input_data)
            self.face_model.invoke()
            
            # Get results
            boxes = self.face_model.get_tensor(output_details[0]['index'])
            scores = self.face_model.get_tensor(output_details[2]['index'])
            
            # Filter faces with confidence above adaptive threshold
            faces = []
            for i in range(len(scores[0])):
                if scores[0][i] > self.adaptive_threshold:
                    box = boxes[0][i]
                    h, w = frame.shape[:2]
                    x1 = int(box[1] * w)
                    y1 = int(box[0] * h)
                    x2 = int(box[3] * w)
                    y2 = int(box[2] * h)
                    faces.append((x1, y1, x2-x1, y2-y1))
            
            return faces
            
        except Exception as e:
            logger.error(f"AI face detection failed: {e}")
            return self.detect_faces_opencv(frame)
    
    def detect_faces_opencv(self, frame):
        """Fallback face detection using OpenCV with multi-scale approach"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        all_faces = []
        
        # Try different scale factors and min neighbors based on lighting
        if self.lighting_mode == "DARK":
            scale_factors = [1.05, 1.1, 1.15]
            min_neighbors = [2, 3, 4]
        elif self.lighting_mode == "BRIGHT":
            scale_factors = [1.2, 1.3, 1.4]
            min_neighbors = [4, 5, 6]
        else:
            scale_factors = [1.1, 1.2, 1.3]
            min_neighbors = [3, 4, 5]
        
        for scale in scale_factors:
            for neighbors in min_neighbors:
                faces = self.face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=scale,
                    minNeighbors=neighbors,
                    minSize=(30, 30),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                all_faces.extend(faces)
        
        # Remove duplicate detections
        return self.remove_duplicate_faces(all_faces)
    
    def remove_duplicate_faces(self, faces):
        """Remove duplicate face detections using NMS"""
        if len(faces) == 0:
            return faces
        
        # Convert to format for NMS
        boxes = []
        scores = []
        
        for (x, y, w, h) in faces:
            boxes.append([x, y, x+w, y+h])
            scores.append(1.0)  # All have same confidence in OpenCV
        
        # Apply Non-Maximum Suppression
        indices = cv2.dnn.NMSBoxes(boxes, scores, 0.5, 0.4)
        
        if len(indices) == 0:
            return []
        
        # Return filtered faces
        filtered_faces = []
        for i in indices.flatten():
            x, y, x2, y2 = boxes[i]
            filtered_faces.append((x, y, x2-x, y2-y))
        
        return filtered_faces
    
    def detect_faces(self, frame):
        """Main face detection function with lighting adaptation"""
        start_time = time.time()
        
        # Analyze lighting conditions
        lighting_data = self.analyze_lighting_conditions(frame)
        
        # Preprocess frame based on lighting
        processed_frame = self.preprocess_frame(frame)
        
        # Detect faces using AI model
        faces = self.detect_faces_ai(processed_frame)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        self.processing_times.append(processing_time)
        
        # Update FPS counter
        self.fps_counter += 1
        if time.time() - self.last_fps_time >= 1.0:
            fps = self.fps_counter / (time.time() - self.last_fps_time)
            logger.info(f"Face Detection FPS: {fps:.1f}, Lighting: {self.lighting_mode}")
            self.fps_counter = 0
            self.last_fps_time = time.time()
        
        return {
            'faces': faces,
            'lighting_mode': self.lighting_mode,
            'lighting_data': lighting_data,
            'processing_time': processing_time,
            'avg_processing_time': np.mean(self.processing_times) if self.processing_times else 0
        }
    
    def draw_detections(self, frame, detection_result):
        """Draw face detections on frame with lighting information"""
        faces = detection_result['faces']
        lighting_mode = detection_result['lighting_mode']
        
        # Draw face rectangles
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, "Face", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # Draw lighting information
        cv2.putText(frame, f"Lighting: {lighting_mode}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Faces: {len(faces)}", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"FPS: {1.0/detection_result['avg_processing_time']:.1f}", (10, 90), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return frame
    
    def start_detection(self):
        """Start face detection in a separate thread"""
        self.is_running = True
        detection_thread = threading.Thread(target=self._detection_loop)
        detection_thread.daemon = True
        detection_thread.start()
        return detection_thread
    
    def _detection_loop(self):
        """Main detection loop"""
        while self.is_running:
            ret, frame = self.cap.read()
            if not ret:
                logger.error("Failed to read frame from camera")
                continue
            
            # Detect faces
            detection_result = self.detect_faces(frame)
            
            # Draw detections
            frame_with_detections = self.draw_detections(frame, detection_result)
            
            # Display frame
            cv2.imshow('Poppy Face Detection', frame_with_detections)
            
            # Check for exit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        self.is_running = False
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        logger.info("Face detection system cleaned up")
    
    def get_detection_stats(self):
        """Get performance statistics"""
        return {
            'fps': self.fps_counter,
            'avg_processing_time': np.mean(self.processing_times) if self.processing_times else 0,
            'lighting_mode': self.lighting_mode,
            'is_running': self.is_running
        }

# Example usage
if __name__ == "__main__":
    try:
        face_detector = AdvancedFaceDetection()
        detection_thread = face_detector.start_detection()
        detection_thread.join()
    except KeyboardInterrupt:
        logger.info("Face detection stopped by user")
    except Exception as e:
        logger.error(f"Face detection error: {e}")
