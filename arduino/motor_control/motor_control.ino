/*
 * Poppy Robot - Arduino Motor Control System
 * Real-time motor control with PID and safety systems
 * Optimized for hardware challenges
 */

#include <Wire.h>
#include <PID_v1.h>
#include <Encoder.h>

// Motor control pins
#define MOTOR_LEFT_PWM 5
#define MOTOR_LEFT_DIR1 6
#define MOTOR_LEFT_DIR2 7
#define MOTOR_RIGHT_PWM 9
#define MOTOR_RIGHT_DIR1 10
#define MOTOR_RIGHT_DIR2 11

// Encoder pins
#define ENCODER_LEFT_A 2
#define ENCODER_LEFT_B 3
#define ENCODER_RIGHT_A 18
#define ENCODER_RIGHT_B 19

// Safety pins
#define EMERGENCY_STOP_PIN 12
#define BATTERY_MONITOR_PIN A0

// Communication
#define I2C_ADDRESS 0x08
#define COMMAND_BUFFER_SIZE 32

// Motor control variables
double leftTargetSpeed = 0;
double leftCurrentSpeed = 0;
double leftOutput = 0;

double rightTargetSpeed = 0;
double rightCurrentSpeed = 0;
double rightOutput = 0;

// PID controllers
PID leftPID(&leftCurrentSpeed, &leftOutput, &leftTargetSpeed, 2.0, 5.0, 1.0, DIRECT);
PID rightPID(&rightCurrentSpeed, &rightOutput, &rightTargetSpeed, 2.0, 5.0, 1.0, DIRECT);

// Encoders
Encoder leftEncoder(ENCODER_LEFT_A, ENCODER_LEFT_B);
Encoder rightEncoder(ENCODER_RIGHT_A, ENCODER_RIGHT_B);

// Safety and monitoring
bool emergencyStop = false;
float batteryVoltage = 0;
unsigned long lastSafetyCheck = 0;
unsigned long lastSpeedUpdate = 0;

// Communication
char commandBuffer[COMMAND_BUFFER_SIZE];
int commandIndex = 0;

// Performance monitoring
unsigned long loopCount = 0;
unsigned long lastPerformanceReport = 0;

void setup() {
  Serial.begin(115200);
  Wire.begin(I2C_ADDRESS);
  Wire.onReceive(receiveCommand);
  Wire.onRequest(sendStatus);
  
  // Initialize motor pins
  pinMode(MOTOR_LEFT_PWM, OUTPUT);
  pinMode(MOTOR_LEFT_DIR1, OUTPUT);
  pinMode(MOTOR_LEFT_DIR2, OUTPUT);
  pinMode(MOTOR_RIGHT_PWM, OUTPUT);
  pinMode(MOTOR_RIGHT_DIR1, OUTPUT);
  pinMode(MOTOR_RIGHT_DIR2, OUTPUT);
  
  // Initialize safety pins
  pinMode(EMERGENCY_STOP_PIN, INPUT_PULLUP);
  pinMode(BATTERY_MONITOR_PIN, INPUT);
  
  // Configure PID controllers
  leftPID.SetMode(AUTOMATIC);
  leftPID.SetOutputLimits(-255, 255);
  leftPID.SetSampleTime(1); // 1ms sample time for 1kHz control loop
  
  rightPID.SetMode(AUTOMATIC);
  rightPID.SetOutputLimits(-255, 255);
  rightPID.SetSampleTime(1);
  
  // Initialize safety systems
  checkEmergencyStop();
  updateBatteryVoltage();
  
  Serial.println("Poppy Arduino Motor Control System Ready");
  Serial.println("I2C Address: 0x08");
  Serial.println("Control Loop: 1kHz");
}

void loop() {
  unsigned long currentTime = millis();
  
  // Safety check every 10ms
  if (currentTime - lastSafetyCheck >= 10) {
    checkEmergencyStop();
    updateBatteryVoltage();
    lastSafetyCheck = currentTime;
  }
  
  // Speed update every 1ms for 1kHz control loop
  if (currentTime - lastSpeedUpdate >= 1) {
    updateMotorSpeeds();
    lastSpeedUpdate = currentTime;
  }
  
  // Performance monitoring every 5 seconds
  if (currentTime - lastPerformanceReport >= 5000) {
    reportPerformance();
    lastPerformanceReport = currentTime;
  }
  
  loopCount++;
}

void updateMotorSpeeds() {
  if (emergencyStop) {
    stopMotors();
    return;
  }
  
  // Read encoder positions and calculate speeds
  static long leftLastPosition = 0;
  static long rightLastPosition = 0;
  
  long leftPosition = leftEncoder.read();
  long rightPosition = rightEncoder.read();
  
  // Calculate speed (pulses per millisecond)
  leftCurrentSpeed = (leftPosition - leftLastPosition) * 1000.0;
  rightCurrentSpeed = (rightPosition - rightLastPosition) * 1000.0;
  
  leftLastPosition = leftPosition;
  rightLastPosition = rightPosition;
  
  // Update PID controllers
  leftPID.Compute();
  rightPID.Compute();
  
  // Apply motor outputs
  setMotorSpeed(0, leftOutput);  // Left motor
  setMotorSpeed(1, rightOutput); // Right motor
}

void setMotorSpeed(int motor, double speed) {
  int pwmPin, dir1Pin, dir2Pin;
  
  if (motor == 0) { // Left motor
    pwmPin = MOTOR_LEFT_PWM;
    dir1Pin = MOTOR_LEFT_DIR1;
    dir2Pin = MOTOR_LEFT_DIR2;
  } else { // Right motor
    pwmPin = MOTOR_RIGHT_PWM;
    dir1Pin = MOTOR_RIGHT_DIR1;
    dir2Pin = MOTOR_RIGHT_DIR2;
  }
  
  // Constrain speed to valid range
  speed = constrain(speed, -255, 255);
  
  if (speed > 0) {
    digitalWrite(dir1Pin, HIGH);
    digitalWrite(dir2Pin, LOW);
    analogWrite(pwmPin, (int)speed);
  } else if (speed < 0) {
    digitalWrite(dir1Pin, LOW);
    digitalWrite(dir2Pin, HIGH);
    analogWrite(pwmPin, (int)(-speed));
  } else {
    digitalWrite(dir1Pin, LOW);
    digitalWrite(dir2Pin, LOW);
    analogWrite(pwmPin, 0);
  }
}

void stopMotors() {
  setMotorSpeed(0, 0);
  setMotorSpeed(1, 0);
  leftTargetSpeed = 0;
  rightTargetSpeed = 0;
}

void checkEmergencyStop() {
  emergencyStop = digitalRead(EMERGENCY_STOP_PIN) == LOW;
  if (emergencyStop) {
    stopMotors();
  }
}

void updateBatteryVoltage() {
  int rawValue = analogRead(BATTERY_MONITOR_PIN);
  batteryVoltage = (rawValue * 5.0 * 4.0) / 1024.0; // Voltage divider with 4:1 ratio
}

void receiveCommand(int byteCount) {
  commandIndex = 0;
  while (Wire.available() && commandIndex < COMMAND_BUFFER_SIZE - 1) {
    char c = Wire.read();
    commandBuffer[commandIndex] = c;
    commandIndex++;
  }
  commandBuffer[commandIndex] = '\0';
  
  processCommand();
}

void processCommand() {
  if (strlen(commandBuffer) == 0) return;
  
  char* token = strtok(commandBuffer, ",");
  if (token == NULL) return;
  
  String command = String(token);
  
  if (command == "MOVE") {
    // Format: MOVE,left_speed,right_speed
    token = strtok(NULL, ",");
    if (token != NULL) leftTargetSpeed = atof(token);
    token = strtok(NULL, ",");
    if (token != NULL) rightTargetSpeed = atof(token);
  }
  else if (command == "STOP") {
    stopMotors();
  }
  else if (command == "EMERGENCY") {
    emergencyStop = true;
    stopMotors();
  }
  else if (command == "RESET") {
    emergencyStop = false;
    leftPID.SetMode(AUTOMATIC);
    rightPID.SetMode(AUTOMATIC);
  }
  else if (command == "PID_TUNE") {
    // Format: PID_TUNE,kp,ki,kd
    token = strtok(NULL, ",");
    if (token != NULL) {
      double kp = atof(token);
      token = strtok(NULL, ",");
      if (token != NULL) {
        double ki = atof(token);
        token = strtok(NULL, ",");
        if (token != NULL) {
          double kd = atof(token);
          leftPID.SetTunings(kp, ki, kd);
          rightPID.SetTunings(kp, ki, kd);
        }
      }
    }
  }
}

void sendStatus() {
  // Send status data to Raspberry Pi
  String status = String(leftCurrentSpeed) + "," + 
                  String(rightCurrentSpeed) + "," + 
                  String(batteryVoltage) + "," + 
                  String(emergencyStop ? 1 : 0);
  
  Wire.write(status.c_str());
}

void reportPerformance() {
  Serial.print("Performance - Loop Count: ");
  Serial.print(loopCount);
  Serial.print(", Left Speed: ");
  Serial.print(leftCurrentSpeed);
  Serial.print(", Right Speed: ");
  Serial.print(rightCurrentSpeed);
  Serial.print(", Battery: ");
  Serial.print(batteryVoltage);
  Serial.print("V, Emergency Stop: ");
  Serial.println(emergencyStop ? "YES" : "NO");
  
  loopCount = 0;
}

// Safety functions
void emergencyStopSequence() {
  emergencyStop = true;
  stopMotors();
  
  // Send emergency signal to Raspberry Pi
  Wire.beginTransmission(0x09); // Raspberry Pi I2C address
  Wire.write("EMERGENCY_STOP");
  Wire.endTransmission();
}

// Calibration functions
void calibrateEncoders() {
  leftEncoder.write(0);
  rightEncoder.write(0);
  Serial.println("Encoders calibrated");
}

#include <PID_AutoTune_v0.h>

void calibratePID() {
  // Full auto-tune of PID parameters for both motors
  const double setpoint = 50.0; // Target speed for tuning (adjust as needed)
  const int outputStep = 50;    // Output step for auto-tune
  const int lookBack = 20;      // Number of samples to look back for auto-tune
  const unsigned long tuneTimeout = 15000; // Timeout for auto-tune in ms

  double leftInput = 0, leftOutput = 0;
  double rightInput = 0, rightOutput = 0;

  PID_ATune leftAutoTune(&leftInput, &leftOutput);
  PID_ATune rightAutoTune(&rightInput, &rightOutput);

  leftAutoTune.SetOutputStep(outputStep);
  leftAutoTune.SetControlType(1); // PI or PID
  leftAutoTune.SetLookbackSec(lookBack);
  leftAutoTune.SetNoiseBand(1);

  rightAutoTune.SetOutputStep(outputStep);
  rightAutoTune.SetControlType(1);
  rightAutoTune.SetLookbackSec(lookBack);
  rightAutoTune.SetNoiseBand(1);

  Serial.println("Starting PID auto-tune for left motor...");
  leftTargetSpeed = setpoint;
  unsigned long start = millis();
  while (leftAutoTune.Runtime() != 1) {
    leftInput = leftCurrentSpeed;
    leftOutput = leftOutput; // Output will be set by auto-tune
    analogWrite(MOTOR_LEFT_PWM, constrain(leftOutput, 0, 255));
    if (millis() - start > tuneTimeout) {
      Serial.println("Left motor PID auto-tune timed out.");
      break;
    }
    delay(10);
  }
  double leftKp = leftAutoTune.GetKp();
  double leftKi = leftAutoTune.GetKi();
  double leftKd = leftAutoTune.GetKd();
  leftPID.SetTunings(leftKp, leftKi, leftKd);
  analogWrite(MOTOR_LEFT_PWM, 0);

  Serial.print("Left PID tuned: Kp=");
  Serial.print(leftKp, 4);
  Serial.print(", Ki=");
  Serial.print(leftKi, 4);
  Serial.print(", Kd=");
  Serial.println(leftKd, 4);

  Serial.println("Starting PID auto-tune for right motor...");
  rightTargetSpeed = setpoint;
  start = millis();
  while (rightAutoTune.Runtime() != 1) {
    rightInput = rightCurrentSpeed;
    rightOutput = rightOutput;
    analogWrite(MOTOR_RIGHT_PWM, constrain(rightOutput, 0, 255));
    if (millis() - start > tuneTimeout) {
      Serial.println("Right motor PID auto-tune timed out.");
      break;
    }
    delay(10);
  }
  double rightKp = rightAutoTune.GetKp();
  double rightKi = rightAutoTune.GetKi();
  double rightKd = rightAutoTune.GetKd();
  rightPID.SetTunings(rightKp, rightKi, rightKd);
  analogWrite(MOTOR_RIGHT_PWM, 0);

  Serial.print("Right PID tuned: Kp=");
  Serial.print(rightKp, 4);
  Serial.print(", Ki=");
  Serial.print(rightKi, 4);
  Serial.print(", Kd=");
  Serial.println(rightKd, 4);

  Serial.println("PID parameters auto-tuned and applied.");
}
