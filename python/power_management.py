#!/usr/bin/env python3
"""
Poppy Robot - Smart Power Management System
BMS integration and power optimization for hardware challenges
"""

import time
import threading
import logging
import json
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
from bms_service import get_bms_service, BatteryStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PowerMode(Enum):
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW_POWER = "LOW_POWER"
    EMERGENCY = "EMERGENCY"

@dataclass
class PowerComponent:
    name: str
    voltage: float
    current: float
    enabled: bool
    priority: int  # 1 = highest priority, 5 = lowest

class SmartPowerManager:
    def __init__(self):
        # Initialize BMS service
        self.bms = get_bms_service()
        self.bms.add_callback(self._on_battery_update)
        
        # Power components
        self.components = {
            'raspberry_pi': PowerComponent('Raspberry Pi', 5.0, 2.5, True, 1),
            'arduino': PowerComponent('Arduino', 5.0, 0.1, True, 1),
            'motors': PowerComponent('Motors', 12.0, 2.0, True, 2),
            'camera': PowerComponent('Camera', 3.3, 0.2, True, 3),
            'sensors': PowerComponent('Sensors', 3.3, 0.1, True, 3),
            'wifi': PowerComponent('WiFi', 3.3, 0.3, True, 4),
            'leds': PowerComponent('LEDs', 5.0, 0.5, False, 5),
            'speaker': PowerComponent('Speaker', 5.0, 0.8, False, 5)
        }
        
        # Power modes and thresholds
        self.power_modes = {
            PowerMode.HIGH: {'min_voltage': 12.0, 'max_current': 5.0},
            PowerMode.NORMAL: {'min_voltage': 11.5, 'max_current': 3.5},
            PowerMode.LOW_POWER: {'min_voltage': 11.0, 'max_current': 2.0},
            PowerMode.EMERGENCY: {'min_voltage': 10.5, 'max_current': 1.0}
        }
        
        # Current power state
        self.current_mode = PowerMode.NORMAL
        self.battery_status = BatteryStatus(0, 0, 0, 0, 0, 0)
        self.is_running = False
        self.monitoring_thread = None
        
        # Power history for optimization
        self.power_history = []
        self.optimization_enabled = True
        
        # Initialize BMS communication
        self.init_bms()
        
    def init_bms(self):
        """Initialize communication with Battery Management System"""
        try:
            # Test BMS communication
            self.read_battery_status()
            logger.info("✓ BMS communication established")
        except Exception as e:
            logger.warning(f"BMS communication failed: {e}")
            logger.info("Using simulated battery data")
    
    def read_battery_status(self):
        """Read battery status from BMS"""
        self.battery_status = self.bms.get_battery_status()
    
    def _on_battery_update(self, battery_status: BatteryStatus):
        """Callback for battery status updates from BMS"""
        self.battery_status = battery_status
        logger.info(f"Battery updated: {battery_status.charge_percentage:.1f}% "
                   f"({battery_status.voltage:.2f}V, {battery_status.current:.3f}A)")
    
    def calculate_total_power(self):
        """Calculate total power consumption"""
        total_power = 0
        for component in self.components.values():
            if component.enabled:
                total_power += component.voltage * component.current
        return total_power
    
    def determine_power_mode(self):
        """Determine appropriate power mode based on battery status"""
        voltage = self.battery_status.voltage
        current = abs(self.battery_status.current)
        
        if voltage < 10.5:
            return PowerMode.EMERGENCY
        elif voltage < 11.0:
            return PowerMode.LOW_POWER
        elif voltage < 11.5:
            return PowerMode.NORMAL
        else:
            return PowerMode.HIGH
    
    def optimize_power_consumption(self):
        """Optimize power consumption based on current mode"""
        mode_config = self.power_modes[self.current_mode]
        max_current = mode_config['max_current']
        
        # Calculate current consumption
        total_current = sum(comp.current for comp in self.components.values() if comp.enabled)
        
        if total_current > max_current:
            # Disable non-essential components
            components_by_priority = sorted(
                [comp for comp in self.components.values() if comp.enabled],
                key=lambda x: x.priority,
                reverse=True
            )
            
            for component in components_by_priority:
                if total_current <= max_current:
                    break
                component.enabled = False
                total_current -= component.current
                logger.info(f"Disabled {component.name} to save power")
    
    def set_power_mode(self, mode: PowerMode):
        """Set power mode and optimize components"""
        if mode == self.current_mode:
            return
        
        self.current_mode = mode
        logger.info(f"Switching to {mode.value} power mode")
        
        if mode == PowerMode.HIGH:
            # Enable all components
            for component in self.components.values():
                component.enabled = True
                
        elif mode == PowerMode.NORMAL:
            # Enable essential components
            for component in self.components.values():
                if component.priority <= 3:
                    component.enabled = True
                else:
                    component.enabled = False
                    
        elif mode == PowerMode.LOW_POWER:
            # Enable only critical components
            for component in self.components.values():
                if component.priority <= 2:
                    component.enabled = True
                else:
                    component.enabled = False
                    
        elif mode == PowerMode.EMERGENCY:
            # Enable only essential components
            for component in self.components.values():
                if component.priority == 1:
                    component.enabled = True
                else:
                    component.enabled = False
        
        # Optimize power consumption
        self.optimize_power_consumption()
    
    def start_monitoring(self):
        """Start power monitoring in background thread"""
        self.is_running = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        logger.info("Power monitoring started")
    
    def stop_monitoring(self):
        """Stop power monitoring"""
        self.is_running = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
        logger.info("Power monitoring stopped")
    
    def _monitoring_loop(self):
        """Main power monitoring loop"""
        while self.is_running:
            try:
                # Read battery status
                self.read_battery_status()
                
                # Determine power mode
                new_mode = self.determine_power_mode()
                if new_mode != self.current_mode:
                    self.set_power_mode(new_mode)
                
                # Log power status
                self.log_power_status()
                
                # Store power history
                self.power_history.append({
                    'timestamp': time.time(),
                    'voltage': self.battery_status.voltage,
                    'current': self.battery_status.current,
                    'power': self.calculate_total_power(),
                    'mode': self.current_mode.value
                })
                
                # Keep only last 1000 entries
                if len(self.power_history) > 1000:
                    self.power_history = self.power_history[-1000:]
                
                time.sleep(1)  # Monitor every second
                
            except Exception as e:
                logger.error(f"Power monitoring error: {e}")
                time.sleep(5)
    
    def log_power_status(self):
        """Log current power status"""
        total_power = self.calculate_total_power()
        enabled_components = [name for name, comp in self.components.items() if comp.enabled]
        
        logger.info(f"Power Status - Mode: {self.current_mode.value}, "
                   f"Battery: {self.battery_status.voltage:.1f}V "
                   f"({self.battery_status.charge_percentage:.1f}%), "
                   f"Current: {self.battery_status.current:.2f}A, "
                   f"Total Power: {total_power:.1f}W, "
                   f"Components: {len(enabled_components)}")
    
    def get_power_status(self):
        """Get current power status"""
        return {
            'battery': {
                'voltage': self.battery_status.voltage,
                'current': self.battery_status.current,
                'temperature': self.battery_status.temperature,
                'charge_percentage': self.battery_status.charge_percentage,
                'health': self.battery_status.health,
                'cycles': self.battery_status.cycles
            },
            'power_mode': self.current_mode.value,
            'total_power': self.calculate_total_power(),
            'components': {
                name: {
                    'enabled': comp.enabled,
                    'voltage': comp.voltage,
                    'current': comp.current,
                    'power': comp.voltage * comp.current if comp.enabled else 0
                }
                for name, comp in self.components.items()
            }
        }
    
    def emergency_shutdown(self):
        """Emergency shutdown sequence"""
        logger.warning("EMERGENCY SHUTDOWN INITIATED")
        
        # Disable all non-essential components
        for component in self.components.values():
            if component.priority > 1:
                component.enabled = False
        
        # Set to emergency mode
        self.set_power_mode(PowerMode.EMERGENCY)
        
        # Send emergency signal to control system
        self.send_emergency_signal()
    
    def send_emergency_signal(self):
        """Send emergency signal to control system via communication manager"""
        try:
            from communication_manager import get_communication_manager, MessageType
            
            comm_manager = get_communication_manager()
            
            # Send emergency message with critical priority
            emergency_data = {
                "battery_voltage": self.battery_status.voltage,
                "battery_percentage": self.battery_status.charge_percentage,
                "battery_current": self.battery_status.current,
                "battery_temperature": self.battery_status.temperature,
                "power_mode": "EMERGENCY",
                "action": "immediate_shutdown",
                "components_disabled": [name for name, comp in self.components.items() if not comp.enabled]
            }
            
            comm_manager.send_emergency("power_management", emergency_data)
            
            # Log the emergency event
            logger.critical("EMERGENCY SIGNAL SENT TO ALL CONTROL SYSTEMS")
            
        except Exception as e:
            logger.error(f"Failed to send emergency signal: {e}")
    
    def send_status_update(self):
        """Send regular status update via communication manager"""
        try:
            from communication_manager import get_communication_manager, MessageType
            
            comm_manager = get_communication_manager()
            
            status_data = {
                "battery_voltage": self.battery_status.voltage,
                "battery_percentage": self.battery_status.charge_percentage,
                "battery_current": self.battery_status.current,
                "battery_temperature": self.battery_status.temperature,
                "power_mode": self.current_mode.value,
                "total_power_consumption": self.calculate_total_power(),
                "components_status": {
                    name: {
                        "enabled": comp.enabled,
                        "voltage": comp.voltage,
                        "current": comp.current,
                        "priority": comp.priority
                    }
                    for name, comp in self.components.items()
                }
            }
            
            comm_manager.send_status_update("power_management", status_data)
            
        except Exception as e:
            logger.error(f"Failed to send status update: {e}")
    
    def send_battery_alert(self, alert_type: str, threshold: float):
        """Send battery alert via communication manager"""
        try:
            from communication_manager import get_communication_manager, MessageType
            
            comm_manager = get_communication_manager()
            
            alert_data = {
                "alert_type": alert_type,
                "threshold": threshold,
                "current_value": self.battery_status.charge_percentage,
                "battery_voltage": self.battery_status.voltage,
                "recommended_action": self._get_battery_alert_action(alert_type)
            }
            
            from communication_manager import Message
            comm_manager.send_message(Message(
                message_type=MessageType.BATTERY_ALERT,
                source="power_management",
                destination="system_integration",
                data=alert_data,
                timestamp=time.time(),
                priority=1
            ))
            
        except Exception as e:
            logger.error(f"Failed to send battery alert: {e}")
    
    def _get_battery_alert_action(self, alert_type: str) -> str:
        """Get recommended action for battery alert"""
        actions = {
            "low_battery": "Reduce power consumption, prepare for docking",
            "critical_battery": "Immediate docking required",
            "overheating": "Reduce processing load, check cooling",
            "charging_complete": "Continue normal operation",
            "charging_failed": "Check charging system, manual intervention required"
        }
        return actions.get(alert_type, "Monitor battery status")
    
    def enable_component(self, component_name: str):
        """Enable a specific component"""
        if component_name in self.components:
            self.components[component_name].enabled = True
            logger.info(f"Enabled {component_name}")
        else:
            logger.warning(f"Component {component_name} not found")
    
    def disable_component(self, component_name: str):
        """Disable a specific component"""
        if component_name in self.components:
            self.components[component_name].enabled = False
            logger.info(f"Disabled {component_name}")
        else:
            logger.warning(f"Component {component_name} not found")
    
    def get_power_history(self, duration_minutes=60):
        """Get power history for specified duration"""
        cutoff_time = time.time() - (duration_minutes * 60)
        return [entry for entry in self.power_history if entry['timestamp'] > cutoff_time]
    
    def export_power_data(self, filename: str):
        """Export power data to JSON file"""
        try:
            data = {
                'power_status': self.get_power_status(),
                'power_history': self.power_history,
                'export_time': time.time()
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Power data exported to {filename}")
        except Exception as e:
            logger.error(f"Failed to export power data: {e}")

# Example usage
if __name__ == "__main__":
    try:
        power_manager = SmartPowerManager()
        power_manager.start_monitoring()
        
        # Run for 60 seconds
        time.sleep(60)
        
        # Export data
        power_manager.export_power_data("power_data.json")
        
        # Stop monitoring
        power_manager.stop_monitoring()
        
    except KeyboardInterrupt:
        logger.info("Power management stopped by user")
    except Exception as e:
        logger.error(f"Power management error: {e}")
