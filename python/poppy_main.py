#!/usr/bin/env python3
"""
Poppy Robot - Main System Startup
Initializes all systems with proper communication mechanisms
"""

import time
import logging
import signal
import sys
import threading
from typing import Optional

# Import all system components
from communication_manager import get_communication_manager, MessageType
from system_integration import PoppySystemIntegration
from power_management import SmartPowerManager
from raspberry_pi_optimizer import RaspberryPiOptimizer
from advanced_face_detection import AdvancedFaceDetection
from unified_voice_control import UnifiedVoiceControl

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/poppy_system.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class PoppyMainSystem:
    """Main system coordinator for Poppy Robot"""
    
    def __init__(self):
        self.is_running = False
        self.system_integration = None
        self.comm_manager = None
        self.shutdown_event = threading.Event()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Poppy Main System initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_event.set()
        self.stop()
    
    def initialize_system(self):
        """Initialize all system components"""
        try:
            logger.info("Starting Poppy Robot System Initialization...")
            
            # Initialize communication manager first
            logger.info("Initializing Communication Manager...")
            self.comm_manager = get_communication_manager()
            self.comm_manager.start()
            
            # Initialize system integration
            logger.info("Initializing System Integration...")
            self.system_integration = PoppySystemIntegration()
            
            # Start system integration
            self.system_integration.start_system()
            
            # Setup system monitoring
            self._setup_system_monitoring()
            
            self.is_running = True
            logger.info("Poppy Robot System initialization complete")
            
            return True
            
        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            return False
    
    def _setup_system_monitoring(self):
        """Setup system health monitoring"""
        try:
            # Subscribe to system messages
            self.comm_manager.subscribe(MessageType.EMERGENCY, self._handle_system_emergency)
            self.comm_manager.subscribe(MessageType.SYSTEM_SHUTDOWN, self._handle_system_shutdown)
            
            # Start monitoring thread
            monitoring_thread = threading.Thread(target=self._system_monitoring_loop)
            monitoring_thread.daemon = True
            monitoring_thread.start()
            
            logger.info("System monitoring setup complete")
            
        except Exception as e:
            logger.error(f"Failed to setup system monitoring: {e}")
    
    def _system_monitoring_loop(self):
        """Main system monitoring loop"""
        while self.is_running and not self.shutdown_event.is_set():
            try:
                # Check system health
                self._check_system_health()
                
                # Send heartbeat
                self._send_heartbeat()
                
                # Sleep for monitoring interval
                time.sleep(5)  # Monitor every 5 seconds
                
            except Exception as e:
                logger.error(f"System monitoring error: {e}")
                time.sleep(10)  # Wait longer on error
    
    def _check_system_health(self):
        """Check overall system health"""
        try:
            if self.system_integration and self.system_integration.system_status:
                status = self.system_integration.system_status
                
                # Check for critical issues
                if hasattr(status, 'emergency') and status.emergency:
                    logger.critical("System in emergency state")
                    self._handle_system_emergency(None)
                
                # Check battery status
                if hasattr(status, 'battery_percentage') and status.battery_percentage < 10:
                    logger.warning(f"Critical battery level: {status.battery_percentage}%")
                
                # Check system performance
                if hasattr(status, 'system_performance'):
                    perf = status.system_performance
                    if perf.get('cpu_usage', 0) > 90:
                        logger.warning("High CPU usage detected")
                    if perf.get('memory_usage', 0) > 90:
                        logger.warning("High memory usage detected")
                    if perf.get('temperature', 0) > 80:
                        logger.warning("High temperature detected")
                
        except Exception as e:
            logger.error(f"System health check failed: {e}")
    
    def _send_heartbeat(self):
        """Send system heartbeat"""
        try:
            heartbeat_data = {
                "system_status": "running",
                "timestamp": time.time(),
                "uptime": time.time() - getattr(self, 'start_time', time.time())
            }
            
            self.comm_manager.send_message(
                Message(
                    message_type=MessageType.HEARTBEAT,
                    source="main_system",
                    destination="all",
                    data=heartbeat_data,
                    timestamp=time.time(),
                    priority=0
                )
            )
            
        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")
    
    def _handle_system_emergency(self, message):
        """Handle system emergency"""
        try:
            logger.critical("SYSTEM EMERGENCY DETECTED")
            
            # Stop all systems immediately
            if self.system_integration:
                self.system_integration._emergency_shutdown()
            
            # Send emergency notification
            self.comm_manager.send_emergency("main_system", {
                "emergency_type": "system_failure",
                "timestamp": time.time(),
                "action": "immediate_shutdown"
            })
            
        except Exception as e:
            logger.error(f"Emergency handling failed: {e}")
    
    def _handle_system_shutdown(self, message):
        """Handle system shutdown request"""
        try:
            logger.info("System shutdown requested")
            self.shutdown_event.set()
            self.stop()
            
        except Exception as e:
            logger.error(f"Shutdown handling failed: {e}")
    
    def run(self):
        """Main system run loop"""
        try:
            if not self.initialize_system():
                logger.error("System initialization failed, exiting")
                return False
            
            self.start_time = time.time()
            logger.info("Poppy Robot System is now running")
            
            # Main run loop
            while self.is_running and not self.shutdown_event.is_set():
                try:
                    # Check for shutdown signal
                    if self.shutdown_event.wait(timeout=1.0):
                        break
                    
                    # System is running normally
                    time.sleep(0.1)
                    
                except KeyboardInterrupt:
                    logger.info("Keyboard interrupt received")
                    break
                except Exception as e:
                    logger.error(f"Main loop error: {e}")
                    time.sleep(1)
            
            return True
            
        except Exception as e:
            logger.error(f"System run failed: {e}")
            return False
        finally:
            self.stop()
    
    def stop(self):
        """Stop all systems gracefully"""
        try:
            logger.info("Stopping Poppy Robot System...")
            
            self.is_running = False
            self.shutdown_event.set()
            
            # Stop system integration
            if self.system_integration:
                self.system_integration.stop_system()
            
            # Stop communication manager
            if self.comm_manager:
                self.comm_manager.stop()
            
            logger.info("Poppy Robot System stopped")
            
        except Exception as e:
            logger.error(f"System stop failed: {e}")
    
    def restart_system(self):
        """Restart the entire system"""
        try:
            logger.info("Restarting Poppy Robot System...")
            
            # Stop current system
            self.stop()
            
            # Wait a moment
            time.sleep(2)
            
            # Reinitialize
            if self.initialize_system():
                logger.info("System restart successful")
                return True
            else:
                logger.error("System restart failed")
                return False
                
        except Exception as e:
            logger.error(f"System restart failed: {e}")
            return False

def main():
    """Main entry point"""
    try:
        # Create and run main system
        poppy_system = PoppyMainSystem()
        
        # Run the system
        success = poppy_system.run()
        
        if success:
            logger.info("Poppy Robot System completed successfully")
            sys.exit(0)
        else:
            logger.error("Poppy Robot System failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
