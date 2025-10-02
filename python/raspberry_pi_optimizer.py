#!/usr/bin/env python3
"""
Poppy Robot - Raspberry Pi Optimization System
Multi-threading and performance optimization for facial recognition
"""

import os
import sys
import time
import threading
import queue
import psutil
import logging
import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import cv2
import numpy as np
import tensorflow as tf

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    cpu_usage: float
    memory_usage: float
    gpu_usage: float
    temperature: float
    fps: float
    processing_time: float
    timestamp: float

class RaspberryPiOptimizer:
    def __init__(self):
        self.is_running = False
        self.monitoring_thread = None
        self.performance_history = []
        
        # Threading configuration
        self.max_workers = 4
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # Performance monitoring
        self.metrics_queue = queue.Queue(maxsize=100)
        self.optimization_enabled = True
        
        # GPU configuration
        self.gpu_available = self.check_gpu_availability()
        self.configure_gpu()
        
        # Memory management
        self.memory_pool = []
        self.memory_pool_size = 10
        
        # Initialize performance monitoring
        self.init_performance_monitoring()
        
    def check_gpu_availability(self):
        """Check if GPU is available for acceleration"""
        try:
            gpus = tf.config.experimental.list_physical_devices('GPU')
            if gpus:
                logger.info(f"✓ GPU available: {len(gpus)} device(s)")
                return True
            else:
                logger.info("No GPU available, using CPU")
                return False
        except Exception as e:
            logger.warning(f"GPU check failed: {e}")
            return False
    
    def configure_gpu(self):
        """Configure GPU for optimal performance"""
        if not self.gpu_available:
            return
        
        try:
            gpus = tf.config.experimental.list_physical_devices('GPU')
            if gpus:
                # Enable memory growth to avoid allocating all GPU memory
                for gpu in gpus:
                    tf.config.experimental.set_memory_growth(gpu, True)
                
                # Set GPU memory limit (adjust based on available memory)
                tf.config.experimental.set_virtual_device_configuration(
                    gpus[0],
                    [tf.config.experimental.VirtualDeviceConfiguration(memory_limit=2048)]
                )
                
                logger.info("✓ GPU configured for optimal performance")
        except Exception as e:
            logger.error(f"GPU configuration failed: {e}")
    
    def init_performance_monitoring(self):
        """Initialize performance monitoring system"""
        # Set CPU governor to performance mode
        try:
            with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor', 'w') as f:
                f.write('performance')
            logger.info("✓ CPU governor set to performance mode")
        except Exception as e:
            logger.warning(f"Could not set CPU governor: {e}")
        
        # Initialize memory pool
        self.init_memory_pool()
        
        # Configure TensorFlow for optimal performance
        self.configure_tensorflow()
    
    def init_memory_pool(self):
        """Initialize memory pool for efficient memory management"""
        for _ in range(self.memory_pool_size):
            # Pre-allocate memory buffers
            buffer = np.zeros((480, 640, 3), dtype=np.uint8)
            self.memory_pool.append(buffer)
        
        logger.info(f"✓ Memory pool initialized with {self.memory_pool_size} buffers")
    
    def get_memory_buffer(self):
        """Get a memory buffer from the pool"""
        if self.memory_pool:
            return self.memory_pool.pop()
        else:
            # Create new buffer if pool is empty
            return np.zeros((480, 640, 3), dtype=np.uint8)
    
    def return_memory_buffer(self, buffer):
        """Return a memory buffer to the pool"""
        if len(self.memory_pool) < self.memory_pool_size:
            buffer.fill(0)  # Clear the buffer
            self.memory_pool.append(buffer)
    
    def configure_tensorflow(self):
        """Configure TensorFlow for optimal performance"""
        try:
            # Enable mixed precision for better performance
            tf.config.optimizer.set_experimental_options({'auto_mixed_precision': True})
            
            # Set thread count for optimal performance
            tf.config.threading.set_intra_op_parallelism_threads(2)
            tf.config.threading.set_inter_op_parallelism_threads(2)
            
            logger.info("✓ TensorFlow configured for optimal performance")
        except Exception as e:
            logger.warning(f"TensorFlow configuration failed: {e}")
    
    def get_system_metrics(self):
        """Get current system performance metrics"""
        try:
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=0.1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # GPU usage (if available)
            gpu_usage = 0
            if self.gpu_available:
                try:
                    # This would require nvidia-ml-py or similar library
                    # For now, use a placeholder
                    gpu_usage = 0
                except:
                    pass
            
            # Temperature
            temperature = 0
            try:
                with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                    temperature = float(f.read()) / 1000.0
            except:
                pass
            
            return PerformanceMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                gpu_usage=gpu_usage,
                temperature=temperature,
                fps=0,  # Will be set by processing functions
                processing_time=0,  # Will be set by processing functions
                timestamp=time.time()
            )
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return None
    
    def optimize_system_performance(self, metrics: PerformanceMetrics):
        """Optimize system performance based on current metrics"""
        if not self.optimization_enabled:
            return
        
        # CPU optimization
        if metrics.cpu_usage > 80:
            logger.warning("High CPU usage detected, optimizing...")
            self.optimize_cpu_usage()
        
        # Memory optimization
        if metrics.memory_usage > 85:
            logger.warning("High memory usage detected, optimizing...")
            self.optimize_memory_usage()
        
        # Temperature optimization
        if metrics.temperature > 70:
            logger.warning("High temperature detected, throttling...")
            self.throttle_performance()
    
    def optimize_cpu_usage(self):
        """Optimize CPU usage"""
        try:
            # Reduce thread count
            tf.config.threading.set_intra_op_parallelism_threads(1)
            tf.config.threading.set_inter_op_parallelism_threads(1)
            
            # Force garbage collection
            import gc
            gc.collect()
            
            logger.info("CPU usage optimized")
        except Exception as e:
            logger.error(f"CPU optimization failed: {e}")
    
    def optimize_memory_usage(self):
        """Optimize memory usage"""
        try:
            # Clear memory pool
            self.memory_pool.clear()
            self.init_memory_pool()
            
            # Force garbage collection
            import gc
            gc.collect()
            
            logger.info("Memory usage optimized")
        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")
    
    def throttle_performance(self):
        """Throttle performance to reduce temperature"""
        try:
            # Reduce thread count
            tf.config.threading.set_intra_op_parallelism_threads(1)
            tf.config.threading.set_inter_op_parallelism_threads(1)
            
            # Reduce processing frequency
            time.sleep(0.1)
            
            logger.info("Performance throttled due to high temperature")
        except Exception as e:
            logger.error(f"Performance throttling failed: {e}")
    
    def start_monitoring(self):
        """Start performance monitoring"""
        self.is_running = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.is_running = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
        logger.info("Performance monitoring stopped")
    
    def _monitoring_loop(self):
        """Main performance monitoring loop"""
        while self.is_running:
            try:
                metrics = self.get_system_metrics()
                if metrics:
                    self.performance_history.append(metrics)
                    self.optimize_system_performance(metrics)
                    
                    # Keep only last 1000 entries
                    if len(self.performance_history) > 1000:
                        self.performance_history = self.performance_history[-1000:]
                
                time.sleep(1)  # Monitor every second
                
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                time.sleep(5)
    
    def process_frame_async(self, frame, callback: Callable):
        """Process frame asynchronously using thread pool"""
        future = self.executor.submit(self._process_frame, frame)
        future.add_done_callback(callback)
        return future
    
    def _process_frame(self, frame):
        """Process frame with performance monitoring"""
        start_time = time.time()
        
        # Get memory buffer from pool
        buffer = self.get_memory_buffer()
        
        try:
            # Copy frame to buffer
            np.copyto(buffer, frame)
            
            # Process frame (placeholder for actual processing)
            processed_frame = self.process_frame_internal(buffer)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Update performance metrics
            self.update_processing_metrics(processing_time)
            
            return processed_frame
            
        finally:
            # Return buffer to pool
            self.return_memory_buffer(buffer)
    
    def process_frame_internal(self, frame):
        """Advanced frame processing with latest AI and computer vision technologies"""
        try:
            # Initialize processing pipeline if not already done
            if not hasattr(self, 'processing_pipeline'):
                self._init_processing_pipeline()
            
            # Preprocessing optimization
            processed_frame = self._preprocess_frame(frame)
            
            # Multi-stage processing pipeline
            results = {}
            
            # Stage 1: Face detection using optimized OpenCV DNN
            if hasattr(self, 'face_detector'):
                results['faces'] = self._detect_faces_dnn(processed_frame)
            
            # Stage 2: Object detection using TensorFlow Lite
            if hasattr(self, 'object_detector'):
                results['objects'] = self._detect_objects_tflite(processed_frame)
            
            # Stage 3: Edge detection and spatial analysis
            results['edges'] = self._detect_edges_optimized(processed_frame)
            
            # Stage 4: Motion detection
            results['motion'] = self._detect_motion(processed_frame)
            
            # Stage 5: Lighting analysis
            results['lighting'] = self._analyze_lighting(processed_frame)
            
            # Post-processing and optimization
            final_frame = self._postprocess_frame(processed_frame, results)
            
            # Store results for external access
            self.last_processing_results = results
            
            return final_frame
            
        except Exception as e:
            logger.error(f"Frame processing error: {e}")
            return frame
    
    def _init_processing_pipeline(self):
        """Initialize the processing pipeline with latest technologies"""
        try:
            # Initialize OpenCV DNN face detector
            self._init_face_detector()
            
            # Initialize TensorFlow Lite object detector
            self._init_object_detector()
            
            # Initialize motion detection
            self._init_motion_detection()
            
            # Initialize lighting analysis
            self._init_lighting_analysis()
            
            self.processing_pipeline = True
            logger.info("Advanced processing pipeline initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize processing pipeline: {e}")
    
    def _init_face_detector(self):
        """Initialize optimized OpenCV DNN face detector"""
        try:
            # Use OpenCV DNN with optimized model
            model_path = "models/opencv_face_detector_uint8.pb"
            config_path = "models/opencv_face_detector.pbtxt"
            
            # Check if model files exist, otherwise use Haar cascade as fallback
            if os.path.exists(model_path) and os.path.exists(config_path):
                self.face_detector = cv2.dnn.readNetFromTensorflow(model_path, config_path)
                self.face_detection_method = "dnn"
                logger.info("DNN face detector initialized")
            else:
                # Fallback to Haar cascade
                self.face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                self.face_detection_method = "haar"
                logger.info("Haar cascade face detector initialized (fallback)")
                
        except Exception as e:
            logger.warning(f"Face detector initialization failed: {e}")
            self.face_detector = None
    
    def _init_object_detector(self):
        """Initialize TensorFlow Lite object detector"""
        try:
            # Load TensorFlow Lite model
            model_path = "models/ssd_mobilenet_v2.tflite"
            
            if os.path.exists(model_path):
                self.object_detector = tf.lite.Interpreter(model_path=model_path)
                self.object_detector.allocate_tensors()
                
                # Get input and output details
                self.input_details = self.object_detector.get_input_details()
                self.output_details = self.object_detector.get_output_details()
                
                # COCO class labels
                self.class_labels = self._load_coco_labels()
                
                logger.info("TensorFlow Lite object detector initialized")
            else:
                logger.warning("Object detector model not found, skipping initialization")
                self.object_detector = None
                
        except Exception as e:
            logger.warning(f"Object detector initialization failed: {e}")
            self.object_detector = None
    
    def _init_motion_detection(self):
        """Initialize motion detection system"""
        try:
            # Initialize background subtractor with optimized parameters
            self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
                history=500, varThreshold=50, detectShadows=True
            )
            
            # Initialize optical flow for motion tracking
            self.optical_flow_params = dict(
                winSize=(15, 15),
                maxLevel=2,
                criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)
            )
            
            # Previous frame for motion detection
            self.prev_frame = None
            self.prev_gray = None
            
            logger.info("Motion detection system initialized")
            
        except Exception as e:
            logger.error(f"Motion detection initialization failed: {e}")
            self.bg_subtractor = None
    
    def _init_lighting_analysis(self):
        """Initialize lighting analysis system"""
        try:
            # Initialize lighting analysis parameters
            self.lighting_thresholds = {
                'dark': 50,
                'normal': 120,
                'bright': 200
            }
            
            # Histogram analysis parameters
            self.hist_bins = 256
            self.hist_range = [0, 256]
            
            logger.info("Lighting analysis system initialized")
            
        except Exception as e:
            logger.error(f"Lighting analysis initialization failed: {e}")
    
    def update_processing_metrics(self, processing_time: float):
        """Update processing performance metrics"""
        try:
            # Calculate FPS
            fps = 1.0 / processing_time if processing_time > 0 else 0
            
            # Update latest metrics
            if self.performance_history:
                latest_metrics = self.performance_history[-1]
                latest_metrics.fps = fps
                latest_metrics.processing_time = processing_time
        except Exception as e:
            logger.error(f"Failed to update processing metrics: {e}")
    
    def _preprocess_frame(self, frame):
        """Optimized frame preprocessing"""
        try:
            # Resize frame for optimal processing (maintain aspect ratio)
            height, width = frame.shape[:2]
            if width > 640:  # Limit width for performance
                scale = 640 / width
                new_width = 640
                new_height = int(height * scale)
                frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            # Convert to different color spaces for different processing stages
            self.frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            return frame
            
        except Exception as e:
            logger.error(f"Frame preprocessing error: {e}")
            return frame
    
    def _detect_faces_dnn(self, frame):
        """Detect faces using OpenCV DNN"""
        try:
            if not self.face_detector:
                return []
            
            faces = []
            
            if self.face_detection_method == "dnn":
                # DNN-based detection
                blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300), [104, 117, 123])
                self.face_detector.setInput(blob)
                detections = self.face_detector.forward()
                
                h, w = frame.shape[:2]
                for i in range(detections.shape[2]):
                    confidence = detections[0, 0, i, 2]
                    if confidence > 0.5:  # Confidence threshold
                        x1 = int(detections[0, 0, i, 3] * w)
                        y1 = int(detections[0, 0, i, 4] * h)
                        x2 = int(detections[0, 0, i, 5] * w)
                        y2 = int(detections[0, 0, i, 6] * h)
                        faces.append((x1, y1, x2-x1, y2-y1, confidence))
            
            else:
                # Haar cascade detection
                faces = self.face_detector.detectMultiScale(
                    self.frame_gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
                )
                # Convert to (x, y, w, h, confidence) format
                faces = [(x, y, w, h, 1.0) for x, y, w, h in faces]
            
            return faces
            
        except Exception as e:
            logger.error(f"Face detection error: {e}")
            return []
    
    def _detect_objects_tflite(self, frame):
        """Detect objects using TensorFlow Lite"""
        try:
            if not self.object_detector:
                return []
            
            # Prepare input
            input_shape = self.input_details[0]['shape']
            input_height, input_width = input_shape[1], input_shape[2]
            
            # Resize frame to model input size
            resized_frame = cv2.resize(frame, (input_width, input_height))
            input_data = np.expand_dims(resized_frame, axis=0).astype(np.uint8)
            
            # Run inference
            self.object_detector.set_tensor(self.input_details[0]['index'], input_data)
            self.object_detector.invoke()
            
            # Get results
            boxes = self.object_detector.get_tensor(self.output_details[0]['index'])
            classes = self.object_detector.get_tensor(self.output_details[1]['index'])
            scores = self.object_detector.get_tensor(self.output_details[2]['index'])
            num_detections = self.object_detector.get_tensor(self.output_details[3]['index'])
            
            # Process detections
            objects = []
            h, w = frame.shape[:2]
            
            for i in range(int(num_detections[0])):
                if scores[0][i] > 0.5:  # Confidence threshold
                    class_id = int(classes[0][i])
                    class_name = self.class_labels.get(class_id, f"Class_{class_id}")
                    
                    # Convert normalized coordinates to pixel coordinates
                    y1, x1, y2, x2 = boxes[0][i]
                    x1 = int(x1 * w)
                    y1 = int(y1 * h)
                    x2 = int(x2 * w)
                    y2 = int(y2 * h)
                    
                    objects.append({
                        'class': class_name,
                        'confidence': float(scores[0][i]),
                        'bbox': (x1, y1, x2-x1, y2-y1)
                    })
            
            return objects
            
        except Exception as e:
            logger.error(f"Object detection error: {e}")
            return []
    
    def _detect_edges_optimized(self, frame):
        """Optimized edge detection using multiple algorithms"""
        try:
            # Multi-scale edge detection
            edges = []
            
            # Canny edge detection with adaptive thresholds
            gray = self.frame_gray
            median = np.median(gray)
            lower = int(max(0, 0.7 * median))
            upper = int(min(255, 1.3 * median))
            
            canny_edges = cv2.Canny(gray, lower, upper)
            edges.append(('canny', canny_edges))
            
            # Laplacian edge detection
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            laplacian_edges = np.uint8(np.absolute(laplacian))
            edges.append(('laplacian', laplacian_edges))
            
            # Sobel edge detection
            sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            sobel_edges = np.sqrt(sobel_x**2 + sobel_y**2)
            sobel_edges = np.uint8(sobel_edges / sobel_edges.max() * 255)
            edges.append(('sobel', sobel_edges))
            
            return edges
            
        except Exception as e:
            logger.error(f"Edge detection error: {e}")
            return []
    
    def _detect_motion(self, frame):
        """Detect motion using background subtraction and optical flow"""
        try:
            if not self.bg_subtractor:
                return {'motion_detected': False, 'motion_areas': []}
            
            motion_info = {'motion_detected': False, 'motion_areas': []}
            
            # Background subtraction
            fg_mask = self.bg_subtractor.apply(frame)
            
            # Morphological operations to reduce noise
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
            
            # Find contours of moving objects
            contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 500:  # Minimum area threshold
                    x, y, w, h = cv2.boundingRect(contour)
                    motion_info['motion_areas'].append((x, y, w, h))
                    motion_info['motion_detected'] = True
            
            # Optical flow analysis
            if self.prev_gray is not None:
                flow = cv2.calcOpticalFlowPyrLK(
                    self.prev_gray, self.frame_gray, 
                    self._get_good_features(), None, **self.optical_flow_params
                )
                
                if flow[0] is not None and len(flow[0]) > 0:
                    motion_info['optical_flow'] = flow[0]
            
            # Update previous frame
            self.prev_gray = self.frame_gray.copy()
            
            return motion_info
            
        except Exception as e:
            logger.error(f"Motion detection error: {e}")
            return {'motion_detected': False, 'motion_areas': []}
    
    def _analyze_lighting(self, frame):
        """Analyze lighting conditions in the frame"""
        try:
            # Calculate mean brightness
            mean_brightness = np.mean(self.frame_gray)
            
            # Calculate histogram
            hist = cv2.calcHist([self.frame_gray], [0], None, [self.hist_bins], self.hist_range)
            
            # Determine lighting condition
            if mean_brightness < self.lighting_thresholds['dark']:
                lighting_condition = 'dark'
            elif mean_brightness < self.lighting_thresholds['bright']:
                lighting_condition = 'normal'
            else:
                lighting_condition = 'bright'
            
            # Calculate contrast
            contrast = np.std(self.frame_gray)
            
            # Detect overexposure/underexposure
            overexposed = np.sum(hist[-10:]) / np.sum(hist) > 0.1
            underexposed = np.sum(hist[:10]) / np.sum(hist) > 0.1
            
            return {
                'condition': lighting_condition,
                'brightness': float(mean_brightness),
                'contrast': float(contrast),
                'overexposed': overexposed,
                'underexposed': underexposed,
                'histogram': hist.flatten().tolist()
            }
            
        except Exception as e:
            logger.error(f"Lighting analysis error: {e}")
            return {'condition': 'unknown', 'brightness': 0, 'contrast': 0}
    
    def _postprocess_frame(self, frame, results):
        """Post-process frame with results overlay"""
        try:
            # Create output frame
            output_frame = frame.copy()
            
            # Draw face detection results
            if 'faces' in results:
                for face in results['faces']:
                    x, y, w, h, confidence = face
                    cv2.rectangle(output_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(output_frame, f"Face: {confidence:.2f}", 
                              (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # Draw object detection results
            if 'objects' in results:
                for obj in results['objects']:
                    x, y, w, h = obj['bbox']
                    cv2.rectangle(output_frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                    cv2.putText(output_frame, f"{obj['class']}: {obj['confidence']:.2f}", 
                              (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
            
            # Draw motion detection results
            if 'motion' in results and results['motion']['motion_detected']:
                for area in results['motion']['motion_areas']:
                    x, y, w, h = area
                    cv2.rectangle(output_frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                    cv2.putText(output_frame, "Motion", (x, y-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            
            # Add lighting information
            if 'lighting' in results:
                lighting = results['lighting']
                cv2.putText(output_frame, f"Lighting: {lighting['condition']}", 
                          (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(output_frame, f"Brightness: {lighting['brightness']:.1f}", 
                          (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            return output_frame
            
        except Exception as e:
            logger.error(f"Post-processing error: {e}")
            return frame
    
    def _get_good_features(self):
        """Get good features for optical flow tracking"""
        try:
            # Use corner detection for feature points
            corners = cv2.goodFeaturesToTrack(
                self.frame_gray, maxCorners=100, qualityLevel=0.01, minDistance=10
            )
            return corners
        except:
            return None
    
    def _load_coco_labels(self):
        """Load COCO dataset class labels"""
        # COCO class labels (simplified version)
        return {
            0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle', 4: 'airplane',
            5: 'bus', 6: 'train', 7: 'truck', 8: 'boat', 9: 'traffic light',
            10: 'fire hydrant', 11: 'stop sign', 12: 'parking meter', 13: 'bench',
            14: 'bird', 15: 'cat', 16: 'dog', 17: 'horse', 18: 'sheep', 19: 'cow',
            # Add more labels as needed
        }
    
    def get_processing_results(self):
        """Get the latest processing results"""
        return getattr(self, 'last_processing_results', {})
    
    def set_processing_enabled(self, enabled: bool):
        """Enable or disable specific processing stages"""
        self.processing_enabled = {
            'faces': enabled,
            'objects': enabled,
            'edges': enabled,
            'motion': enabled,
            'lighting': enabled
        }
    
    def get_performance_summary(self):
        """Get performance summary"""
        if not self.performance_history:
            return None
        
        recent_metrics = self.performance_history[-10:]  # Last 10 measurements
        
        return {
            'cpu_usage_avg': np.mean([m.cpu_usage for m in recent_metrics]),
            'memory_usage_avg': np.mean([m.memory_usage for m in recent_metrics]),
            'temperature_avg': np.mean([m.temperature for m in recent_metrics]),
            'fps_avg': np.mean([m.fps for m in recent_metrics if m.fps > 0]),
            'processing_time_avg': np.mean([m.processing_time for m in recent_metrics if m.processing_time > 0]),
            'gpu_available': self.gpu_available,
            'thread_count': self.max_workers
        }
    
    def export_performance_data(self, filename: str):
        """Export performance data to JSON file"""
        try:
            data = {
                'performance_summary': self.get_performance_summary(),
                'performance_history': [
                    {
                        'cpu_usage': m.cpu_usage,
                        'memory_usage': m.memory_usage,
                        'gpu_usage': m.gpu_usage,
                        'temperature': m.temperature,
                        'fps': m.fps,
                        'processing_time': m.processing_time,
                        'timestamp': m.timestamp
                    }
                    for m in self.performance_history
                ],
                'export_time': time.time()
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Performance data exported to {filename}")
        except Exception as e:
            logger.error(f"Failed to export performance data: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_monitoring()
        self.executor.shutdown(wait=True)
        self.memory_pool.clear()
        logger.info("Raspberry Pi optimizer cleaned up")

# Example usage
if __name__ == "__main__":
    try:
        optimizer = RaspberryPiOptimizer()
        optimizer.start_monitoring()
        
        # Run for 60 seconds
        time.sleep(60)
        
        # Export data
        optimizer.export_performance_data("performance_data.json")
        
        # Cleanup
        optimizer.cleanup()
        
    except KeyboardInterrupt:
        logger.info("Raspberry Pi optimizer stopped by user")
    except Exception as e:
        logger.error(f"Raspberry Pi optimizer error: {e}")
