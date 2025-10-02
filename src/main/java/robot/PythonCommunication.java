package robot;

import org.eclipse.jetty.websocket.api.Session;
import org.eclipse.jetty.websocket.api.annotations.OnWebSocketClose;
import org.eclipse.jetty.websocket.api.annotations.OnWebSocketConnect;
import org.eclipse.jetty.websocket.api.annotations.OnWebSocketMessage;
import org.eclipse.jetty.websocket.api.annotations.WebSocket;

import java.io.IOException;


@WebSocket
public class PythonCommunication {

    @OnWebSocketConnect
    public void onConnect(Session user) throws Exception {

    }

    @OnWebSocketClose
    public void onClose(Session user, int statusCode, String reason) {}


    @OnWebSocketMessage
    public void onMessage(Session user, String message) {
        System.out.println("Python communication received: " + message);
        
        String[] args = message.split(",");
        String cmd = args[0];
        
        // Handle basic movement commands
        if (cmd.equals("move") && args.length >= 2) {
            try {
                double param = Double.parseDouble(args[1]);
                JackyCoolLib.move(param);
            } catch (NumberFormatException e) {
                System.err.println("Invalid move parameter: " + args[1]);
            }
        } else if (cmd.equals("turn") && args.length >= 2) {
            try {
                double param = Double.parseDouble(args[1]);
                JackyCoolLib.turn(param);
            } catch (NumberFormatException e) {
                System.err.println("Invalid turn parameter: " + args[1]);
            }
        }
        // Handle enhanced commands from Python
        else if (cmd.equals("find_face")) {
            JackyCoolLib.sendToPython("find_face");
        }
        else if (cmd.equals("dance")) {
            JackyCoolLib.dance();
        }
        else if (cmd.equals("stop")) {
            JackyCoolLib.emergencyStop();
        }
        else if (cmd.equals("calibrate")) {
            JackyCoolLib.calibrate();
        }
        else if (cmd.equals("docking_start")) {
            JackyCoolLib.startDocking();
        }
        else if (cmd.equals("docking_stop")) {
            JackyCoolLib.stopDocking();
        }
        else if (cmd.equals("emergency_stop")) {
            JackyCoolLib.emergencyStop();
        }
        else if (cmd.equals("battery_status")) {
            JackyCoolLib.getBatteryStatus();
        }
        else if (cmd.equals("system_status")) {
            JackyCoolLib.getSystemStatus();
        }
        else if (cmd.equals("imu_calibrate")) {
            JackyCoolLib.calibrateIMU();
        }
        else if (cmd.equals("spatial_calibrate")) {
            JackyCoolLib.calibrateSpatial();
        }
        else if (cmd.equals("docking_calibrate")) {
            JackyCoolLib.calibrateDocking();
        }
        else if (cmd.equals("motor_test")) {
            JackyCoolLib.testMotors();
        }
        else if (cmd.equals("spatial_awareness_on")) {
            JackyCoolLib.setSpatialAwareness(true);
        }
        else if (cmd.equals("spatial_awareness_off")) {
            JackyCoolLib.setSpatialAwareness(false);
        }
        else if (cmd.equals("adaptive_pid_on")) {
            JackyCoolLib.setAdaptivePID(true);
        }
        else if (cmd.equals("adaptive_pid_off")) {
            JackyCoolLib.setAdaptivePID(false);
        }
        else if (cmd.equals("voice_control_on")) {
            JackyCoolLib.setVoiceControl(true);
        }
        else if (cmd.equals("voice_control_off")) {
            JackyCoolLib.setVoiceControl(false);
        }
        // Handle PID tuning command
        else if (cmd.equals("PID_TUNE") && args.length >= 4) {
            try {
                double kp = Double.parseDouble(args[1]);
                double ki = Double.parseDouble(args[2]);
                double kd = Double.parseDouble(args[3]);
                JackyCoolLib.tunePID(kp, ki, kd);
            } catch (NumberFormatException e) {
                System.err.println("Invalid PID parameters");
            }
        }
        else {
            System.out.println("Unknown command from Python: " + cmd);
        }
    }

}
