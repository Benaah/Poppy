//
//  RobotConnection.swift
//  PoppyRobot
//
//  Model for managing robot connection and communication
//

import Foundation
import Network

enum ConnectionType {
    case bluetooth
    case wifi
    case usb
}

enum ConnectionStatus {
    case disconnected
    case connecting
    case connected
    case error(String)
}

class RobotConnection: ObservableObject {
    @Published var status: ConnectionStatus = .disconnected
    @Published var connectionType: ConnectionType = .wifi
    @Published var robotName: String = "Poppy"
    @Published var batteryLevel: Int = 100
    @Published var isOnline: Bool = false
    
    private var tcpConnection: NWConnection?
    private let serverHost = "192.168.1.100" // Default robot IP
    private let serverPort: UInt16 = 9999
    
    init() {
        setupNetworkMonitoring()
    }
    
    deinit {
        disconnect()
    }
    
    // MARK: - Connection Management
    
    func connect(type: ConnectionType = .wifi) {
        connectionType = type
        status = .connecting
        
        switch type {
        case .wifi:
            connectViaWiFi()
        case .bluetooth:
            connectViaBluetooth()
        case .usb:
            connectViaUSB()
        }
    }
    
    func disconnect() {
        tcpConnection?.cancel()
        tcpConnection = nil
        status = .disconnected
        isOnline = false
    }
    
    private func connectViaWiFi() {
        let host = NWEndpoint.Host(serverHost)
        let port = NWEndpoint.Port(integerLiteral: serverPort)
        
        tcpConnection = NWConnection(host: host, port: port, using: .tcp)
        
        tcpConnection?.stateUpdateHandler = { [weak self] state in
            DispatchQueue.main.async {
                switch state {
                case .ready:
                    self?.status = .connected
                    self?.isOnline = true
                    print("✅ Connected to Poppy via WiFi")
                case .failed(let error):
                    self?.status = .error("Connection failed: \(error.localizedDescription)")
                    self?.isOnline = false
                    print("❌ WiFi connection failed: \(error)")
                case .cancelled:
                    self?.status = .disconnected
                    self?.isOnline = false
                    print("🔌 WiFi connection cancelled")
                default:
                    break
                }
            }
        }
        
        tcpConnection?.start(queue: .global(qos: .userInitiated))
    }
    
    private func connectViaBluetooth() {
        // Bluetooth connection implementation would go here
        status = .error("Bluetooth connection not implemented yet")
    }
    
    private func connectViaUSB() {
        // USB connection implementation would go here
        status = .error("USB connection not implemented yet")
    }
    
    // MARK: - Communication
    
    func sendCommand(_ command: String) {
        guard isOnline, let connection = tcpConnection else {
            print("❌ Cannot send command - not connected")
            return
        }
        
        let data = command.data(using: .utf8)!
        connection.send(content: data, completion: .contentProcessed { error in
            if let error = error {
                print("❌ Failed to send command: \(error)")
            } else {
                print("📤 Sent command: \(command)")
            }
        })
    }
    
    // MARK: - Enhanced Robot Commands
    
    func sendDockingCommand() {
        sendCommand("docking_start")
    }
    
    func sendUndockingCommand() {
        sendCommand("docking_stop")
    }
    
    func sendCalibrationCommand() {
        sendCommand("calibrate")
    }
    
    func sendEmergencyStop() {
        sendCommand("emergency_stop")
    }
    
    func sendSpatialAwarenessToggle(_ enabled: Bool) {
        sendCommand("spatial_awareness_\(enabled ? "on" : "off")")
    }
    
    func sendAdaptivePIDToggle(_ enabled: Bool) {
        sendCommand("adaptive_pid_\(enabled ? "on" : "off")")
    }
    
    func sendVoiceControlToggle(_ enabled: Bool) {
        sendCommand("voice_control_\(enabled ? "on" : "off")")
    }
    
    func sendBatteryStatusRequest() {
        sendCommand("battery_status")
    }
    
    func sendSystemStatusRequest() {
        sendCommand("system_status")
    }
    
    func sendSensorCalibration() {
        sendCommand("sensor_calibrate")
    }
    
    func sendMotorTest() {
        sendCommand("motor_test")
    }
    
    func sendIMUCalibration() {
        sendCommand("imu_calibrate")
    }
    
    func sendSpatialCalibration() {
        sendCommand("spatial_calibrate")
    }
    
    func sendDockingCalibration() {
        sendCommand("docking_calibrate")
    }
    
    func sendCustomCommand(_ command: String, parameters: [String: Any] = [:]) {
        var fullCommand = command
        if !parameters.isEmpty {
            let paramString = parameters.map { "\($0.key)=\($0.value)" }.joined(separator: ",")
            fullCommand += ",\(paramString)"
        }
        sendCommand(fullCommand)
    }
    
    func sendMovementCommand(forward: Double, turn: Double) {
        let command = "move,\(forward),\(turn)"
        sendCommand(command)
    }
    
    func sendTurnCommand(angle: Double) {
        let command = "turn,\(angle)"
        sendCommand(command)
    }
    
    func sendStopCommand() {
        sendCommand("stop")
    }
    
    func sendCalibrationCommand() {
        sendCommand("calibrate")
    }
    
    func sendStatusRequest() {
        sendCommand("status")
    }
    
    // MARK: - Network Monitoring
    
    private func setupNetworkMonitoring() {
        let monitor = NWPathMonitor()
        monitor.pathUpdateHandler = { [weak self] path in
            DispatchQueue.main.async {
                if path.status == .satisfied {
                    print("🌐 Network connection available")
                } else {
                    print("❌ No network connection")
                    if self?.isOnline == true {
                        self?.status = .error("Network connection lost")
                        self?.isOnline = false
                    }
                }
            }
        }
        
        let queue = DispatchQueue(label: "NetworkMonitor")
        monitor.start(queue: queue)
    }
}
