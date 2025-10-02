import java.util.Scanner;

import static org.lwjgl.opengl.GL11.*;

public class MonitorBattery extends Monitor {
    public double batteryLevel = 0.0;
    public double voltage = 0.0;
    public double current = 0.0;
    public String powerMode = "NORMAL";
    
    public void onData(String str) {
        Scanner scanner = new Scanner(str);
        try {
            batteryLevel = scanner.nextDouble();
            voltage = scanner.nextDouble();
            current = scanner.nextDouble();
            if (scanner.hasNext()) {
                powerMode = scanner.next();
            }
        } catch (Exception e) {
            // Handle parsing errors gracefully
        }
    }

    public void render2d(int width, int height) {
        // Battery level indicator
        glTranslated(width - 200, 20, 0);
        drawBatteryIndicator();
        
        // Power mode indicator
        glTranslated(0, 30, 0);
        drawPowerModeIndicator();
    }
    
    private void drawBatteryIndicator() {
        // Battery outline
        glColor3f(0.2f, 0.2f, 0.2f);
        glBegin(GL_LINE_LOOP);
        glVertex2d(0, 0);
        glVertex2d(60, 0);
        glVertex2d(60, 20);
        glVertex2d(65, 20);
        glVertex2d(65, 15);
        glVertex2d(70, 15);
        glVertex2d(70, 5);
        glVertex2d(65, 5);
        glVertex2d(65, 0);
        glVertex2d(0, 0);
        glEnd();
        
        // Battery fill based on level
        if (batteryLevel > 0) {
            if (batteryLevel > 0.5) {
                glColor3f(0.0f, 1.0f, 0.0f); // Green
            } else if (batteryLevel > 0.2) {
                glColor3f(1.0f, 1.0f, 0.0f); // Yellow
            } else {
                glColor3f(1.0f, 0.0f, 0.0f); // Red
            }
            
            glBegin(GL_QUADS);
            glVertex2d(2, 2);
            glVertex2d(2 + (batteryLevel * 58), 2);
            glVertex2d(2 + (batteryLevel * 58), 18);
            glVertex2d(2, 18);
            glEnd();
        }
    }
    
    private void drawPowerModeIndicator() {
        glColor3f(0.8f, 0.8f, 0.8f);
        glBegin(GL_QUADS);
        glVertex2d(0, 0);
        glVertex2d(80, 0);
        glVertex2d(80, 15);
        glVertex2d(0, 15);
        glEnd();
    }

    public String text() {
        return String.format("Battery: %.1f%% (%.1fV, %.1fA) [%s]", 
                           batteryLevel * 100, voltage, current, powerMode);
    }
}
