import org.lwjgl.LWJGLException;
import org.lwjgl.input.Keyboard;
import org.lwjgl.input.Mouse;
import org.lwjgl.opengl.Display;
import org.lwjgl.opengl.DisplayMode;

import java.awt.event.MouseEvent;
import java.net.InetSocketAddress;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.atomic.AtomicBoolean;

import static org.lwjgl.opengl.GL11.*;

public class QuaternionVisualizer {

	public static int width, height;

	public static NetworkHandler handler;
	public static WebSocketHandler wsHandler;

	public static HashMap<String, Integer> monitorInd = new HashMap<>();
	public static ArrayList<Monitor> monitorList = new ArrayList<>();

	public static GuiContainer mainGui;
	public static boolean mouseInBounds;
	
	// Enhanced data structures for real-time monitoring
	public static ConcurrentLinkedQueue<DataPoint> dataHistory = new ConcurrentLinkedQueue<>();
	public static AtomicBoolean isConnected = new AtomicBoolean(false);
	public static RobotStatus robotStatus = new RobotStatus();

	public static void newMonitor(String name, Monitor monitor) {
		monitor.name = name;
		monitorInd.put(name, monitorList.size());
		monitorList.add(monitor);
	}

	public static Monitor getMonitor(String name) {
		Integer ind = monitorInd.get(name);
		if(ind != null) {
			return monitorList.get(ind);
		}
		return null;
	}

	public static GuiAngle angle = new GuiAngle();
	
	// Data point class for historical data tracking
	public static class DataPoint {
		public long timestamp;
		public String type;
		public double[] values;
		
		public DataPoint(String type, double[] values) {
			this.timestamp = System.currentTimeMillis();
			this.type = type;
			this.values = values.clone();
		}
	}
	
	// Robot status class for comprehensive monitoring
	public static class RobotStatus {
		public double batteryLevel = 0.0;
		public double temperature = 0.0;
		public boolean spatialAwareness = false;
		public boolean adaptivePID = false;
		public boolean voiceControl = false;
		public String powerMode = "NORMAL";
		public String lightingMode = "UNKNOWN";
		public int faceDetectionCount = 0;
		public double processingTime = 0.0;
	}

	public static void main(String[] args) throws LWJGLException {

		Display.setTitle("Poppy Robot Visualizer 2025");
		Display.setDisplayMode(new DisplayMode(1280, 720));
		Display.create();
		Display.setVSyncEnabled(true);

		glEnable(GL_BLEND);
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

		FontUtil.init();
		Object3D.init();
		GLUtil.init();

		// Enhanced network communication with both TCP and WebSocket
		handler = new NetworkHandler(new InetSocketAddress("localhost", 8080));
		wsHandler = new WebSocketHandler("ws://localhost:9999/socket/");

		// Enhanced monitoring with new capabilities
		newMonitor("dt", new MonitorDt());
		newMonitor("imu", new MonitorIMU());
		newMonitor("ori", new MonitorOrientation());
		newMonitor("out", new MonitorOutput());
		newMonitor("battery", new MonitorBattery());
		newMonitor("spatial", new MonitorSpatial());
		newMonitor("docking", new MonitorDocking());
		newMonitor("face_detection", new MonitorFaceDetection());

		Gui3D gui3D = new Gui3D();
//		GuiTextfield tf = new GuiTextfield("\nasdfasdf\ntest\n\ntest");
//		GuiSlider slider = new GuiSlider();
		angle = new GuiAngle(ang -> handler.sendDouble(5, ang / Math.PI * 180));
//		GuiButton button = new GuiButton("Test", () -> System.out.println("Clicked"));

		GuiContainer guiSettings = new GuiContainer((c) -> {
//			tf.x = tf.y = 10;
//			tf.width = 180;
//			tf.height = FontUtil.fontMetric[FontUtil.font16].height * 7;
//
//			slider.x = 10;
//			slider.y = 200;
//			slider.width = 180;
//			slider.height = 25;
//
//			button.x = 10;
//			button.y = 250;
//			button.width = 180;
//			button.height = 40;

			angle.x = 10;
			angle.y = 100;
			angle.width = 180;
			angle.height = 180;
		});
//		guiSettings.add(tf);
//		guiSettings.add(slider);
//		guiSettings.add(button);
		guiSettings.add(angle);

		mainGui = new GuiContainer((c) -> {
			gui3D.width = c.width - 200;
			gui3D.height = c.height;

			guiSettings.x = c.width - 200;
			guiSettings.width = 200;
			guiSettings.height = height;
		});

		mainGui.add(gui3D);
		mainGui.add(guiSettings);

		Mouse.setClipMouseCoordinatesToWindow(false);
		Mouse.updateCursor();
		Keyboard.enableRepeatEvents(true);

		handler.start();
		wsHandler.start();
		
		// Send initial command to get robot status
		wsHandler.sendMessage("system_status");

		double t = System.nanoTime() / 1e9;

		while(!Display.isCloseRequested()) {

			double nt = System.nanoTime() / 1e9;
			double dt = nt - t;
			t = nt;
			
			// Update connection status
			boolean tcpConnected = handler.socket != null && !handler.socket.isClosed();
			boolean wsConnected = wsHandler != null && wsHandler.isConnected();
			isConnected.set(tcpConnected || wsConnected);

			if(width != Display.getWidth() || height != Display.getHeight()) {
				width = Display.getWidth();
				height = Display.getHeight();
				MouseHelper.height = height;
				mainGui.width = width;
				mainGui.height = height;
				mainGui.resize();
			}

			while(Keyboard.next()) {
				if(!Keyboard.isRepeatEvent()) {
					if (Keyboard.getEventKeyState()) {
						mainGui.keyPress();
					} else {
						mainGui.keyRelease();
					}
				}
				if(Keyboard.getEventKeyState()) {
					mainGui.keyType();
				}
			}

			while(Mouse.next()) {
				int x = MouseHelper.getEventX();
				int y = MouseHelper.getEventY();
				int btn = Mouse.getEventButton();
				int wheel = Mouse.getDWheel();
				if(btn == -1) {
					mainGui.mouseMove(x, y);
				} else {
					if (Mouse.getEventButtonState()) {
						mainGui.mousePress(x, y, btn);
					} else {
						mainGui.mouseRelease(x, y, btn);
						if(!Mouse.isInsideWindow()) {
							mainGui.mouseLeave();
						}
					}
				}
				if(wheel != 0) {
					mainGui.mouseWheel(x, y, wheel);
				}
			}

			boolean isInside = Mouse.isInsideWindow();

			if(mouseInBounds != isInside) {
				if(mouseInBounds) {
					mainGui.mouseLeave();
				}
				mouseInBounds = isInside;
			}

			mainGui.input(dt);

			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

			mainGui.render();

			Display.update();
		}

		// Cleanup connections
		if (wsHandler != null) {
			wsHandler.stopHandler();
		}
		if (handler != null) {
			try {
				handler.socket.close();
			} catch (Exception e) {
				System.err.println("Error closing TCP connection: " + e.getMessage());
			}
		}

		Display.destroy();

		System.exit(0);

	}
}
