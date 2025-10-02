#ifndef SPATIAL_H
#define SPATIAL_H

#include <stdint.h>
#include <time.h>

// Enhanced Spatial Awareness System
// Supports multiple ultrasonic sensors and advanced obstacle detection

#define MAX_SENSORS 4
#define SENSOR_HISTORY_SIZE 10
#define OBSTACLE_THRESHOLD_CM 30
#define EDGE_THRESHOLD_CM 15
#define SAFE_DISTANCE_CM 50

// Sensor configuration
typedef struct {
    uint8_t trigger_pin;
    uint8_t echo_pin;
    double last_distance;
    double distance_history[SENSOR_HISTORY_SIZE];
    int history_index;
    struct timespec last_reading;
    int is_active;
    double reliability;  // 0.0 to 1.0
} ultrasonic_sensor_t;

// Spatial awareness state
typedef struct {
    ultrasonic_sensor_t sensors[MAX_SENSORS];
    int sensor_count;
    double front_distance;
    double left_distance;
    double right_distance;
    double rear_distance;
    
    // Obstacle detection
    int obstacle_detected;
    double obstacle_distance;
    int obstacle_direction;  // -1: left, 0: front, 1: right
    
    // Edge detection
    int edge_detected;
    double edge_distance;
    int edge_direction;
    
    // Safety systems
    int emergency_stop;
    double safety_margin;
    
    // Performance metrics
    double avg_response_time;
    int total_readings;
    int failed_readings;
} spatial_awareness_t;

// Enhanced functions
int spatial_init(spatial_awareness_t *spatial);
int spatial_add_sensor(spatial_awareness_t *spatial, uint8_t trigger_pin, uint8_t echo_pin);
void spatial_update(spatial_awareness_t *spatial);
double spatial_read_sensor(ultrasonic_sensor_t *sensor);
void spatial_calculate_distances(spatial_awareness_t *spatial);
int spatial_detect_obstacles(spatial_awareness_t *spatial);
int spatial_detect_edges(spatial_awareness_t *spatial);
void spatial_update_safety(spatial_awareness_t *spatial);
double spatial_get_safe_speed(spatial_awareness_t *spatial, double desired_speed);
double spatial_get_safe_turn(spatial_awareness_t *spatial, double desired_turn);
void spatial_emergency_stop(spatial_awareness_t *spatial);
void spatial_reset_emergency(spatial_awareness_t *spatial);

// Utility functions
double spatial_calculate_median(double *values, int count);
double spatial_calculate_reliability(ultrasonic_sensor_t *sensor);
void spatial_log_reading(ultrasonic_sensor_t *sensor, double distance);
int spatial_is_reading_valid(double distance);

#endif
