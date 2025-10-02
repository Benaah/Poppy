import java.net.URI;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.SocketChannel;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;

public class WebSocketHandler extends Thread {
    private String wsUrl;
    private AtomicBoolean running = new AtomicBoolean(false);
    private BlockingQueue<String> messageQueue = new LinkedBlockingQueue<>();
    private SocketChannel socketChannel;
    private String host;
    private int port;
    private String path;
    
    public WebSocketHandler(String wsUrl) {
        this.wsUrl = wsUrl;
        parseUrl();
    }
    
    private void parseUrl() {
        try {
            URI uri = new URI(wsUrl);
            this.host = uri.getHost();
            this.port = uri.getPort() == -1 ? 80 : uri.getPort();
            this.path = uri.getPath() + (uri.getQuery() != null ? "?" + uri.getQuery() : "");
        } catch (Exception e) {
            System.err.println("Error parsing WebSocket URL: " + e.getMessage());
            this.host = "localhost";
            this.port = 9999;
            this.path = "/socket/";
        }
    }
    
    public void run() {
        running.set(true);
        
        while (running.get()) {
            try {
                connectWebSocket();
                
                // Process incoming messages
                while (running.get() && socketChannel != null && socketChannel.isConnected()) {
                    ByteBuffer buffer = ByteBuffer.allocate(1024);
                    int bytesRead = socketChannel.read(buffer);
                    
                    if (bytesRead > 0) {
                        buffer.flip();
                        String message = parseWebSocketMessage(buffer);
                        if (message != null && !message.isEmpty()) {
                            processMessage(message);
                        }
                    } else if (bytesRead == -1) {
                        // Connection closed
                        break;
                    }
                    
                    // Small delay to prevent busy waiting
                    Thread.sleep(10);
                }
                
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            } catch (Exception e) {
                System.err.println("WebSocket error: " + e.getMessage());
                try {
                    Thread.sleep(5000); // Wait before retrying
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                    break;
                }
            } finally {
                closeConnection();
            }
        }
    }
    
    private void connectWebSocket() throws IOException {
        socketChannel = SocketChannel.open();
        socketChannel.connect(new InetSocketAddress(host, port));
        
        // Send WebSocket handshake
        String handshake = createHandshake();
        socketChannel.write(ByteBuffer.wrap(handshake.getBytes(StandardCharsets.UTF_8)));
        
        // Read handshake response
        ByteBuffer responseBuffer = ByteBuffer.allocate(1024);
        int bytesRead = socketChannel.read(responseBuffer);
        
        if (bytesRead > 0) {
            responseBuffer.flip();
            String response = StandardCharsets.UTF_8.decode(responseBuffer).toString();
            if (response.contains("101 Switching Protocols")) {
                System.out.println("WebSocket connected successfully");
            } else {
                throw new IOException("WebSocket handshake failed: " + response);
            }
        }
    }
    
    private String createHandshake() {
        String key = generateWebSocketKey();
        return "GET " + path + " HTTP/1.1\r\n" +
               "Host: " + host + ":" + port + "\r\n" +
               "Upgrade: websocket\r\n" +
               "Connection: Upgrade\r\n" +
               "Sec-WebSocket-Key: " + key + "\r\n" +
               "Sec-WebSocket-Version: 13\r\n" +
               "\r\n";
    }
    
    private String generateWebSocketKey() {
        // Simple base64 encoded key (in real implementation, use proper random key)
        return "dGhlIHNhbXBsZSBub25jZQ==";
    }
    
    private void closeConnection() {
        try {
            if (socketChannel != null && socketChannel.isConnected()) {
                socketChannel.close();
            }
        } catch (IOException e) {
            System.err.println("Error closing WebSocket connection: " + e.getMessage());
        }
        socketChannel = null;
    }
    
    private void processMessage(String rawMessage) {
        try {
            // Parse WebSocket frame
            String message = parseWebSocketFrame(rawMessage);
            if (message == null) return;
            
            String[] parts = message.split(" ", 2);
            if (parts.length >= 2) {
                String monitorName = parts[0];
                String data = parts[1];
                
                Monitor monitor = QuaternionVisualizer.getMonitor(monitorName);
                if (monitor != null) {
                    monitor.onData(data);
                }
            }
        } catch (Exception e) {
            System.err.println("Error processing WebSocket message: " + e.getMessage());
        }
    }
    
    private String parseWebSocketMessage(ByteBuffer buffer) {
        try {
            if (buffer.remaining() < 2) return null;
            
            // Read first byte (FIN + opcode)
            byte firstByte = buffer.get();
            boolean fin = (firstByte & 0x80) != 0;
            int opcode = firstByte & 0x0F;
            
            // Read second byte (mask + payload length)
            byte secondByte = buffer.get();
            boolean masked = (secondByte & 0x80) != 0;
            int payloadLength = secondByte & 0x7F;
            
            // Handle extended payload length
            if (payloadLength == 126) {
                if (buffer.remaining() < 2) return null;
                payloadLength = buffer.getShort() & 0xFFFF;
            } else if (payloadLength == 127) {
                if (buffer.remaining() < 8) return null;
                payloadLength = (int) buffer.getLong();
            }
            
            // Read masking key if present
            byte[] mask = null;
            if (masked) {
                if (buffer.remaining() < 4) return null;
                mask = new byte[4];
                buffer.get(mask);
            }
            
            // Read payload
            if (buffer.remaining() < payloadLength) return null;
            byte[] payload = new byte[payloadLength];
            buffer.get(payload);
            
            // Unmask payload if necessary
            if (masked && mask != null) {
                for (int i = 0; i < payload.length; i++) {
                    payload[i] ^= mask[i % 4];
                }
            }
            
            // Handle different opcodes
            switch (opcode) {
                case 0x01: // Text frame
                    return new String(payload, StandardCharsets.UTF_8);
                case 0x08: // Close frame
                    return null; // Connection should be closed
                case 0x09: // Ping frame
                    // Send pong frame
                    sendPongFrame(payload);
                    return null;
                case 0x0A: // Pong frame
                    return null; // Just acknowledge
                default:
                    return null; // Unsupported opcode
            }
            
        } catch (Exception e) {
            System.err.println("Error parsing WebSocket message: " + e.getMessage());
            return null;
        }
    }
    
    private void sendPongFrame(byte[] payload) {
        try {
            ByteBuffer frame = createWebSocketFrame(payload, false);
            frame.put(0, (byte) 0x8A); // Pong frame opcode
            socketChannel.write(frame);
        } catch (IOException e) {
            System.err.println("Error sending pong frame: " + e.getMessage());
        }
    }
    
    private String parseWebSocketFrame(String rawMessage) {
        try {
            // Simple WebSocket frame parsing (for text frames)
            if (rawMessage.length() < 2) return null;
            
            // Check if this is a WebSocket frame or HTTP response
            if (rawMessage.startsWith("HTTP/")) {
                return null; // Skip HTTP responses
            }
            
            // For simplicity, assume the message is already decoded
            // In a full implementation, you would parse the WebSocket frame format
            return rawMessage;
        } catch (Exception e) {
            System.err.println("Error parsing WebSocket frame: " + e.getMessage());
            return null;
        }
    }
    
    public void sendMessage(String message) {
        if (socketChannel != null && socketChannel.isConnected()) {
            try {
                // Create WebSocket frame
                byte[] payload = message.getBytes(StandardCharsets.UTF_8);
                ByteBuffer frame = createWebSocketFrame(payload, true);
                socketChannel.write(frame);
            } catch (IOException e) {
                System.err.println("Error sending WebSocket message: " + e.getMessage());
            }
        } else {
            messageQueue.offer(message);
        }
    }
    
    private ByteBuffer createWebSocketFrame(byte[] payload, boolean isText) {
        int payloadLength = payload.length;
        int frameSize = 2 + (payloadLength < 126 ? 0 : (payloadLength < 65536 ? 2 : 8)) + payloadLength;
        
        ByteBuffer frame = ByteBuffer.allocate(frameSize);
        
        // FIN + opcode (text frame = 0x81)
        frame.put((byte) (0x80 | (isText ? 0x01 : 0x02)));
        
        // Mask + payload length
        if (payloadLength < 126) {
            frame.put((byte) (0x80 | payloadLength));
        } else if (payloadLength < 65536) {
            frame.put((byte) (0x80 | 126));
            frame.putShort((short) payloadLength);
        } else {
            frame.put((byte) (0x80 | 127));
            frame.putLong(payloadLength);
        }
        
        // Masking key (4 bytes)
        byte[] mask = new byte[4];
        for (int i = 0; i < 4; i++) {
            mask[i] = (byte) (Math.random() * 256);
            frame.put(mask[i]);
        }
        
        // Masked payload
        for (int i = 0; i < payloadLength; i++) {
            frame.put((byte) (payload[i] ^ mask[i % 4]));
        }
        
        frame.flip();
        return frame;
    }
    
    public void stopHandler() {
        running.set(false);
        closeConnection();
    }
    
    public boolean isConnected() {
        return socketChannel != null && socketChannel.isConnected();
    }
}
