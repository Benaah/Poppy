package robot;

import java.io.BufferedWriter;
import java.io.FileOutputStream;
import java.io.FileWriter;
import java.io.IOException;

public class JackyCoolLib {

    private static boolean enablePipe = true;

//    private static BufferedWriter bw;

    private static FileOutputStream fos;
    static {
        if (enablePipe) {
            try {
                fos = new FileOutputStream("/tmp/poppypipe");
//                bw = new BufferedWriter(new FileWriter("/tmp/poppypipe"));
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }

    // Basic movement methods
    public static void move(double vec){
        sendpipe("move " + vec);
    }
    
    public static void turn(double degree){
        sendpipe("turn " + degree);
    }

    // Enhanced methods for hardware solutions
    public static void sendToPython(String command) {
        sendpipe(command);
    }
    
    public static void dance() {
        sendpipe("dance");
    }
    
    public static void emergencyStop() {
        sendpipe("emergency_stop");
    }
    
    public static void calibrate() {
        sendpipe("calibrate");
    }
    
    public static void startDocking() {
        sendpipe("docking_start");
    }
    
    public static void stopDocking() {
        sendpipe("docking_stop");
    }
    
    public static void getBatteryStatus() {
        sendpipe("battery_status");
    }
    
    public static void getSystemStatus() {
        sendpipe("system_status");
    }
    
    public static void calibrateIMU() {
        sendpipe("imu_calibrate");
    }
    
    public static void calibrateSpatial() {
        sendpipe("spatial_calibrate");
    }
    
    public static void calibrateDocking() {
        sendpipe("docking_calibrate");
    }
    
    public static void testMotors() {
        sendpipe("motor_test");
    }
    
    public static void setSpatialAwareness(boolean enabled) {
        sendpipe(enabled ? "spatial_awareness_on" : "spatial_awareness_off");
    }
    
    public static void setAdaptivePID(boolean enabled) {
        sendpipe(enabled ? "adaptive_pid_on" : "adaptive_pid_off");
    }
    
    public static void setVoiceControl(boolean enabled) {
        sendpipe(enabled ? "voice_control_on" : "voice_control_off");
    }
    
    public static void tunePID(double kp, double ki, double kd) {
        sendpipe("PID_TUNE " + kp + " " + ki + " " + kd);
    }

    public static void sendpipe(String s){
        if (enablePipe) {
            try {
                fos.write((s+"\n").getBytes());
                fos.flush();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        System.out.println(s);
    }

}
