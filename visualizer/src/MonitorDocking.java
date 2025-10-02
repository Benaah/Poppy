import java.util.Scanner;

import static org.lwjgl.opengl.GL11.*;

public class MonitorDocking extends Monitor {
    public String dockingState = "IDLE";
    public double batteryVoltage = 0.0;
    public boolean isCharging = false;
    public boolean dockingStationFound = false;
    public int dockingAttempts = 0;
    public int successfulDockings = 0;
    
    public void onData(String str) {
        Scanner scanner = new Scanner(str);
        try {
            dockingState = scanner.next();
            batteryVoltage = scanner.nextDouble();
            isCharging = scanner.nextBoolean();
            dockingStationFound = scanner.nextBoolean();
            dockingAttempts = scanner.nextInt();
            successfulDockings = scanner.nextInt();
        } catch (Exception e) {
            // Handle parsing errors gracefully
        }
    }

    public void render2d(int width, int height) {
        // Docking status panel
        glTranslated(width - 250, 250, 0);
        drawDockingPanel();
        
        // Charging indicator
        glTranslated(0, 80, 0);
        drawChargingIndicator();
    }
    
    private void drawDockingPanel() {
        // Panel background
        glColor3f(0.1f, 0.1f, 0.1f);
        glBegin(GL_QUADS);
        glVertex2d(0, 0);
        glVertex2d(200, 0);
        glVertex2d(200, 60);
        glVertex2d(0, 60);
        glEnd();
        
        // State indicator
        if (dockingState.equals("DOCKED") || dockingState.equals("CHARGING")) {
            glColor3f(0.0f, 1.0f, 0.0f); // Green
        } else if (dockingState.equals("SEARCHING") || dockingState.equals("APPROACHING")) {
            glColor3f(1.0f, 1.0f, 0.0f); // Yellow
        } else if (dockingState.equals("ERROR")) {
            glColor3f(1.0f, 0.0f, 0.0f); // Red
        } else {
            glColor3f(0.5f, 0.5f, 0.5f); // Gray
        }
        
        glBegin(GL_QUADS);
        glVertex2d(5, 5);
        glVertex2d(195, 5);
        glVertex2d(195, 25);
        glVertex2d(5, 25);
        glEnd();
        
        // Station found indicator
        glTranslated(0, 30, 0);
        if (dockingStationFound) {
            glColor3f(0.0f, 1.0f, 0.0f);
        } else {
            glColor3f(1.0f, 0.0f, 0.0f);
        }
        glBegin(GL_QUADS);
        glVertex2d(5, 0);
        glVertex2d(25, 0);
        glVertex2d(25, 20);
        glVertex2d(5, 20);
        glEnd();
    }
    
    private void drawChargingIndicator() {
        // Charging status
        if (isCharging) {
            glColor3f(0.0f, 1.0f, 0.0f);
            // Animated charging effect
            double time = System.currentTimeMillis() / 1000.0;
            double pulse = (Math.sin(time * 4) + 1) / 2;
            glColor3f(0.0f, (float)pulse, 0.0f);
        } else {
            glColor3f(0.3f, 0.3f, 0.3f);
        }
        
        glBegin(GL_QUADS);
        glVertex2d(0, 0);
        glVertex2d(50, 0);
        glVertex2d(50, 20);
        glVertex2d(0, 20);
        glEnd();
        
        // Battery voltage bar
        glTranslated(60, 0, 0);
        double voltagePercent = Math.max(0, Math.min(1, (batteryVoltage - 6.0) / 2.4)); // 6V to 8.4V range
        
        glColor3f(0.2f, 0.2f, 0.2f);
        glBegin(GL_QUADS);
        glVertex2d(0, 0);
        glVertex2d(100, 0);
        glVertex2d(100, 20);
        glVertex2d(0, 20);
        glEnd();
        
        if (voltagePercent > 0.5) {
            glColor3f(0.0f, 1.0f, 0.0f);
        } else if (voltagePercent > 0.2) {
            glColor3f(1.0f, 1.0f, 0.0f);
        } else {
            glColor3f(1.0f, 0.0f, 0.0f);
        }
        
        glBegin(GL_QUADS);
        glVertex2d(2, 2);
        glVertex2d(2 + voltagePercent * 96, 2);
        glVertex2d(2 + voltagePercent * 96, 18);
        glVertex2d(2, 18);
        glEnd();
    }

    public String text() {
        return String.format("Docking: %s | Charging: %s | Station: %s | Attempts: %d/%d", 
                           dockingState, isCharging ? "YES" : "NO", 
                           dockingStationFound ? "FOUND" : "NOT FOUND",
                           successfulDockings, dockingAttempts);
    }
}
