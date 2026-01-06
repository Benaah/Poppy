#include "spatial.h"
#include <wiringPi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

// Enhanced Spatial Awareness Implementation
// Based on latest ultrasonic sensor improvements and multi-sensor fusion

#define SOUND_SPEED_CM_PER_US 0.0343
#define MAX_DISTANCE_CM 400
#define MIN_DISTANCE_CM 2
#define TIMEOUT_US 30000

int spatial_init(spatial_awareness_t *spatial) {
    if (!spatial) return -1;
    
    memset(spatial, 0, sizeof(spatial_awareness_t));
    spatial->sensor_count = 0;
    spatial->safety_margin = 20.0;  // 20cm safety margin
    spatial->emergency_stop = 0;
    
    // Initialize wiringPi for GPIO access
    if (wiringPiSetupGpio() == -1) {
        printf("Failed to initialize wiringPi\n");
        return -1;
    }
    
    printf("[OK] Spatial awareness system initialized\n");
    return 0;
}

int spatial_add_sensor(spatial_awareness_t *spatial, uint8_t trigger_pin, uint8_t echo_pin) {
    if (!spatial || spatial->sensor_count >= MAX_SENSORS) {
        return -1;
    }
    
    ultrasonic_sensor_t *sensor = &spatial->sensors[spatial->sensor_count];
    sensor->trigger_pin = trigger_pin;
    sensor->echo_pin = echo_pin;
    sensor->last_distance = 0.0;
    sensor->history_index = 0;
    sensor->is_active = 1;
    sensor->reliability = 1.0;
    
    // Initialize GPIO pins
    pinMode(trigger_pin, OUTPUT);
    pinMode(echo_pin, INPUT);
    digitalWrite(trigger_pin, LOW);
    
    spatial->sensor_count++;
    printf("[OK] Added ultrasonic sensor: trigger=%d, echo=%d\n", trigger_pin, echo_pin);
    return spatial->sensor_count - 1;
}

double spatial_read_sensor(ultrasonic_sensor_t *sensor) {
    if (!sensor || !sensor->is_active) {
        return -1.0;
    }
    
    // Send trigger pulse
    digitalWrite(sensor->trigger_pin, HIGH);
    delayMicroseconds(10);
    digitalWrite(sensor->trigger_pin, LOW);
    
    // Wait for echo start
    struct timespec start_time, end_time;
    clock_gettime(CLOCK_MONOTONIC, &start_time);
    
    while (digitalRead(sensor->echo_pin) == LOW) {
        clock_gettime(CLOCK_MONOTONIC, &end_time);
        double elapsed = (end_time.tv_sec - start_time.tv_sec) * 1000000.0 + 
                        (end_time.tv_nsec - start_time.tv_nsec) / 1000.0;
        if (elapsed > TIMEOUT_US) {
            return -1.0;  // Timeout
        }
    }
    
    clock_gettime(CLOCK_MONOTONIC, &start_time);
    
    // Wait for echo end
    while (digitalRead(sensor->echo_pin) == HIGH) {
        clock_gettime(CLOCK_MONOTONIC, &end_time);
        double elapsed = (end_time.tv_sec - start_time.tv_sec) * 1000000.0 + 
                        (end_time.tv_nsec - start_time.tv_nsec) / 1000.0;
        if (elapsed > TIMEOUT_US) {
            return -1.0;  // Timeout
        }
    }
    
    clock_gettime(CLOCK_MONOTONIC, &end_time);
    
    // Calculate distance
    double pulse_duration = (end_time.tv_sec - start_time.tv_sec) * 1000000.0 + 
                           (end_time.tv_nsec - start_time.tv_nsec) / 1000.0;
    double distance = (pulse_duration * SOUND_SPEED_CM_PER_US) / 2.0;
    
    // Validate reading
    if (!spatial_is_reading_valid(distance)) {
        return -1.0;
    }
    
    // Update sensor state
    sensor->last_distance = distance;
    spatial_log_reading(sensor, distance);
    clock_gettime(CLOCK_MONOTONIC, &sensor->last_reading);
    
    return distance;
}

int spatial_is_reading_valid(double distance) {
    return (distance >= MIN_DISTANCE_CM && distance <= MAX_DISTANCE_CM);
}

void spatial_log_reading(ultrasonic_sensor_t *sensor, double distance) {
    sensor->distance_history[sensor->history_index] = distance;
    sensor->history_index = (sensor->history_index + 1) % SENSOR_HISTORY_SIZE;
    
    // Update reliability based on reading consistency
    sensor->reliability = spatial_calculate_reliability(sensor);
}

double spatial_calculate_reliability(ultrasonic_sensor_t *sensor) {
    if (sensor->history_index < 3) return 1.0;
    
    double sum = 0.0;
    double sum_sq = 0.0;
    int valid_readings = 0;
    
    for (int i = 0; i < SENSOR_HISTORY_SIZE; i++) {
        if (spatial_is_reading_valid(sensor->distance_history[i])) {
            sum += sensor->distance_history[i];
            sum_sq += sensor->distance_history[i] * sensor->distance_history[i];
            valid_readings++;
        }
    }
    
    if (valid_readings < 3) return 0.5;
    
    double mean = sum / valid_readings;
    double variance = (sum_sq / valid_readings) - (mean * mean);
    double std_dev = sqrt(variance);
    
    // Reliability decreases with high variance
    double reliability = 1.0 - (std_dev / mean);
    return (reliability < 0.0) ? 0.0 : (reliability > 1.0) ? 1.0 : reliability;
}

double spatial_calculate_median(double *values, int count) {
    if (count == 0) return 0.0;
    
    // Simple bubble sort for small arrays
    for (int i = 0; i < count - 1; i++) {
        for (int j = 0; j < count - i - 1; j++) {
            if (values[j] > values[j + 1]) {
                double temp = values[j];
                values[j] = values[j + 1];
                values[j + 1] = temp;
            }
        }
    }
    
    if (count % 2 == 0) {
        return (values[count / 2 - 1] + values[count / 2]) / 2.0;
    } else {
        return values[count / 2];
    }
}

void spatial_update(spatial_awareness_t *spatial) {
    if (!spatial) return;
    
    struct timespec update_start, update_end;
    clock_gettime(CLOCK_MONOTONIC, &update_start);
    
    // Read all sensors
    for (int i = 0; i < spatial->sensor_count; i++) {
        spatial_read_sensor(&spatial->sensors[i]);
    }
    
    // Calculate distances
    spatial_calculate_distances(spatial);
    
    // Detect obstacles and edges
    spatial_detect_obstacles(spatial);
    spatial_detect_edges(spatial);
    
    // Update safety systems
    spatial_update_safety(spatial);
    
    // Update performance metrics
    clock_gettime(CLOCK_MONOTONIC, &update_end);
    double response_time = (update_end.tv_sec - update_start.tv_sec) * 1000.0 + 
                          (update_end.tv_nsec - update_start.tv_nsec) / 1000000.0;
    
    spatial->total_readings++;
    spatial->avg_response_time = (spatial->avg_response_time * (spatial->total_readings - 1) + response_time) / spatial->total_readings;
}

void spatial_calculate_distances(spatial_awareness_t *spatial) {
    // Calculate median distances for each direction
    double front_readings[SENSOR_HISTORY_SIZE];
    double left_readings[SENSOR_HISTORY_SIZE];
    double right_readings[SENSOR_HISTORY_SIZE];
    double rear_readings[SENSOR_HISTORY_SIZE];
    
    int front_count = 0, left_count = 0, right_count = 0, rear_count = 0;
    
    // Collect readings from all sensors (assuming sensor positions)
    for (int i = 0; i < spatial->sensor_count; i++) {
        ultrasonic_sensor_t *sensor = &spatial->sensors[i];
        if (sensor->is_active && spatial_is_reading_valid(sensor->last_distance)) {
            // Assign sensors to directions based on position
            // This is a simplified mapping - in practice, you'd configure actual positions
            switch (i) {
                case 0:  // Front sensor
                    front_readings[front_count++] = sensor->last_distance;
                    break;
                case 1:  // Left sensor
                    left_readings[left_count++] = sensor->last_distance;
                    break;
                case 2:  // Right sensor
                    right_readings[right_count++] = sensor->last_distance;
                    break;
                case 3:  // Rear sensor
                    rear_readings[rear_count++] = sensor->last_distance;
                    break;
            }
        }
    }
    
    // Calculate median distances
    spatial->front_distance = (front_count > 0) ? spatial_calculate_median(front_readings, front_count) : MAX_DISTANCE_CM;
    spatial->left_distance = (left_count > 0) ? spatial_calculate_median(left_readings, left_count) : MAX_DISTANCE_CM;
    spatial->right_distance = (right_count > 0) ? spatial_calculate_median(right_readings, right_count) : MAX_DISTANCE_CM;
    spatial->rear_distance = (rear_count > 0) ? spatial_calculate_median(rear_readings, rear_count) : MAX_DISTANCE_CM;
}

int spatial_detect_obstacles(spatial_awareness_t *spatial) {
    spatial->obstacle_detected = 0;
    spatial->obstacle_distance = MAX_DISTANCE_CM;
    spatial->obstacle_direction = 0;
    
    // Check front obstacle
    if (spatial->front_distance < OBSTACLE_THRESHOLD_CM) {
        spatial->obstacle_detected = 1;
        spatial->obstacle_distance = spatial->front_distance;
        spatial->obstacle_direction = 0;
        return 1;
    }
    
    // Check left obstacle
    if (spatial->left_distance < OBSTACLE_THRESHOLD_CM) {
        spatial->obstacle_detected = 1;
        spatial->obstacle_distance = spatial->left_distance;
        spatial->obstacle_direction = -1;
        return 1;
    }
    
    // Check right obstacle
    if (spatial->right_distance < OBSTACLE_THRESHOLD_CM) {
        spatial->obstacle_detected = 1;
        spatial->obstacle_distance = spatial->right_distance;
        spatial->obstacle_direction = 1;
        return 1;
    }
    
    return 0;
}

int spatial_detect_edges(spatial_awareness_t *spatial) {
    spatial->edge_detected = 0;
    spatial->edge_distance = MAX_DISTANCE_CM;
    spatial->edge_direction = 0;
    
    // Check for edges (very close readings or invalid readings)
    if (spatial->front_distance < EDGE_THRESHOLD_CM) {
        spatial->edge_detected = 1;
        spatial->edge_distance = spatial->front_distance;
        spatial->edge_direction = 0;
        return 1;
    }
    
    if (spatial->left_distance < EDGE_THRESHOLD_CM) {
        spatial->edge_detected = 1;
        spatial->edge_distance = spatial->left_distance;
        spatial->edge_direction = -1;
        return 1;
    }
    
    if (spatial->right_distance < EDGE_THRESHOLD_CM) {
        spatial->edge_detected = 1;
        spatial->edge_distance = spatial->right_distance;
        spatial->edge_direction = 1;
        return 1;
    }
    
    return 0;
}

void spatial_update_safety(spatial_awareness_t *spatial) {
    // Emergency stop conditions
    if (spatial->obstacle_detected && spatial->obstacle_distance < spatial->safety_margin) {
        spatial_emergency_stop(spatial);
    }
    
    if (spatial->edge_detected && spatial->edge_distance < spatial->safety_margin) {
        spatial_emergency_stop(spatial);
    }
}

double spatial_get_safe_speed(spatial_awareness_t *spatial, double desired_speed) {
    if (spatial->emergency_stop) {
        return 0.0;
    }
    
    if (spatial->obstacle_detected) {
        // Reduce speed based on obstacle distance
        double speed_factor = (spatial->obstacle_distance - spatial->safety_margin) / 
                             (OBSTACLE_THRESHOLD_CM - spatial->safety_margin);
        speed_factor = (speed_factor < 0.0) ? 0.0 : (speed_factor > 1.0) ? 1.0 : speed_factor;
        return desired_speed * speed_factor;
    }
    
    return desired_speed;
}

double spatial_get_safe_turn(spatial_awareness_t *spatial, double desired_turn) {
    if (spatial->emergency_stop) {
        return 0.0;
    }
    
    // Avoid turning towards obstacles
    if (spatial->obstacle_detected) {
        if (spatial->obstacle_direction == -1 && desired_turn < 0) {
            return 0.0;  // Don't turn left if obstacle on left
        }
        if (spatial->obstacle_direction == 1 && desired_turn > 0) {
            return 0.0;  // Don't turn right if obstacle on right
        }
    }
    
    return desired_turn;
}

void spatial_emergency_stop(spatial_awareness_t *spatial) {
    spatial->emergency_stop = 1;
    printf("[WARN]  EMERGENCY STOP: Obstacle/Edge detected at %.1f cm\n", 
           spatial->obstacle_detected ? spatial->obstacle_distance : spatial->edge_distance);
}

void spatial_reset_emergency(spatial_awareness_t *spatial) {
    spatial->emergency_stop = 0;
    printf("[OK] Emergency stop cleared\n");
}
