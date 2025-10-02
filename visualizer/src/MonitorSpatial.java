import java.util.Scanner;

import static org.lwjgl.opengl.GL11.*;

public class MonitorSpatial extends Monitor {
    public double frontDistance = 0.0;
    public double leftDistance = 0.0;
    public double rightDistance = 0.0;
    public boolean obstacleDetected = false;
    public boolean edgeDetected = false;
    public boolean emergencyStop = false;
    
    public void onData(String str) {
        Scanner scanner = new Scanner(str);
        try {
            frontDistance = scanner.nextDouble();
            leftDistance = scanner.nextDouble();
            rightDistance = scanner.nextDouble();
            obstacleDetected = scanner.nextBoolean();
            edgeDetected = scanner.nextBoolean();
            emergencyStop = scanner.nextBoolean();
        } catch (Exception e) {
            // Handle parsing errors gracefully
        }
    }

    public void render2d(int width, int height) {
        // Spatial awareness radar
        glTranslated(width - 300, 100, 0);
        drawSpatialRadar();
        
        // Obstacle indicators
        glTranslated(0, 120, 0);
        drawObstacleIndicators();
    }
    
    private void drawSpatialRadar() {
        int centerX = 100;
        int centerY = 100;
        int radius = 80;
        
        // Radar circle
        glColor3f(0.3f, 0.3f, 0.3f);
        glBegin(GL_LINE_LOOP);
        for (int i = 0; i < 360; i += 10) {
            double angle = Math.toRadians(i);
            double x = centerX + Math.cos(angle) * radius;
            double y = centerY + Math.sin(angle) * radius;
            glVertex2d(x, y);
        }
        glEnd();
        
        // Distance indicators
        drawDistanceLine(centerX, centerY, 0, frontDistance, 0.0f, 1.0f, 0.0f); // Front - Green
        drawDistanceLine(centerX, centerY, -90, leftDistance, 1.0f, 1.0f, 0.0f); // Left - Yellow
        drawDistanceLine(centerX, centerY, 90, rightDistance, 0.0f, 1.0f, 1.0f); // Right - Cyan
        
        // Robot center
        glColor3f(1.0f, 1.0f, 1.0f);
        glBegin(GL_QUADS);
        glVertex2d(centerX - 5, centerY - 5);
        glVertex2d(centerX + 5, centerY - 5);
        glVertex2d(centerX + 5, centerY + 5);
        glVertex2d(centerX - 5, centerY + 5);
        glEnd();
    }
    
    private void drawDistanceLine(int centerX, int centerY, int angle, double distance, float r, float g, float b) {
        if (distance > 0 && distance < 400) {
            double normalizedDistance = Math.min(distance / 200.0, 1.0);
            double rad = Math.toRadians(angle);
            double endX = centerX + Math.cos(rad) * normalizedDistance * 80;
            double endY = centerY + Math.sin(rad) * normalizedDistance * 80;
            
            glColor3f(r, g, b);
            glBegin(GL_LINES);
            glVertex2d(centerX, centerY);
            glVertex2d(endX, endY);
            glEnd();
        }
    }
    
    private void drawObstacleIndicators() {
        // Obstacle detected indicator
        if (obstacleDetected) {
            glColor3f(1.0f, 0.0f, 0.0f);
        } else {
            glColor3f(0.0f, 1.0f, 0.0f);
        }
        glBegin(GL_QUADS);
        glVertex2d(0, 0);
        glVertex2d(20, 0);
        glVertex2d(20, 20);
        glVertex2d(0, 20);
        glEnd();
        
        // Edge detected indicator
        glTranslated(30, 0, 0);
        if (edgeDetected) {
            glColor3f(1.0f, 1.0f, 0.0f);
        } else {
            glColor3f(0.5f, 0.5f, 0.5f);
        }
        glBegin(GL_QUADS);
        glVertex2d(0, 0);
        glVertex2d(20, 0);
        glVertex2d(20, 20);
        glVertex2d(0, 20);
        glEnd();
        
        // Emergency stop indicator
        glTranslated(30, 0, 0);
        if (emergencyStop) {
            glColor3f(1.0f, 0.0f, 0.0f);
        } else {
            glColor3f(0.0f, 0.0f, 0.0f);
        }
        glBegin(GL_QUADS);
        glVertex2d(0, 0);
        glVertex2d(20, 0);
        glVertex2d(20, 20);
        glVertex2d(0, 20);
        glEnd();
    }

    public String text() {
        return String.format("Spatial: F:%.1fcm L:%.1fcm R:%.1fcm Obstacle:%s Edge:%s", 
                           frontDistance, leftDistance, rightDistance, 
                           obstacleDetected ? "YES" : "NO", edgeDetected ? "YES" : "NO");
    }
}
