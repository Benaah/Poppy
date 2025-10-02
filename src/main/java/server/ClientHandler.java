package server;

import org.eclipse.jetty.websocket.api.Session;
import org.eclipse.jetty.websocket.api.annotations.OnWebSocketClose;
import org.eclipse.jetty.websocket.api.annotations.OnWebSocketConnect;
import org.eclipse.jetty.websocket.api.annotations.OnWebSocketMessage;
import org.eclipse.jetty.websocket.api.annotations.WebSocket;

import java.io.IOException;
import java.util.concurrent.ConcurrentHashMap;
import java.util.Map;

@WebSocket
public class ClientHandler {

    private Session robot;
    private int stepDist = 1;
    
    // Enhanced command handling for 2025 hardware solutions
    private static final Map<String, String> ENHANCED_COMMANDS = new ConcurrentHashMap<>();
    
    static {
        // Initialize enhanced command mappings
        ENHANCED_COMMANDS.put("find_face", "find_face");
        ENHANCED_COMMANDS.put("dance", "dance");
        ENHANCED_COMMANDS.put("stop", "stop");
        ENHANCED_COMMANDS.put("calibrate", "calibrate");
        ENHANCED_COMMANDS.put("dock", "docking_start");
        ENHANCED_COMMANDS.put("undock", "docking_stop");
        ENHANCED_COMMANDS.put("emergency_stop", "emergency_stop");
        ENHANCED_COMMANDS.put("battery_status", "battery_status");
        ENHANCED_COMMANDS.put("system_status", "system_status");
        ENHANCED_COMMANDS.put("imu_calibrate", "imu_calibrate");
        ENHANCED_COMMANDS.put("spatial_calibrate", "spatial_calibrate");
        ENHANCED_COMMANDS.put("docking_calibrate", "docking_calibrate");
        ENHANCED_COMMANDS.put("motor_test", "motor_test");
        ENHANCED_COMMANDS.put("spatial_awareness_on", "spatial_awareness_on");
        ENHANCED_COMMANDS.put("spatial_awareness_off", "spatial_awareness_off");
        ENHANCED_COMMANDS.put("adaptive_pid_on", "adaptive_pid_on");
        ENHANCED_COMMANDS.put("adaptive_pid_off", "adaptive_pid_off");
        ENHANCED_COMMANDS.put("voice_control_on", "voice_control_on");
        ENHANCED_COMMANDS.put("voice_control_off", "voice_control_off");
    }

    @OnWebSocketConnect
    public void onConnect(Session user) throws Exception {
        System.out.println("Connected user: " + user.getRemoteAddress());
    }

    @OnWebSocketClose
    public void onClose(Session user, int statusCode, String reason) {
        System.out.println("User disconnected: " + reason);
    }

    private final static double revDist = 0.2;
    
    @OnWebSocketMessage
    public void onMessage(Session user, String message) {
        System.out.println("Received message: " + message);
        
        if (message.equals("robotInit")){
            System.out.println("Robot initialized!");
            robot = user;
            return;
        }
        
        // Enhanced command processing for 2025 hardware solutions
        if(message.startsWith("cmd ")){
            try {
                String[] parts = message.split(" ", 3);
                String cmd = parts[1];
                
                // Handle basic movement commands
                if (cmd.equals("moveForwards"))
                    sendToRobot("move," + revDist);
                else if (cmd.equals("moveBackwards"))
                    sendToRobot("move," + (revDist * -1));
                else if (cmd.equals("move") && parts.length > 2)
                    sendToRobot("move," + parts[2]);
                else if (cmd.equals("turn") && parts.length > 2)
                    sendToRobot("turn," + parts[2]);
                
                // Handle enhanced commands
                else if (ENHANCED_COMMANDS.containsKey(cmd)) {
                    String robotCommand = ENHANCED_COMMANDS.get(cmd);
                    sendToRobot(robotCommand);
                    System.out.println("Enhanced command sent: " + cmd + " -> " + robotCommand);
                }
                
                // Handle parameterized enhanced commands
                else if (cmd.equals("move_motors") && parts.length > 3) {
                    sendToRobot("move," + parts[2] + "," + parts[3]);
                }
                else if (cmd.equals("tune_pid") && parts.length > 4) {
                    sendToRobot("PID_TUNE," + parts[2] + "," + parts[3] + "," + parts[4]);
                }
                else if (cmd.equals("custom") && parts.length > 2) {
                    sendToRobot(parts[2]); // Send custom command directly
                }
                
                else {
                    System.out.println("Unknown command: " + cmd);
                }
                
            } catch (Exception e) {
                System.err.println("Error processing command: " + e.getMessage());
                e.printStackTrace();
            }
        }
        
        // Handle direct robot commands (for Python integration)
        else if (message.contains(",")) {
            sendToRobot(message);
        }
    }
    
    private void sendToRobot(String command) {
        if (robot != null && robot.isOpen()) {
            try {
                robot.getRemote().sendString(command);
                System.out.println("Sent to robot: " + command);
            } catch (IOException e) {
                System.err.println("Failed to send command to robot: " + e.getMessage());
            }
        } else {
            System.err.println("Robot not connected, cannot send command: " + command);
        }
    }

    public void sendUpdateCodeQuery(){
        try{
            robot.getRemote().sendString("getCode");
        }catch (IOException e){
            e.printStackTrace();
        }
    }
    
    public Session getRobot() {
        return robot;
    }
}
