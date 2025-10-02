#ifndef DOCKING_H
#define DOCKING_H

#include <stdint.h>
#include <time.h>

// Self-Docking and Charging System
// Enables autonomous charging and docking capabilities

#define DOCKING_STATION_DETECTION_DISTANCE_CM 50
#define DOCKING_ALIGNMENT_TOLERANCE_DEG 5
#define CHARGING_VOLTAGE_THRESHOLD 3.7
#define DOCKING_TIMEOUT_SEC 30

// Docking states
typedef enum {
    DOCKING_IDLE,
    DOCKING_SEARCHING,
    DOCKING_APPROACHING,
    DOCKING_ALIGNING,
    DOCKING_CONNECTING,
    DOCKING_CHARGING,
    DOCKING_ERROR,
    DOCKING_COMPLETE
} docking_state_t;

// Charging states
typedef enum {
    CHARGING_DISCONNECTED,
    CHARGING_CONNECTED,
    CHARGING_IN_PROGRESS,
    CHARGING_COMPLETE,
    CHARGING_ERROR
} charging_state_t;

// Docking station detection
typedef struct {
    double distance;
    double angle;
    double confidence;
    int detected;
    struct timespec last_detection;
} docking_station_t;

// Charging system
typedef struct {
    double voltage;
    double current;
    double battery_percentage;
    int is_charging;
    charging_state_t state;
    struct timespec charge_start_time;
} charging_system_t;

// Main docking controller
typedef struct {
    docking_state_t state;
    docking_station_t station;
    charging_system_t charging;
    
    // Navigation parameters
    double approach_speed;
    double alignment_speed;
    double final_approach_speed;
    
    // Safety parameters
    double min_battery_level;
    double max_docking_time;
    int emergency_stop;
    
    // Performance metrics
    int docking_attempts;
    int successful_dockings;
    double avg_docking_time;
    struct timespec docking_start_time;
} docking_controller_t;

// Enhanced functions
int docking_init(docking_controller_t *controller);
void docking_update(docking_controller_t *controller);
int docking_start_search(docking_controller_t *controller);
int docking_approach_station(docking_controller_t *controller);
int docking_align_with_station(docking_controller_t *controller);
int docking_connect(docking_controller_t *controller);
int docking_start_charging(docking_controller_t *controller);
int docking_undock(docking_controller_t *controller);

// Station detection
int docking_detect_station(docking_controller_t *controller);
double docking_calculate_approach_angle(docking_controller_t *controller);
int docking_is_station_aligned(docking_controller_t *controller);

// Charging management
int charging_init(charging_system_t *charging);
void charging_update(charging_system_t *charging);
int charging_is_connected(charging_system_t *charging);
int charging_is_complete(charging_system_t *charging);
double charging_get_battery_percentage(charging_system_t *charging);

// Safety functions
int docking_check_safety(docking_controller_t *controller);
void docking_emergency_stop(docking_controller_t *controller);
int docking_is_safe_to_dock(docking_controller_t *controller);

// Utility functions
const char* docking_state_to_string(docking_state_t state);
const char* charging_state_to_string(charging_state_t state);
double docking_calculate_distance(double x1, double y1, double x2, double y2);
double docking_calculate_angle(double x1, double y1, double x2, double y2);

#endif
