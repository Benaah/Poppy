#ifndef PID_H
#define PID_H

#include <time.h>
#include <math.h>

// Adaptive PID with neural network integration
struct adaptive_pid {
	// Traditional PID parameters
	double kp;
	double ki;
	double kd;

	// Adaptive parameters
	double adaptive_kp;
	double adaptive_ki;
	double adaptive_kd;
	
	// Learning rates for adaptation
	double learning_rate;
	double adaptation_factor;
	
	// Neural network weights (simplified RBF-like)
	double rbf_centers[3];  // Centers for radial basis functions
	double rbf_weights[3];  // Weights for each center
	double rbf_sigma;       // Gaussian width parameter
	
	// State variables
	double vi;
	double vd;
	double last;
	double last_error;
	double error_history[10];  // For trend analysis
	int history_index;
	
	// Bounds
	double pmin, pmax;
	double imin, iimin, imax, iimax;
	double dmin, dmax;
	
	// Performance metrics
	double performance_error;
	double adaptation_threshold;
	int adaptation_enabled;
};

struct pid {
	double kp;
	double ki;
	double kd;

	double vi;
	double vd;

	double pmin;
	double pmax;
	double imin, iimin;
	double imax, iimax;
	double dmin;
	double dmax;

	double last;
};

struct timespec get_time();
double get_dt(struct timespec *last);
double get_timediff(const struct timespec a, const struct timespec b);

double pid_update(struct pid *p, double feedback, double target, double dt);
struct pid pid_simple(double kp, double ki, double kd);

// Enhanced adaptive PID functions
struct adaptive_pid adaptive_pid_create(double kp, double ki, double kd, double learning_rate);
double adaptive_pid_update(struct adaptive_pid *pid, double feedback, double target, double dt);
void adaptive_pid_reset(struct adaptive_pid *pid);
void adaptive_pid_set_adaptation(struct adaptive_pid *pid, int enabled);
double rbf_activation(double input, double center, double sigma);

#endif
