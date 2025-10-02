package robot;

import main.Poppy;
import org.eclipse.jetty.websocket.api.Session;
import org.eclipse.jetty.websocket.api.annotations.OnWebSocketClose;
import org.eclipse.jetty.websocket.api.annotations.OnWebSocketConnect;
import org.eclipse.jetty.websocket.api.annotations.OnWebSocketMessage;
import org.eclipse.jetty.websocket.api.annotations.WebSocket;
import org.eclipse.jetty.websocket.client.ClientUpgradeRequest;
import org.eclipse.jetty.websocket.client.WebSocketClient;

import java.io.IOException;
import java.net.URI;

@WebSocket
public class RobotSocket {

    private Robot instance;

    public RobotSocket(Robot robot){
        instance = robot;
    }

    @OnWebSocketConnect
    public void onConnect(Session user) throws Exception {
        System.out.println("Connects!!");
        try{
            user.getRemote().sendString("robotInit");
        }catch (IOException e){
            e.printStackTrace();
        }
    }

    @OnWebSocketClose
    public void onClose(Session user, int statusCode, String reason) {
        WebSocketClient client = new WebSocketClient();

        RobotSocket socket = new RobotSocket(instance);
        try {
            client.start();

            URI echoUri = new URI(Poppy.SERVER_SOCKET_URL);
            ClientUpgradeRequest request = new ClientUpgradeRequest();
            client.connect(socket,echoUri,request);
            System.out.println("Reconnecting...");
        }
        catch (Throwable t) {
            t.printStackTrace();
        }
    }


    /*
    *   Enhanced command support for 2025 hardware solutions:
    *   - Basic movement: move, turn
    *   - Enhanced features: find_face, dance, dock, calibrate, etc.
    *   - System control: battery_status, system_status, emergency_stop
    *   - Hardware control: motor_test, spatial_awareness, adaptive_pid
    **/
    @OnWebSocketMessage
    public void onMessage(Session user, String message) {
        System.out.println("Robot received: " + message);
        
        String[] args = message.split(",");
        String cmd = args[0];
        
        if(cmd.equals("getCode")){
            instance.executeCode();
        }
        // Enhanced command handling for 2025 hardware solutions
        else if (cmd.equals("find_face")) {
            System.out.println("Starting face detection...");
            // This would trigger the Python face detection system
            JackyCoolLib.sendToPython("find_face");
        }
        else if (cmd.equals("dance")) {
            System.out.println("Starting dance sequence...");
            JackyCoolLib.dance();
        }
        else if (cmd.equals("stop")) {
            System.out.println("Emergency stop activated");
            JackyCoolLib.emergencyStop();
        }
        else if (cmd.equals("calibrate")) {
            System.out.println("Starting system calibration...");
            JackyCoolLib.calibrate();
        }
        else if (cmd.equals("docking_start")) {
            System.out.println("Starting docking sequence...");
            JackyCoolLib.startDocking();
        }
        else if (cmd.equals("docking_stop")) {
            System.out.println("Stopping docking sequence...");
            JackyCoolLib.stopDocking();
        }
        else if (cmd.equals("emergency_stop")) {
            System.out.println("EMERGENCY STOP ACTIVATED");
            JackyCoolLib.emergencyStop();
        }
        else if (cmd.equals("battery_status")) {
            System.out.println("Requesting battery status...");
            JackyCoolLib.getBatteryStatus();
        }
        else if (cmd.equals("system_status")) {
            System.out.println("Requesting system status...");
            JackyCoolLib.getSystemStatus();
        }
        else if (cmd.equals("imu_calibrate")) {
            System.out.println("Starting IMU calibration...");
            JackyCoolLib.calibrateIMU();
        }
        else if (cmd.equals("spatial_calibrate")) {
            System.out.println("Starting spatial calibration...");
            JackyCoolLib.calibrateSpatial();
        }
        else if (cmd.equals("docking_calibrate")) {
            System.out.println("Starting docking calibration...");
            JackyCoolLib.calibrateDocking();
        }
        else if (cmd.equals("motor_test")) {
            System.out.println("Starting motor test...");
            JackyCoolLib.testMotors();
        }
        else if (cmd.equals("spatial_awareness_on")) {
            System.out.println("Enabling spatial awareness...");
            JackyCoolLib.setSpatialAwareness(true);
        }
        else if (cmd.equals("spatial_awareness_off")) {
            System.out.println("Disabling spatial awareness...");
            JackyCoolLib.setSpatialAwareness(false);
        }
        else if (cmd.equals("adaptive_pid_on")) {
            System.out.println("Enabling adaptive PID...");
            JackyCoolLib.setAdaptivePID(true);
        }
        else if (cmd.equals("adaptive_pid_off")) {
            System.out.println("Disabling adaptive PID...");
            JackyCoolLib.setAdaptivePID(false);
        }
        else if (cmd.equals("voice_control_on")) {
            System.out.println("Enabling voice control...");
            JackyCoolLib.setVoiceControl(true);
        }
        else if (cmd.equals("voice_control_off")) {
            System.out.println("Disabling voice control...");
            JackyCoolLib.setVoiceControl(false);
        }
        // Handle PID tuning command
        else if (cmd.equals("PID_TUNE") && args.length >= 4) {
            System.out.println("Tuning PID parameters...");
            double kp = Double.parseDouble(args[1]);
            double ki = Double.parseDouble(args[2]);
            double kd = Double.parseDouble(args[3]);
            JackyCoolLib.tunePID(kp, ki, kd);
        }
        // Handle basic movement commands
        else if (args.length >= 2) {
            try {
                double param = Double.parseDouble(args[1]);
                if (cmd.equals("move")){
                    JackyCoolLib.move(param);
                }else if (cmd.equals("turn")){
                    JackyCoolLib.turn(param);
                }
            } catch (NumberFormatException e) {
                System.err.println("Invalid parameter for command " + cmd + ": " + args[1]);
            }
        }
        else {
            System.out.println("Unknown command: " + cmd);
        }
    }

}
