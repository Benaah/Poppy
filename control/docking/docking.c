#include "docking.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <unistd.h>

// Self-Docking and Charging Implementation
// Provides autonomous docking and charging capabilities

#define PI 3.14159265359
#define DEG_TO_RAD (PI / 180.0)
#define RAD_TO_DEG (180.0 / PI)

// Global docking controller instance
static docking_controller_t *g_docking_controller = NULL;

int docking_init(docking_controller_t *controller) {
    if (!controller) return -1;
    
    memset(controller, 0, sizeof(docking_controller_t));
    
    // Initialize states
    controller->state = DOCKING_IDLE;
    controller->charging.state = CHARGING_DISCONNECTED;
    
    // Set default parameters
    controller->approach_speed = 0.3;
    controller->alignment_speed = 0.1;
    controller->final_approach_speed = 0.05;
    
    // Safety parameters
    controller->min_battery_level = 20.0;  // 20% minimum battery
    controller->max_docking_time = 30.0;   // 30 seconds max docking time
    controller->emergency_stop = 0;
    
    // Initialize charging system
    if (charging_init(&controller->charging) < 0) {
        printf(" Failed to initialize charging system\n");
        return -1;
    }
    
    g_docking_controller = controller;
    printf(" Docking system initialized\n");
    return 0;
}

void docking_update(docking_controller_t *controller) {
    if (!controller) return;
    
    // Update charging system
    charging_update(&controller->charging);
    
    // Check safety conditions
    if (!docking_check_safety(controller)) {
        docking_emergency_stop(controller);
        return;
    }
    
    // State machine
    switch (controller->state) {
        case DOCKING_IDLE:
            // Wait for docking command or low battery
            if (controller->charging.battery_percentage < controller->min_battery_level) {
                printf("🔋 Low battery detected (%.1f%%), starting docking sequence\n", 
                       controller->charging.battery_percentage);
                docking_start_search(controller);
            }
            break;
            
        case DOCKING_SEARCHING:
            if (docking_detect_station(controller)) {
                printf("🎯 Docking station detected at %.1f cm, %.1f°\n", 
                       controller->station.distance, controller->station.angle);
                controller->state = DOCKING_APPROACHING;
            } else {
                // Continue searching
                printf("🔍 Searching for docking station...\n");
            }
            break;
            
        case DOCKING_APPROACHING:
            if (docking_approach_station(controller)) {
                printf("📍 Approached docking station\n");
                controller->state = DOCKING_ALIGNING;
            }
            break;
            
        case DOCKING_ALIGNING:
            if (docking_align_with_station(controller)) {
                printf("🎯 Aligned with docking station\n");
                controller->state = DOCKING_CONNECTING;
            }
            break;
            
        case DOCKING_CONNECTING:
            if (docking_connect(controller)) {
                printf("🔌 Connected to docking station\n");
                controller->state = DOCKING_CHARGING;
                docking_start_charging(controller);
            }
            break;
            
        case DOCKING_CHARGING:
            if (charging_is_complete(&controller->charging)) {
                printf("✅ Charging complete (%.1f%%)\n", 
                       controller->charging.battery_percentage);
                controller->state = DOCKING_COMPLETE;
            } else {
                printf("🔋 Charging... %.1f%% (%.1fV, %.1fA)\n", 
                       controller->charging.battery_percentage,
                       controller->charging.voltage,
                       controller->charging.current);
            }
            break;
            
        case DOCKING_ERROR:
            printf("❌ Docking error occurred\n");
            controller->state = DOCKING_IDLE;
            break;
            
        case DOCKING_COMPLETE:
            printf("✅ Docking sequence complete\n");
            controller->state = DOCKING_IDLE;
            break;
    }
}

int docking_start_search(docking_controller_t *controller) {
    if (!controller) return -1;
    
    controller->state = DOCKING_SEARCHING;
    controller->docking_attempts++;
    clock_gettime(CLOCK_MONOTONIC, &controller->docking_start_time);
    
    printf("🔍 Starting docking station search (attempt %d)\n", controller->docking_attempts);
    return 0;
}

int docking_approach_station(docking_controller_t *controller) {
    if (!controller || !controller->station.detected) return -1;
    
    double distance = controller->station.distance;
    double angle = controller->station.angle;
    
    // Calculate approach parameters
    double approach_distance = 10.0;  // 10cm from station
    double speed = controller->approach_speed;
    
    if (distance > approach_distance) {
        // Move towards station
        double forward_speed = speed * 0.8;
        double turn_speed = angle * 0.1;  // Proportional turn
        
        // Send movement commands (this would interface with the main control system)
        printf("📤 Approach: move=%.2f, turn=%.2f (dist=%.1f, angle=%.1f)\n", 
               forward_speed, turn_speed, distance, angle);
        
        // Simulate movement (in real implementation, this would send actual commands)
        controller->station.distance -= speed * 0.1;  // Simulate getting closer
        controller->station.angle *= 0.9;  // Simulate alignment
        
        return 0;  // Still approaching
    } else {
        return 1;  // Reached approach distance
    }
}

int docking_align_with_station(docking_controller_t *controller) {
    if (!controller || !controller->station.detected) return -1;
    
    double angle = controller->station.angle;
    double alignment_tolerance = DOCKING_ALIGNMENT_TOLERANCE_DEG;
    
    if (fabs(angle) > alignment_tolerance) {
        // Align with station
        double turn_speed = angle * 0.05;  // Fine alignment
        
        printf("📤 Align: turn=%.2f (angle=%.1f°)\n", turn_speed, angle);
        
        // Simulate alignment
        controller->station.angle *= 0.8;
        
        return 0;  // Still aligning
    } else {
        return 1;  // Aligned
    }
}

int docking_connect(docking_controller_t *controller) {
    if (!controller) return -1;
    
    // Simulate connection process
    static int connection_attempts = 0;
    connection_attempts++;
    
    if (connection_attempts < 5) {
        printf("🔌 Connecting to docking station... (attempt %d)\n", connection_attempts);
        return 0;  // Still connecting
    } else {
        printf("✅ Connected to docking station\n");
        connection_attempts = 0;
        return 1;  // Connected
    }
}

int docking_start_charging(docking_controller_t *controller) {
    if (!controller) return -1;
    
    controller->charging.state = CHARGING_IN_PROGRESS;
    clock_gettime(CLOCK_MONOTONIC, &controller->charging.charge_start_time);
    controller->charging.is_charging = 1;
    
    printf("🔋 Started charging\n");
    return 0;
}

int docking_undock(docking_controller_t *controller) {
    if (!controller) return -1;
    
    controller->charging.state = CHARGING_DISCONNECTED;
    controller->charging.is_charging = 0;
    controller->state = DOCKING_IDLE;
    
    printf("🔌 Undocked from charging station\n");
    return 0;
}

// Station detection functions
int docking_detect_station(docking_controller_t *controller) {
    if (!controller) return 0;
    
    // Simulate docking station detection using various sensors
    // In real implementation, this would use:
    // - IR sensors for station detection
    // - Camera for visual recognition
    // - Ultrasonic sensors for distance measurement
    
    static int detection_cycle = 0;
    detection_cycle++;
    
    // Simulate periodic detection
    if (detection_cycle % 10 == 0) {
        // Simulate finding a station
        controller->station.detected = 1;
        controller->station.distance = 30.0 + (rand() % 20);  // 30-50 cm
        controller->station.angle = (rand() % 60) - 30;  // -30 to +30 degrees
        controller->station.confidence = 0.8;
        clock_gettime(CLOCK_MONOTONIC, &controller->station.last_detection);
        
        return 1;
    }
    
    return 0;
}

double docking_calculate_approach_angle(docking_controller_t *controller) {
    if (!controller || !controller->station.detected) return 0.0;
    
    return controller->station.angle;
}

int docking_is_station_aligned(docking_controller_t *controller) {
    if (!controller || !controller->station.detected) return 0;
    
    return fabs(controller->station.angle) < DOCKING_ALIGNMENT_TOLERANCE_DEG;
}

// Charging management functions
int charging_init(charging_system_t *charging) {
    if (!charging) return -1;
    
    charging->voltage = 3.7;  // Default battery voltage
    charging->current = 0.0;
    charging->battery_percentage = 50.0;  // Start with 50% battery
    charging->is_charging = 0;
    charging->state = CHARGING_DISCONNECTED;
    
    printf("✅ Charging system initialized\n");
    return 0;
}

void charging_update(charging_system_t *charging) {
    if (!charging) return;
    
    // Simulate battery and charging behavior
    if (charging->state == CHARGING_IN_PROGRESS) {
        // Simulate charging process
        charging->voltage += 0.01;  // Gradually increase voltage
        charging->current = 1.0;    // 1A charging current
        charging->battery_percentage += 0.1;  // 0.1% per update
        
        // Clamp values
        if (charging->voltage > 4.2) charging->voltage = 4.2;
        if (charging->battery_percentage > 100.0) {
            charging->battery_percentage = 100.0;
            charging->state = CHARGING_COMPLETE;
            charging->is_charging = 0;
        }
    } else if (charging->state == CHARGING_DISCONNECTED) {
        // Simulate battery drain when not charging
        charging->battery_percentage -= 0.01;  // Very slow drain
        if (charging->battery_percentage < 0.0) charging->battery_percentage = 0.0;
    }
}

int charging_is_connected(charging_system_t *charging) {
    if (!charging) return 0;
    return charging->state != CHARGING_DISCONNECTED;
}

int charging_is_complete(charging_system_t *charging) {
    if (!charging) return 0;
    return charging->state == CHARGING_COMPLETE;
}

double charging_get_battery_percentage(charging_system_t *charging) {
    if (!charging) return 0.0;
    return charging->battery_percentage;
}

// Safety functions
int docking_check_safety(docking_controller_t *controller) {
    if (!controller) return 1;
    
    // Check battery level
    if (controller->charging.battery_percentage < 5.0) {
        printf("⚠️  Critical battery level: %.1f%%\n", controller->charging.battery_percentage);
        return 0;
    }
    
    // Check docking timeout
    struct timespec current_time;
    clock_gettime(CLOCK_MONOTONIC, &current_time);
    double elapsed = (current_time.tv_sec - controller->docking_start_time.tv_sec) + 
                     (current_time.tv_nsec - controller->docking_start_time.tv_nsec) / 1e9;
    
    if (elapsed > controller->max_docking_time) {
        printf("⚠️  Docking timeout: %.1f seconds\n", elapsed);
        return 0;
    }
    
    // Check emergency stop
    if (controller->emergency_stop) {
        printf("⚠️  Emergency stop active\n");
        return 0;
    }
    
    return 1;
}

void docking_emergency_stop(docking_controller_t *controller) {
    if (!controller) return;
    
    controller->emergency_stop = 1;
    controller->state = DOCKING_ERROR;
    
    printf("🛑 EMERGENCY STOP: Docking sequence aborted\n");
}

int docking_is_safe_to_dock(docking_controller_t *controller) {
    if (!controller) return 0;
    
    // Check if it's safe to start docking
    return (controller->charging.battery_percentage > controller->min_battery_level) &&
           (controller->state == DOCKING_IDLE) &&
           (!controller->emergency_stop);
}

// Utility functions
const char* docking_state_to_string(docking_state_t state) {
    switch (state) {
        case DOCKING_IDLE: return "IDLE";
        case DOCKING_SEARCHING: return "SEARCHING";
        case DOCKING_APPROACHING: return "APPROACHING";
        case DOCKING_ALIGNING: return "ALIGNING";
        case DOCKING_CONNECTING: return "CONNECTING";
        case DOCKING_CHARGING: return "CHARGING";
        case DOCKING_ERROR: return "ERROR";
        case DOCKING_COMPLETE: return "COMPLETE";
        default: return "UNKNOWN";
    }
}

const char* charging_state_to_string(charging_state_t state) {
    switch (state) {
        case CHARGING_DISCONNECTED: return "DISCONNECTED";
        case CHARGING_CONNECTED: return "CONNECTED";
        case CHARGING_IN_PROGRESS: return "IN_PROGRESS";
        case CHARGING_COMPLETE: return "COMPLETE";
        case CHARGING_ERROR: return "ERROR";
        default: return "UNKNOWN";
    }
}

double docking_calculate_distance(double x1, double y1, double x2, double y2) {
    double dx = x2 - x1;
    double dy = y2 - y1;
    return sqrt(dx * dx + dy * dy);
}

double docking_calculate_angle(double x1, double y1, double x2, double y2) {
    double dx = x2 - x1;
    double dy = y2 - y1;
    return atan2(dy, dx) * RAD_TO_DEG;
}
