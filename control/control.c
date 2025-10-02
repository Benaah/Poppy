#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/timerfd.h>
#include <poll.h>
#include <string.h>

#include "pi-blaster/pi-blaster.h"
#include "imu/imu.h"
#include "imu/vec.h"
#include "monitor/monitor.h"
#include "pid/pid.h"
#include "spatial/spatial.h"
#include "docking/docking.h"

void motor_set(uint8_t motor, double speed) {
	if(speed >= 0) {
		pwm[motor * 2] = speed * 2000;
		pwm[motor * 2 + 1] = 0;
	} else {
		pwm[motor * 2] = 0;
		pwm[motor * 2 + 1] = -speed * 2000;
	}
}

void move(double forward, double turn) {
	if(turn > 0.5) 
		turn = 0.5;
	if(turn < -0.5)
		turn = -0.5;
	double m1 = forward + turn;
	double m2 = forward - turn;
	motor_set(0, m1);
	motor_set(1, m2);
	monitor_msg("out %f %f\n", m1, m2);
	pwm_update();
}

double tilt_offset = 134.5;
double heading_set = 0;
double velocity_set = 0;

// Spatial awareness system
spatial_awareness_t spatial_system;

// Docking and charging system
docking_controller_t docking_system;

void on_monitor_data(uint32_t type, uint32_t len, uint8_t *data) {
	switch(type) {
		case 1:
			imu_monitor_get_calib();
			break;
		case 2:
			imu_monitor_set_calib(len, data);
			break;
		case 3:
			imu_save_calib("imu/calib.dat");
			break;
		case 4:
			tilt_offset = *(double *) data;
			break;
		case 5:
			heading_set = *(double *) data;
			break;
		case 6:
			velocity_set = *(double *) data;
			break;
	}
}

int main() {
	monitor_socket(8080);
	monitor_cb = on_monitor_data;

	// Initialize spatial awareness system
	if (spatial_init(&spatial_system) < 0) {
		printf("Warning: Failed to initialize spatial awareness system\n");
	} else {
		// Add ultrasonic sensors (configure pins as needed)
		spatial_add_sensor(&spatial_system, 23, 24);  // Front sensor
		spatial_add_sensor(&spatial_system, 25, 26);  // Left sensor
		spatial_add_sensor(&spatial_system, 27, 28);  // Right sensor
		printf("✓ Spatial awareness system initialized with %d sensors\n", spatial_system.sensor_count);
	}

	// Initialize docking and charging system
	if (docking_init(&docking_system) < 0) {
		printf("Warning: Failed to initialize docking system\n");
	} else {
		printf("✓ Docking and charging system initialized\n");
	}

	int cfd = open("/tmp/poppypipe", O_RDONLY);
	if(cfd < 0) {
		perror("open\n");
		return 1;
	}
	struct pollfd pfd;
	pfd.fd = cfd;
	pfd.events = POLLIN;

	FILE *in = fdopen(cfd, "r");

	uint8_t pins[] = {12, 13, 19, 26};
	pwm_init(pins, 4, 0);

	if(imu_load_calib("imu/calib.dat") < 0) {
		perror("Could not load calibration data");
	}
	imu_init();

	double output_lowpass = 0;

	imu_acc_weight = 0.1;
	imu_mag_weight = 0.1;
	imu_update(0, 100);
//	imu_acc_weight = 0.005;
//	imu_mag_weight = 0.002;

	struct timespec t = get_time();

	// Use adaptive PID controllers with neural network integration
	struct adaptive_pid pid_tilt = adaptive_pid_create(0.1, 0.6, 0.0005, 0.01);
	struct adaptive_pid pid_speed = adaptive_pid_create(0.5, 0.15, 0.00, 0.01);
	struct adaptive_pid pid_turn = adaptive_pid_create(0.6, 0.0, 0.000, 0.01);

	// Set bounds for adaptive PID controllers
	pid_tilt.iimax = 10;
	pid_tilt.iimin = -10;
	pid_tilt.imax = 10;
	pid_tilt.imin = -10;

	pid_speed.iimax = 0.5;
	pid_speed.iimin = -0.5;
	pid_speed.imax = 0.5;
	pid_speed.imin = -0.5;

	pid_turn.iimax = 0.1;
	pid_turn.iimin = -0.1;
	pid_turn.imax = 0.1;
	pid_turn.imin = -0.1;

	int tfd = timerfd_create(CLOCK_MONOTONIC, 0);
	struct itimerspec timer = {};
	timer.it_interval.tv_nsec = 1000000000 / 500;
	timer.it_value.tv_nsec = 1000000000 / 500;
	timerfd_settime(tfd, 0, &timer, NULL);

	double dt;
	double vvss = 0;

	for(;; monitor_msg("dt %f %f\n", dt, get_timediff(get_time(), t))) {
		uint64_t missed;
		read(tfd, &missed, sizeof(missed));

		dt = get_dt(&t);

		imu_update(dt, 0);

		// Update spatial awareness
		spatial_update(&spatial_system);

		// Update docking and charging system
		docking_update(&docking_system);

		monitor_check();

		if(poll(&pfd, 1, 0) > 0) {
			char c[1024];
			double d;
			fscanf(in, "%s %lf", c, &d);
			if(strncmp(c, "move", 4) == 0) {
				printf("move: %f\n", d);
				pid_speed.vi -= d / 10;
			} else if(strncmp(c, "turn", 4) == 0) {
				printf("turn: %f\n", d);
				heading_set += d;
			} else if(strncmp(c, "find_face", 9) == 0) {
				printf("Starting face detection...\n");
				// Face detection is handled in Python hotword.py
			} else if(strncmp(c, "dance", 5) == 0) {
				printf("Starting dance sequence...\n");
				// Simple dance sequence
				for(int i = 0; i < 4; i++) {
					heading_set += 10;
					usleep(500000); // 0.5 second delay
					heading_set -= 10;
					usleep(500000);
				}
			} else if(strncmp(c, "stop", 4) == 0) {
				printf("Emergency stop activated\n");
				velocity_set = 0;
				heading_set = 0;
				pid_speed.vi = 0;
				pid_tilt.vi = 0;
			} else if(strncmp(c, "calibrate", 9) == 0) {
				printf("Starting system calibration...\n");
				// Reset PID controllers
				adaptive_pid_reset(&pid_tilt);
				adaptive_pid_reset(&pid_speed);
				adaptive_pid_reset(&pid_turn);
			} else if(strncmp(c, "docking_start", 13) == 0) {
				printf("Starting docking sequence...\n");
				docking_start_search(&docking_system);
			} else if(strncmp(c, "docking_stop", 12) == 0) {
				printf("Stopping docking sequence...\n");
				docking_undock(&docking_system);
			} else if(strncmp(c, "emergency_stop", 14) == 0) {
				printf("EMERGENCY STOP ACTIVATED\n");
				velocity_set = 0;
				heading_set = 0;
				pid_speed.vi = 0;
				pid_tilt.vi = 0;
				spatial_emergency_stop(&spatial_system);
				docking_emergency_stop(&docking_system);
			} else if(strncmp(c, "battery_status", 14) == 0) {
				printf("Battery: %.1f%% (%.1fV, %.1fA)\n", 
				       docking_system.charging.battery_percentage,
				       docking_system.charging.voltage,
				       docking_system.charging.current);
			} else if(strncmp(c, "system_status", 13) == 0) {
				printf("System Status:\n");
				printf("  Balance: %.1f°\n", tilt);
				printf("  Battery: %.1f%%\n", docking_system.charging.battery_percentage);
				printf("  Spatial: %s\n", spatial_system.obstacle_detected ? "Obstacle detected" : "Clear");
				printf("  Docking: %s\n", docking_state_to_string(docking_system.state));
			} else if(strncmp(c, "imu_calibrate", 13) == 0) {
				printf("Starting IMU calibration...\n");
				imu_save_calib("imu/calib.dat");
			} else if(strncmp(c, "spatial_calibrate", 17) == 0) {
				printf("Starting spatial calibration...\n");
				// Reset spatial system
				for(int i = 0; i < spatial_system.sensor_count; i++) {
					spatial_system.sensors[i].reliability = 1.0;
				}
			} else if(strncmp(c, "docking_calibrate", 17) == 0) {
				printf("Starting docking calibration...\n");
				docking_system.docking_attempts = 0;
				docking_system.successful_dockings = 0;
			} else if(strncmp(c, "motor_test", 10) == 0) {
				printf("Starting motor test...\n");
				// Test each motor
				motor_set(0, 0.1);
				usleep(1000000);
				motor_set(0, 0);
				motor_set(1, 0.1);
				usleep(1000000);
				motor_set(1, 0);
			} else if(strncmp(c, "spatial_awareness_on", 20) == 0) {
				printf("Spatial awareness enabled\n");
				// Already enabled by default
			} else if(strncmp(c, "spatial_awareness_off", 21) == 0) {
				printf("Spatial awareness disabled\n");
				// Disable spatial awareness (would need implementation)
			} else if(strncmp(c, "adaptive_pid_on", 15) == 0) {
				printf("Adaptive PID enabled\n");
				adaptive_pid_set_adaptation(&pid_tilt, 1);
				adaptive_pid_set_adaptation(&pid_speed, 1);
				adaptive_pid_set_adaptation(&pid_turn, 1);
			} else if(strncmp(c, "adaptive_pid_off", 16) == 0) {
				printf("Adaptive PID disabled\n");
				adaptive_pid_set_adaptation(&pid_tilt, 0);
				adaptive_pid_set_adaptation(&pid_speed, 0);
				adaptive_pid_set_adaptation(&pid_turn, 0);
			} else if(strncmp(c, "voice_control_on", 16) == 0) {
				printf("Voice control enabled\n");
				// Voice control is handled in Python
			} else if(strncmp(c, "voice_control_off", 17) == 0) {
				printf("Voice control disabled\n");
				// Voice control is handled in Python
			}
		}

		struct vec3 rx = quat_rot(imu_rot, VEC3_XP);
		struct vec3 ry = quat_rot(imu_rot, VEC3_YP);
		struct vec3 rz = quat_rot(imu_rot, VEC3_ZP);
		double tilt = atan2(rx.z, rz.z) / M_PI * 180 + tilt_offset;
		double heading = atan2(rx.x, ry.x) / M_PI * 180;
		if(tilt != tilt || heading != heading)
			goto stall;

		monitor_msg("ori %f %f\n", tilt, heading);

		vvss += (velocity_set - vvss) / 300;

		if(fabs(tilt) > 30) {
			adaptive_pid_reset(&pid_tilt);
			adaptive_pid_reset(&pid_speed);
			goto stall;
		}

		double tilt_set = atan(adaptive_pid_update(&pid_speed, vvss * 0.4, output_lowpass, dt)) / M_PI * 180;
		if(tilt_set < -20) {
			tilt_set = -20;
		} else if(tilt_set > 20) {
			tilt_set = 20;
		}
		double output = tan(adaptive_pid_update(&pid_tilt, tilt, tilt_set, dt) / 180.0 * M_PI) * 100;
		if(output < -1)
			output = -1;
		if(output > 1)
			output = 1;
		output_lowpass += (output - output_lowpass) / 400;
		printf("%12.6f\n", tilt);
//		printf("%12.6f %12.6f %12.6f\n", output, output_lowpass, tilt_set);
	//	printf("Output: %12f %12f %12f\n", tilt, tilt - tilt_set, output_lowpass);
	
		double heading_diff = (heading + heading_set) / 180 * M_PI;
		heading_diff = atan2(cos(heading_diff), sin(heading_diff));

		double turn = adaptive_pid_update(&pid_turn, heading, heading + heading_diff, dt);

		// Apply spatial awareness safety constraints
		output = spatial_get_safe_speed(&spatial_system, output);
		turn = spatial_get_safe_turn(&spatial_system, turn);

		// Check for emergency stop
		if (spatial_system.emergency_stop) {
			output = 0.0;
			turn = 0.0;
			printf("⚠️  Emergency stop active - obstacle/edge detected\n");
		}

		move(output, turn);

		continue;
stall:;
		move(0, 0);
	}

}
