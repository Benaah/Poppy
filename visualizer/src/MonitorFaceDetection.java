import java.util.Scanner;

import static org.lwjgl.opengl.GL11.*;

public class MonitorFaceDetection extends Monitor {
    public int faceCount = 0;
    public String lightingMode = "UNKNOWN";
    public double processingTime = 0.0;
    public double avgProcessingTime = 0.0;
    public int detectionCount = 0;
    public boolean isActive = false;
    
    public void onData(String str) {
        Scanner scanner = new Scanner(str);
        try {
            faceCount = scanner.nextInt();
            lightingMode = scanner.next();
            processingTime = scanner.nextDouble();
            avgProcessingTime = scanner.nextDouble();
            detectionCount = scanner.nextInt();
            isActive = scanner.nextBoolean();
        } catch (Exception e) {
            // Handle parsing errors gracefully
        }
    }

    public void render2d(int width, int height) {
        // Face detection status panel
        glTranslated(width - 300, 400, 0);
        drawFaceDetectionPanel();
        
        // Processing time graph
        glTranslated(0, 100, 0);
        drawProcessingTimeGraph();
    }
    
    private void drawFaceDetectionPanel() {
        // Panel background
        glColor3f(0.1f, 0.1f, 0.1f);
        glBegin(GL_QUADS);
        glVertex2d(0, 0);
        glVertex2d(250, 0);
        glVertex2d(250, 80);
        glVertex2d(0, 80);
        glEnd();
        
        // Active indicator
        if (isActive) {
            glColor3f(0.0f, 1.0f, 0.0f);
        } else {
            glColor3f(0.5f, 0.5f, 0.5f);
        }
        glBegin(GL_QUADS);
        glVertex2d(5, 5);
        glVertex2d(20, 5);
        glVertex2d(20, 20);
        glVertex2d(5, 20);
        glEnd();
        
        // Face count indicator
        glTranslated(30, 0, 0);
        for (int i = 0; i < Math.min(faceCount, 10); i++) {
            glColor3f(1.0f, 1.0f, 0.0f);
            glBegin(GL_QUADS);
            glVertex2d(i * 15, 5);
            glVertex2d(i * 15 + 10, 5);
            glVertex2d(i * 15 + 10, 15);
            glVertex2d(i * 15 + 10, 15);
            glEnd();
        }
        
        // Lighting mode indicator
        glTranslated(0, 25, 0);
        if (lightingMode.equals("BRIGHT")) {
            glColor3f(1.0f, 1.0f, 1.0f);
        } else if (lightingMode.equals("DARK")) {
            glColor3f(0.2f, 0.2f, 0.2f);
        } else if (lightingMode.equals("NORMAL")) {
            glColor3f(0.5f, 0.5f, 0.5f);
        } else {
            glColor3f(0.8f, 0.8f, 0.0f);
        }
        glBegin(GL_QUADS);
        glVertex2d(0, 0);
        glVertex2d(50, 0);
        glVertex2d(50, 20);
        glVertex2d(0, 20);
        glEnd();
    }
    
    private void drawProcessingTimeGraph() {
        // Graph background
        glColor3f(0.05f, 0.05f, 0.05f);
        glBegin(GL_QUADS);
        glVertex2d(0, 0);
        glVertex2d(200, 0);
        glVertex2d(200, 50);
        glVertex2d(0, 50);
        glEnd();
        
        // Processing time bar
        double normalizedTime = Math.min(processingTime * 1000, 100); // Convert to ms, cap at 100ms
        glColor3f(0.0f, 1.0f, 0.0f);
        if (normalizedTime > 50) {
            glColor3f(1.0f, 1.0f, 0.0f);
        }
        if (normalizedTime > 80) {
            glColor3f(1.0f, 0.0f, 0.0f);
        }
        
        glBegin(GL_QUADS);
        glVertex2d(5, 5);
        glVertex2d(5 + normalizedTime * 1.9, 5);
        glVertex2d(5 + normalizedTime * 1.9, 45);
        glVertex2d(5, 45);
        glEnd();
    }

    public String text() {
        return String.format("Faces: %d | Lighting: %s | Time: %.1fms (Avg: %.1fms) | Count: %d", 
                           faceCount, lightingMode, processingTime * 1000, avgProcessingTime * 1000, detectionCount);
    }
}
