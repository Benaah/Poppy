#!/usr/bin/env python3

import smbus
import time
import threading
import logging
from dataclasses import dataclass
from typing import Optional, Callable
import struct

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BatteryStatus:
    voltage: float
    current: float
    temperature: float
    charge_percentage: float
    health: float
    cycles: int
    power_mode: str
    charging: bool
    time_remaining: int  # minutes
    cell_voltages: list  # Individual cell voltages
    cell_temperatures: list  # Individual cell temperatures
    error_flags: int  # Bit flags for various errors

class BMSService:
    """
    Battery Management System service for hardware communication
    Supports I2C communication with BMS modules and direct ADC readings
    """
    
    def __init__(self, i2c_bus=1, bms_address=0x48, adc_address=0x4A):
        self.i2c_bus = i2c_bus
        self.bms_address = bms_address
        self.adc_address = adc_address
        self.bus = None
        self.running = False
        self.monitor_thread = None
        self.callbacks = []
        
        # BMS configuration
        self.num_cells = 4
        self.cell_nominal_voltage = 3.7  # V
        self.cell_max_voltage = 4.2  # V
        self.cell_min_voltage = 3.0  # V
        self.pack_nominal_voltage = self.num_cells * self.cell_nominal_voltage
        
        # Calibration values (would be loaded from config in production)
        self.voltage_scale = 0.001  # ADC to voltage conversion
        self.current_scale = 0.01   # ADC to current conversion
        self.temp_scale = 0.1       # ADC to temperature conversion
        
        # Current battery status
        self.battery_status = BatteryStatus(
            voltage=0.0, current=0.0, temperature=0.0,
            charge_percentage=0.0, health=100.0, cycles=0,
            power_mode="UNKNOWN", charging=False, time_remaining=0,
            cell_voltages=[0.0] * self.num_cells,
            cell_temperatures=[0.0] * self.num_cells,
            error_flags=0
        )
        
        self.init_hardware()
    
    def init_hardware(self):
        """Initialize I2C communication and hardware"""
        try:
            self.bus = smbus.SMBus(self.i2c_bus)
            logger.info(f"BMS initialized on I2C bus {self.i2c_bus}")
            
            # Test communication with BMS
            if self.test_bms_communication():
                logger.info("BMS communication test successful")
            else:
                logger.warning("BMS communication test failed, using fallback mode")
                
        except Exception as e:
            logger.error(f"Failed to initialize BMS hardware: {e}")
            self.bus = None
    
    def test_bms_communication(self) -> bool:
        """Test communication with BMS module"""
        try:
            if self.bus is None:
                return False
            # Try to read a register from BMS
            self.bus.read_byte_data(self.bms_address, 0x00)
            return True
        except Exception:
            return False
    
    def read_voltage(self) -> float:
        """Read battery pack voltage from BMS"""
        try:
            if self.bus is None:
                return self.pack_nominal_voltage
            
            # Read voltage from BMS register (address 0x01)
            voltage_raw = self.bus.read_word_data(self.bms_address, 0x01)
            voltage = struct.unpack('>H', struct.pack('<H', voltage_raw))[0] * self.voltage_scale
            return round(voltage, 2)
            
        except Exception as e:
            logger.error(f"Error reading voltage: {e}")
            return self.pack_nominal_voltage
    
    def read_current(self) -> float:
        """Read battery current from BMS"""
        try:
            if self.bus is None:
                return 0.0
            
            # Read current from BMS register (address 0x02)
            current_raw = self.bus.read_word_data(self.bms_address, 0x02)
            current = struct.unpack('>h', struct.pack('<H', current_raw))[0] * self.current_scale
            return round(current, 3)
            
        except Exception as e:
            logger.error(f"Error reading current: {e}")
            return 0.0
    
    def read_temperature(self) -> float:
        """Read battery temperature from BMS"""
        try:
            if self.bus is None:
                return 25.0  # Room temperature
            
            # Read temperature from BMS register (address 0x03)
            temp_raw = self.bus.read_word_data(self.bms_address, 0x03)
            temperature = struct.unpack('>h', struct.pack('<H', temp_raw))[0] * self.temp_scale
            return round(temperature, 1)
            
        except Exception as e:
            logger.error(f"Error reading temperature: {e}")
            return 25.0
    
    def read_cell_voltages(self) -> list:
        """Read individual cell voltages"""
        cell_voltages = []
        try:
            if self.bus is None:
                return [self.cell_nominal_voltage] * self.num_cells
            
            for i in range(self.num_cells):
                # Read cell voltage from registers 0x10 + i
                cell_raw = self.bus.read_word_data(self.bms_address, 0x10 + i)
                cell_voltage = struct.unpack('>H', struct.pack('<H', cell_raw))[0] * self.voltage_scale
                cell_voltages.append(round(cell_voltage, 3))
            
            return cell_voltages
            
        except Exception as e:
            logger.error(f"Error reading cell voltages: {e}")
            return [self.cell_nominal_voltage] * self.num_cells
    
    def read_cell_temperatures(self) -> list:
        """Read individual cell temperatures"""
        cell_temps = []
        try:
            if self.bus is None:
                return [25.0] * self.num_cells
            
            for i in range(self.num_cells):
                # Read cell temperature from registers 0x20 + i
                temp_raw = self.bus.read_word_data(self.bms_address, 0x20 + i)
                cell_temp = struct.unpack('>h', struct.pack('<H', temp_raw))[0] * self.temp_scale
                cell_temps.append(round(cell_temp, 1))
            
            return cell_temps
            
        except Exception as e:
            logger.error(f"Error reading cell temperatures: {e}")
            return [25.0] * self.num_cells
    
    def read_charge_percentage(self) -> float:
        """Calculate charge percentage based on voltage"""
        voltage = self.read_voltage()
        
        # Voltage-based SOC calculation (simplified)
        if voltage >= self.pack_nominal_voltage * 1.05:  # 100% at 4.2V per cell
            return 100.0
        elif voltage >= self.pack_nominal_voltage * 0.95:  # 80% at 3.9V per cell
            return 80.0 + (voltage - self.pack_nominal_voltage * 0.95) / (self.pack_nominal_voltage * 0.1) * 20.0
        elif voltage >= self.pack_nominal_voltage * 0.85:  # 50% at 3.5V per cell
            return 50.0 + (voltage - self.pack_nominal_voltage * 0.85) / (self.pack_nominal_voltage * 0.1) * 30.0
        elif voltage >= self.pack_nominal_voltage * 0.75:  # 20% at 3.2V per cell
            return 20.0 + (voltage - self.pack_nominal_voltage * 0.75) / (self.pack_nominal_voltage * 0.1) * 30.0
        else:
            return max(0.0, (voltage - self.pack_nominal_voltage * 0.65) / (self.pack_nominal_voltage * 0.1) * 20.0)
    
    def read_charging_status(self) -> bool:
        """Read charging status from BMS"""
        try:
            if self.bus is None:
                return False
            
            # Read charging status from BMS register (address 0x04)
            status_byte = self.bus.read_byte_data(self.bms_address, 0x04)
            return bool(status_byte & 0x01)  # Bit 0 indicates charging
            
        except Exception as e:
            logger.error(f"Error reading charging status: {e}")
            return False
    
    def read_error_flags(self) -> int:
        """Read error flags from BMS"""
        try:
            if self.bus is None:
                return 0
            
            # Read error flags from BMS register (address 0x05)
            error_flags = self.bus.read_byte_data(self.bms_address, 0x05)
            return error_flags
            
        except Exception as e:
            logger.error(f"Error reading error flags: {e}")
            return 0
    
    def calculate_health(self, charge_percentage: float, cycles: int) -> float:
        """Calculate battery health based on charge cycles and other factors"""
        # Health decreases with cycles (simplified model)
        cycle_health = max(0, 100 - (cycles * 0.01))
        
        # Health decreases if voltage is consistently low
        voltage_health = min(100, charge_percentage + 20)
        
        # Return minimum of both factors
        return min(cycle_health, voltage_health)
    
    def determine_power_mode(self, voltage: float, current: float, temperature: float) -> str:
        """Determine power mode based on battery conditions"""
        if voltage < self.pack_nominal_voltage * 0.7:  # Below 3V per cell
            return "EMERGENCY"
        elif voltage < self.pack_nominal_voltage * 0.8:  # Below 3.2V per cell
            return "LOW_POWER"
        elif temperature > 45.0 or temperature < 0.0:  # Temperature limits
            return "THERMAL_LIMIT"
        elif voltage < self.pack_nominal_voltage * 0.9:  # Below 3.4V per cell
            return "NORMAL"
        else:
            return "HIGH"
    
    def calculate_time_remaining(self, current: float, charge_percentage: float) -> int:
        """Calculate estimated time remaining in minutes"""
        if current == 0:
            return 0
        
        if current > 0:  # Discharging
            remaining_capacity = charge_percentage / 100.0 * 2.5  # Assume 2.5Ah capacity
            time_hours = remaining_capacity / abs(current)
            return int(time_hours * 60)
        else:  # Charging
            remaining_capacity = (100 - charge_percentage) / 100.0 * 2.5
            time_hours = remaining_capacity / abs(current)
            return int(time_hours * 60)
    
    def update_battery_status(self):
        """Update all battery status parameters"""
        try:
            # Read all parameters from hardware
            voltage = self.read_voltage()
            current = self.read_current()
            temperature = self.read_temperature()
            cell_voltages = self.read_cell_voltages()
            cell_temperatures = self.read_cell_temperatures()
            charging = self.read_charging_status()
            error_flags = self.read_error_flags()
            
            # Calculate derived parameters
            charge_percentage = self.read_charge_percentage()
            power_mode = self.determine_power_mode(voltage, current, temperature)
            time_remaining = self.calculate_time_remaining(current, charge_percentage)
            health = self.calculate_health(charge_percentage, self.battery_status.cycles)
            
            # Update battery status
            self.battery_status = BatteryStatus(
                voltage=voltage,
                current=current,
                temperature=temperature,
                charge_percentage=charge_percentage,
                health=health,
                cycles=self.battery_status.cycles,  # Would be read from persistent storage
                power_mode=power_mode,
                charging=charging,
                time_remaining=time_remaining,
                cell_voltages=cell_voltages,
                cell_temperatures=cell_temperatures,
                error_flags=error_flags
            )
            
            # Notify callbacks
            for callback in self.callbacks:
                try:
                    callback(self.battery_status)
                except Exception as e:
                    logger.error(f"Error in BMS callback: {e}")
                    
        except Exception as e:
            logger.error(f"Error updating battery status: {e}")
    
    def add_callback(self, callback: Callable[[BatteryStatus], None]):
        """Add a callback function to be called when battery status updates"""
        self.callbacks.append(callback)
    
    def start_monitoring(self, interval: float = 1.0):
        """Start continuous battery monitoring"""
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logger.info(f"BMS monitoring started with {interval}s interval")
    
    def stop_monitoring(self):
        """Stop continuous battery monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        logger.info("BMS monitoring stopped")
    
    def _monitor_loop(self, interval: float):
        """Internal monitoring loop"""
        while self.running:
            try:
                self.update_battery_status()
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error in BMS monitor loop: {e}")
                time.sleep(interval)
    
    def get_battery_status(self) -> BatteryStatus:
        """Get current battery status"""
        return self.battery_status
    
    def set_charging(self, enabled: bool):
        """Enable or disable charging"""
        try:
            if self.bus is None:
                logger.warning("BMS not available, cannot control charging")
                return
            
            # Write charging control to BMS register (address 0x06)
            control_byte = 0x01 if enabled else 0x00
            self.bus.write_byte_data(self.bms_address, 0x06, control_byte)
            logger.info(f"Charging {'enabled' if enabled else 'disabled'}")
            
        except Exception as e:
            logger.error(f"Error setting charging: {e}")
    
    def emergency_shutdown(self):
        """Emergency shutdown of battery system"""
        try:
            if self.bus is None:
                return
            
            # Write emergency shutdown command to BMS register (address 0x07)
            self.bus.write_byte_data(self.bms_address, 0x07, 0xFF)
            logger.warning("Emergency battery shutdown initiated")
            
        except Exception as e:
            logger.error(f"Error during emergency shutdown: {e}")

# Global BMS instance
bms_service = BMSService()

def get_bms_service() -> BMSService:
    """Get the global BMS service instance"""
    return bms_service

if __name__ == "__main__":
    # Test the BMS service
    bms = get_bms_service()
    
    def status_callback(status: BatteryStatus):
        print(f"Battery: {status.charge_percentage:.1f}% ({status.voltage:.2f}V, {status.current:.3f}A)")
        print(f"Temperature: {status.temperature:.1f}°C, Health: {status.health:.1f}%")
        print(f"Power Mode: {status.power_mode}, Charging: {status.charging}")
        print(f"Time Remaining: {status.time_remaining} minutes")
        print("---")
    
    bms.add_callback(status_callback)
    bms.start_monitoring(2.0)  # Update every 2 seconds
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        bms.stop_monitoring()
        print("BMS monitoring stopped")
