#include <time.h>
#include "pid.h"

#define EPS 1e-9

struct timespec get_time() {
	struct timespec curr;
	clock_gettime(CLOCK_MONOTONIC, &curr); 
	return curr;
}

double get_dt(struct timespec *last) {
	struct timespec curr = get_time();
	double dt = curr.tv_sec - last->tv_sec + (curr.tv_nsec - last->tv_nsec) * 1e-9;
	*last = curr;
	return dt;
}

double get_timediff(const struct timespec a, const struct timespec b) {
	return a.tv_sec - b.tv_sec + (a.tv_nsec - b.tv_nsec) * 1e-9;
}

double clamp(double x, double min, double max) {
	return x < min ? min : (x > max ? max : x);
}

double pid_update(struct pid *pid_dat, double feedback, double target, double dt) {
	double err = feedback - target;

	double p = clamp(err * pid_dat->kp, pid_dat->pmin, pid_dat->pmax);

	pid_dat->vi = clamp(pid_dat->vi + (err * pid_dat->ki) * dt, pid_dat->iimin, pid_dat->iimax);

	double i = clamp(pid_dat->vi * pid_dat->ki, pid_dat->imin, pid_dat->imax);

	if(dt < EPS)
		return p + i;

	double d = clamp((err - pid_dat->last) / dt * pid_dat->kd, pid_dat->dmin, pid_dat->dmax);
	pid_dat->last = err;

	return p + i + d;
}

struct pid pid_simple(double kp, double ki, double kd) {
	struct pid p = {0};
	p.kp = kp;
	p.ki = ki;
	p.kd = kd;

	p.pmin = p.imin = p.iimin = p.dmin = -1.0 / 0.0;
	p.pmax = p.imax = p.iimax = p.dmax = 1.0 / 0.0;
	return p;
}

// Enhanced Adaptive PID Implementation
struct adaptive_pid adaptive_pid_create(double kp, double ki, double kd, double learning_rate) {
	struct adaptive_pid pid = {0};
	
	// Initialize traditional PID parameters
	pid.kp = kp;
	pid.ki = ki;
	pid.kd = kd;
	
	// Initialize adaptive parameters
	pid.adaptive_kp = kp;
	pid.adaptive_ki = ki;
	pid.adaptive_kd = kd;
	
	// Learning parameters
	pid.learning_rate = learning_rate;
	pid.adaptation_factor = 0.1;
	pid.adaptation_threshold = 0.1;
	pid.adaptation_enabled = 1;
	
	// Initialize RBF network parameters
	pid.rbf_centers[0] = -1.0;  // Low error
	pid.rbf_centers[1] = 0.0;   // Medium error
	pid.rbf_centers[2] = 1.0;   // High error
	pid.rbf_weights[0] = 1.0;
	pid.rbf_weights[1] = 1.0;
	pid.rbf_weights[2] = 1.0;
	pid.rbf_sigma = 0.5;
	
	// Initialize state
	pid.vi = 0.0;
	pid.vd = 0.0;
	pid.last = 0.0;
	pid.last_error = 0.0;
	pid.performance_error = 0.0;
	pid.history_index = 0;
	
	// Initialize bounds
	pid.pmin = pid.imin = pid.iimin = pid.dmin = -1.0 / 0.0;
	pid.pmax = pid.imax = pid.iimax = pid.dmax = 1.0 / 0.0;
	
	return pid;
}

double rbf_activation(double input, double center, double sigma) {
	double diff = input - center;
	return exp(-(diff * diff) / (2.0 * sigma * sigma));
}

double adaptive_pid_update(struct adaptive_pid *pid, double feedback, double target, double dt) {
	double err = feedback - target;
	
	// Store error in history for trend analysis
	pid->error_history[pid->history_index] = err;
	pid->history_index = (pid->history_index + 1) % 10;
	
	// Calculate RBF activations
	double rbf_output = 0.0;
	for(int i = 0; i < 3; i++) {
		rbf_output += pid->rbf_weights[i] * rbf_activation(err, pid->rbf_centers[i], pid->rbf_sigma);
	}
	
	// Adaptive parameter adjustment based on RBF output
	if(pid->adaptation_enabled) {
		double adaptation = (rbf_output - 1.0) * pid->adaptation_factor;
		pid->adaptive_kp = pid->kp * (1.0 + adaptation);
		pid->adaptive_ki = pid->ki * (1.0 + adaptation);
		pid->adaptive_kd = pid->kd * (1.0 + adaptation);
		
		// Clamp adaptive parameters to reasonable bounds
		pid->adaptive_kp = clamp(pid->adaptive_kp, pid->kp * 0.5, pid->kp * 2.0);
		pid->adaptive_ki = clamp(pid->adaptive_ki, pid->ki * 0.5, pid->ki * 2.0);
		pid->adaptive_kd = clamp(pid->adaptive_kd, pid->kd * 0.5, pid->kd * 2.0);
	}
	
	// Calculate PID terms using adaptive parameters
	double p = clamp(err * pid->adaptive_kp, pid->pmin, pid->pmax);
	
	pid->vi = clamp(pid->vi + (err * pid->adaptive_ki) * dt, pid->iimin, pid->iimax);
	double i = clamp(pid->vi * pid->adaptive_ki, pid->imin, pid->imax);
	
	double d = 0.0;
	if(dt > EPS) {
		d = clamp((err - pid->last) / dt * pid->adaptive_kd, pid->dmin, pid->dmax);
	}
	
	pid->last = err;
	pid->last_error = err;
	
	// Update performance metrics
	pid->performance_error = fabs(err);
	
	// Update RBF weights based on performance (simplified learning)
	if(pid->adaptation_enabled && fabs(err) > pid->adaptation_threshold) {
		for(int i = 0; i < 3; i++) {
			double activation = rbf_activation(err, pid->rbf_centers[i], pid->rbf_sigma);
			pid->rbf_weights[i] += pid->learning_rate * activation * err * 0.01;
			pid->rbf_weights[i] = clamp(pid->rbf_weights[i], 0.1, 2.0);
		}
	}
	
	return p + i + d;
}

void adaptive_pid_reset(struct adaptive_pid *pid) {
	pid->vi = 0.0;
	pid->vd = 0.0;
	pid->last = 0.0;
	pid->last_error = 0.0;
	pid->performance_error = 0.0;
	pid->history_index = 0;
	
	// Reset adaptive parameters to base values
	pid->adaptive_kp = pid->kp;
	pid->adaptive_ki = pid->ki;
	pid->adaptive_kd = pid->kd;
}

void adaptive_pid_set_adaptation(struct adaptive_pid *pid, int enabled) {
	pid->adaptation_enabled = enabled;
}