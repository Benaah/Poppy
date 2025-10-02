import java.io.*;
import java.net.ConnectException;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.net.SocketTimeoutException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;

public class NetworkHandler extends Thread {

	public InetSocketAddress address;

	public NetworkHandler(InetSocketAddress address) {
		this.address = address;
	}
	public Socket socket = new Socket();
	public OutputStream output;

	public void run() {
		while(true) {
			try {
				socket = new Socket();
				socket.setSoTimeout(1000);
				socket.connect(address, 1000);
				output = socket.getOutputStream();
				BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream()));
				while(true) {
					String line = reader.readLine();
					if(line == null) {
						socket.close();
						break;
					}
					try {
						String[] splitted = line.split(" ", 2);
						Monitor m = QuaternionVisualizer.getMonitor(splitted[0]);
						if(m != null) {
							m.onData(splitted[1]);
							
							// Store data point for historical tracking
							if (splitted[1] != null && !splitted[1].isEmpty()) {
								try {
									String[] values = splitted[1].split("\\s+");
									double[] dataValues = new double[values.length];
									for (int i = 0; i < values.length; i++) {
										dataValues[i] = Double.parseDouble(values[i]);
									}
									QuaternionVisualizer.dataHistory.offer(
										new QuaternionVisualizer.DataPoint(splitted[0], dataValues));
									
									// Keep only last 1000 data points
									while (QuaternionVisualizer.dataHistory.size() > 1000) {
										QuaternionVisualizer.dataHistory.poll();
									}
								} catch (NumberFormatException e) {
									// Skip non-numeric data
								}
							}
						}
					} catch(RuntimeException e) {
						e.printStackTrace();
					}

				}
			} catch(ConnectException | SocketTimeoutException e) {
				System.err.println(e);
			} catch(Exception e) {
				e.printStackTrace();
			}
		}
	}

	public void sendPacket(int type, byte[] data) {
		try {
			ByteBuffer buffer = ByteBuffer.allocate(8 + data.length);
			buffer.order(ByteOrder.LITTLE_ENDIAN);
			buffer.putInt(type);
			buffer.putInt(data.length);
			buffer.put(data);
			output.write(buffer.array());
		} catch(Exception e) {
		}
	}

	public void sendDouble(int type, double d) {
		sendPacket(type, ByteBuffer.allocate(8).order(ByteOrder.LITTLE_ENDIAN).putDouble(d).array());
	}

}
