/**
 * Poppy ESP32 Motor Controller Firmware
 * Manages hybrid locomotion system and sensor interfacing
 */

#include <Arduino.h>
#include <Wire.h>
#include <ESP32Servo.h>
#include <ArduinoJson.h>

// Servo objects
Servo trackLeft1, trackLeft2;
Servo trackRight1, trackRight2;
Servo legServos[8];  // 4 legs × 2 DOF
Servo panServo, tiltServo;

// Sensor pins
#define TOF_FRONT_ADDR 0x29
#define TOF_LEFT_ADDR 0x2A  
#define TOF_RIGHT_ADDR 0x2B
#define CLIFF_LEFT_PIN 34
#define CLIFF_RIGHT_PIN 35
#define BATTERY_PIN 36

// Motor pins
#define TRACK_LEFT1_PIN 13
#define TRACK_LEFT2_PIN 12
#define TRACK_RIGHT1_PIN 14
#define TRACK_RIGHT2_PIN 27
#define PAN_SERVO_PIN 25
#define TILT_SERVO_PIN 26

// Leg servo pins (example)
const int legPins[8] = {32, 33, 15, 2, 4, 16, 17, 5};

// State variables
uint8_t currentMode = 0;  // 0=TRACK, 1=LEG, 2=HYBRID
bool emergencyStop = false;
float batteryVoltage = 0.0;

// Constants
const float VOLTAGE_DIVIDER_RATIO = 3.3;  // 11.1V → 3.3V
const int NEUTRAL_PWM = 90;  // Continuous servo stop position

void setup() {
  Serial.begin(115200);
  Wire.begin();
  
  // Initialize servos
  trackLeft1.attach(TRACK_LEFT1_PIN);
  trackLeft2.attach(TRACK_LEFT2_PIN);
  trackRight1.attach(TRACK_RIGHT1_PIN);
  trackRight2.attach(TRACK_RIGHT2_PIN);
  
  panServo.attach(PAN_SERVO_PIN);
  tiltServo.attach(TILT_SERVO_PIN);
  
  for (int i = 0; i < 8; i++) {
    legServos[i].attach(legPins[i]);
  }
  
  // Initialize sensors
  pinMode(CLIFF_LEFT_PIN, INPUT);
  pinMode(CLIFF_RIGHT_PIN, INPUT);
  pinMode(BATTERY_PIN, INPUT);
  
  // Stop all motors
  stopAllMotors();
  
  Serial.println("{\"status\":\"ESP32 initialized\"}");
}

void loop() {
  // Check for commands from Jetson
  if (Serial.available() > 0) {
    String jsonStr = Serial.readStringUntil('\n');
    processCommand(jsonStr);
  }
  
  // Read and publish sensor data
  readSensors();
  publishSensorData();
  
  // Safety check - cliff detection
  if (digitalRead(CLIFF_LEFT_PIN) == HIGH || digitalRead(CLIFF_RIGHT_PIN) == HIGH) {
    emergencyStop = true;
    stopAllMotors();
    Serial.println("{\"event\":\"cliff_detected\",\"emergency_stop\":true}");
  }
  
  delay(20);  // 50Hz update rate
}

void processCommand(String jsonStr) {
  StaticJsonDocument<512> doc;
  DeserializationError error = deserializeJson(doc, jsonStr);
  
  if (error) {
    Serial.print("{\"error\":\"JSON parse failed: ");
    Serial.print(error.c_str());
    Serial.println("\"}");
    return;
  }
  
  String cmdType = doc["type"];
  
  if (cmdType == "movement") {
    handleMovementCommand(doc);
  } else if (cmdType == "velocity") {
    handleVelocityCommand(doc);
  } else if (cmdType == "servo") {
    handleServoCommand(doc);
  } else if (cmdType == "emergency_stop") {
    emergencyStop = true;
    stopAllMotors();
  } else if (cmdType == "clear_emergency") {
    emergencyStop = false;
  }
}

void handleMovementCommand(JsonDocument& doc) {
  if (emergencyStop) return;
  
  uint8_t cmdType = doc["cmd_type"];
  float distance = doc["distance"];
  float angle = doc["angle"];
  float speed = doc["speed"];
  uint8_t targetMode = doc["target_mode"];
  
  if (cmdType == 5) {  // TRANSFORM
    transformMode(targetMode);
  } else if (cmdType == 0) {  // FORWARD
    moveForward(distance, speed);
  } else if (cmdType == 1) {  // BACKWARD
    moveBackward(distance, speed);
  } else if (cmdType == 2) {  // TURN_LEFT
    turnLeft(angle, speed);
  } else if (cmdType == 3) {  // TURN_RIGHT
    turnRight(angle, speed);
  } else if (cmdType == 4) {  // STOP
    stopAllMotors();
  }
}

void handleVelocityCommand(JsonDocument& doc) {
  if (emergencyStop) return;
  
  float linearX = doc["linear_x"];
  float angularZ = doc["angular_z"];
  
  // Convert to track speeds
  if (currentMode == 0) {  // TRACK mode
    int leftSpeed = NEUTRAL_PWM + (linearX * 30) - (angularZ * 20);
    int rightSpeed = NEUTRAL_PWM + (linearX * 30) + (angularZ * 20);
    
    leftSpeed = constrain(leftSpeed, 0, 180);
    rightSpeed = constrain(rightSpeed, 0, 180);
    
    trackLeft1.write(leftSpeed);
    trackLeft2.write(leftSpeed);
    trackRight1.write(rightSpeed);
    trackRight2.write(rightSpeed);
  }
}

void handleServoCommand(JsonDocument& doc) {
  String servoName = doc["servo"];
  int angle = doc["angle"];
  
  if (servoName == "pan") {
    panServo.write(constrain(angle, 0, 180));
  } else if (servoName == "tilt") {
    tiltServo.write(constrain(angle, 0, 180));
  }
}

void transformMode(uint8_t newMode) {
  if (newMode == currentMode) return;
  
  Serial.print("{\"status\":\"transforming\",\"from\":");
  Serial.print(currentMode);
  Serial.print(",\"to\":");
  Serial.print(newMode);
  Serial.println("}");
  
  stopAllMotors();
  
  if (newMode == 0) {  // Transform to TRACK
    // Retract legs
    for (int i = 0; i < 8; i++) {
      legServos[i].write(90);  // Neutral position
    }
    delay(2000);
  } else if (newMode == 1) {  // Transform to LEG
    // Extend legs
    for (int i = 0; i < 8; i += 2) {
      legServos[i].write(45);    // Hip
      legServos[i+1].write(135); // Knee
    }
    delay(2000);
  }
  
  currentMode = newMode;
  Serial.println("{\"status\":\"transformation_complete\"}");
}

void moveForward(float distance_cm, float speed_pct) {
  int speedVal = map(speed_pct, 0, 100, 90, 120);
  
  trackLeft1.write(speedVal);
  trackLeft2.write(speedVal);
  trackRight1.write(speedVal);
  trackRight2.write(speedVal);
  
  // Calculate duration (simplified)
  unsigned long duration = (distance_cm / 10.0) * 1000;  // Rough estimate
  delay(duration);
  
  stopAllMotors();
}

void moveBackward(float distance_cm, float speed_pct) {
  int speedVal = map(speed_pct, 0, 100, 90, 60);
  
  trackLeft1.write(speedVal);
  trackLeft2.write(speedVal);
  trackRight1.write(speedVal);
  trackRight2.write(speedVal);
  
  unsigned long duration = (distance_cm / 10.0) * 1000;
  delay(duration);
  
  stopAllMotors();
}

void turnLeft(float angle_deg, float speed_pct) {
  int speedVal = map(speed_pct, 0, 100, 0, 30);
  
  trackLeft1.write(NEUTRAL_PWM - speedVal);
  trackLeft2.write(NEUTRAL_PWM - speedVal);
  trackRight1.write(NEUTRAL_PWM + speedVal);
  trackRight2.write(NEUTRAL_PWM + speedVal);
  
  unsigned long duration = (angle_deg / 90.0) * 1000;
  delay(duration);
  
  stopAllMotors();
}

void turnRight(float angle_deg, float speed_pct) {
  int speedVal = map(speed_pct, 0, 100, 0, 30);
  
  trackLeft1.write(NEUTRAL_PWM + speedVal);
  trackLeft2.write(NEUTRAL_PWM + speedVal);
  trackRight1.write(NEUTRAL_PWM - speedVal);
  trackRight2.write(NEUTRAL_PWM - speedVal);
  
  unsigned long duration = (angle_deg / 90.0) * 1000;
  delay(duration);
  
  stopAllMotors();
}

void stopAllMotors() {
  trackLeft1.write(NEUTRAL_PWM);
  trackLeft2.write(NEUTRAL_PWM);
  trackRight1.write(NEUTRAL_PWM);
  trackRight2.write(NEUTRAL_PWM);
}

void readSensors() {
  // Read battery voltage
  int adcValue = analogRead(BATTERY_PIN);
  batteryVoltage = (adcValue / 4095.0) * 3.3 * VOLTAGE_DIVIDER_RATIO;
}

void publishSensorData() {
  static unsigned long lastPublish = 0;
  unsigned long now = millis();
  
  if (now - lastPublish >= 100) {  // 10Hz
    lastPublish = now;
    
    StaticJsonDocument<256> doc;
    doc["battery_voltage"] = batteryVoltage;
    doc["locomotion_mode"] = currentMode;
    doc["emergency_stop"] = emergencyStop;
    doc["cliff_left"] = digitalRead(CLIFF_LEFT_PIN);
    doc["cliff_right"] = digitalRead(CLIFF_RIGHT_PIN);
    doc["timestamp"] = now;
    
    serializeJson(doc, Serial);
    Serial.println();
  }
}
