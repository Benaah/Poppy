//
//  MainViewController.swift
//  PoppyRobot
//
//  Main view controller for Poppy robot control
//

import UIKit
import SwiftUI

class MainViewController: UIViewController {
    
    private var robotConnection = RobotConnection()
    private var controlPanelView: ControlPanelView?
    
    override func viewDidLoad() {
        super.viewDidLoad()
        setupUI()
        setupConnection()
    }
    
    private func setupUI() {
        view.backgroundColor = .systemBackground
        title = "Poppy Robot Control"
        
        // Add navigation bar items
        navigationItem.rightBarButtonItem = UIBarButtonItem(
            title: "Settings",
            style: .plain,
            target: self,
            action: #selector(settingsTapped)
        )
        
        // Create SwiftUI control panel
        let controlPanel = ControlPanelView(robotConnection: robotConnection)
        let hostingController = UIHostingController(rootView: controlPanel)
        
        addChild(hostingController)
        view.addSubview(hostingController.view)
        hostingController.didMove(toParent: self)
        
        // Set up constraints
        hostingController.view.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            hostingController.view.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
            hostingController.view.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            hostingController.view.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            hostingController.view.bottomAnchor.constraint(equalTo: view.bottomAnchor)
        ])
        
        controlPanelView = controlPanel
    }
    
    private func setupConnection() {
        // Connect to robot
        robotConnection.connect()
    }
    
    @objc private func settingsTapped() {
        let settingsVC = SettingsViewController()
        let navController = UINavigationController(rootViewController: settingsVC)
        present(navController, animated: true)
    }
}

// MARK: - SwiftUI Control Panel
struct ControlPanelView: View {
    @ObservedObject var robotConnection: RobotConnection
    @State private var forwardSpeed: Double = 0.0
    @State private var turnSpeed: Double = 0.0
    @State private var isConnected: Bool = false
    
    var body: some View {
        VStack(spacing: 20) {
            // Connection Status
            ConnectionStatusView(robotConnection: robotConnection)
            
            // Movement Controls
            MovementControlsView(
                forwardSpeed: $forwardSpeed,
                turnSpeed: $turnSpeed,
                isConnected: $isConnected
            )
            
            // Quick Actions
            QuickActionsView(robotConnection: robotConnection)
            
            // Advanced Controls
            AdvancedControlsView(robotConnection: robotConnection)
            
            // Voice Control
            VoiceControlView(robotConnection: robotConnection)
            
            Spacer()
        }
        .padding()
        .onAppear {
            isConnected = robotConnection.isOnline
        }
        .onChange(of: robotConnection.isOnline) { newValue in
            isConnected = newValue
        }
    }
}

// MARK: - Connection Status View
struct ConnectionStatusView: View {
    @ObservedObject var robotConnection: RobotConnection
    
    var body: some View {
        VStack {
            HStack {
                Image(systemName: robotConnection.isOnline ? "wifi" : "wifi.slash")
                    .foregroundColor(robotConnection.isOnline ? .green : .red)
                
                Text(robotConnection.isOnline ? "Connected" : "Disconnected")
                    .font(.headline)
                
                Spacer()
                
                Text("\(robotConnection.batteryLevel)%")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            if case .error(let message) = robotConnection.status {
                Text(message)
                    .font(.caption)
                    .foregroundColor(.red)
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(10)
    }
}

// MARK: - Movement Controls View
struct MovementControlsView: View {
    @Binding var forwardSpeed: Double
    @Binding var turnSpeed: Double
    @Binding var isConnected: Bool
    
    var body: some View {
        VStack(spacing: 15) {
            Text("Movement Controls")
                .font(.headline)
            
            // Forward/Backward Control
            VStack {
                Text("Forward/Backward")
                    .font(.subheadline)
                
                HStack {
                    Button("←") {
                        forwardSpeed = -0.5
                    }
                    .disabled(!isConnected)
                    .buttonStyle(ControlButtonStyle())
                    
                    Slider(value: $forwardSpeed, in: -1.0...1.0)
                        .disabled(!isConnected)
                    
                    Button("→") {
                        forwardSpeed = 0.5
                    }
                    .disabled(!isConnected)
                    .buttonStyle(ControlButtonStyle())
                }
            }
            
            // Turn Control
            VStack {
                Text("Turn Left/Right")
                    .font(.subheadline)
                
                HStack {
                    Button("↶") {
                        turnSpeed = -0.5
                    }
                    .disabled(!isConnected)
                    .buttonStyle(ControlButtonStyle())
                    
                    Slider(value: $turnSpeed, in: -1.0...1.0)
                        .disabled(!isConnected)
                    
                    Button("↷") {
                        turnSpeed = 0.5
                    }
                    .disabled(!isConnected)
                    .buttonStyle(ControlButtonStyle())
                }
            }
            
            // Stop Button
            Button("STOP") {
                forwardSpeed = 0.0
                turnSpeed = 0.0
            }
            .disabled(!isConnected)
            .buttonStyle(StopButtonStyle())
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(10)
    }
}

// MARK: - Quick Actions View
struct QuickActionsView: View {
    @ObservedObject var robotConnection: RobotConnection
    
    var body: some View {
        VStack(spacing: 15) {
            Text("Quick Actions")
                .font(.headline)
            
            LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 2), spacing: 10) {
                QuickActionButton(
                    title: "Find Face",
                    icon: "person.crop.circle",
                    action: { robotConnection.sendCommand("find_face") }
                )
                
                QuickActionButton(
                    title: "Dance",
                    icon: "music.note",
                    action: { robotConnection.sendCommand("dance") }
                )
                
                QuickActionButton(
                    title: "Calibrate",
                    icon: "arrow.clockwise",
                    action: { robotConnection.sendCalibrationCommand() }
                )
                
                QuickActionButton(
                    title: "Status",
                    icon: "info.circle",
                    action: { robotConnection.sendStatusRequest() }
                )
                
                QuickActionButton(
                    title: "Dock",
                    icon: "battery.100",
                    action: { robotConnection.sendDockingCommand() }
                )
                
                QuickActionButton(
                    title: "Emergency Stop",
                    icon: "exclamationmark.triangle.fill",
                    action: { robotConnection.sendEmergencyStop() }
                )
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(10)
    }
}

// MARK: - Advanced Controls View
struct AdvancedControlsView: View {
    @ObservedObject var robotConnection: RobotConnection
    @State private var spatialAwarenessEnabled = true
    @State private var adaptivePIDEnabled = true
    @State private var voiceControlEnabled = true
    
    var body: some View {
        VStack(spacing: 15) {
            Text("Advanced Controls")
                .font(.headline)
            
            // System Toggles
            VStack(spacing: 10) {
                Toggle("Spatial Awareness", isOn: $spatialAwarenessEnabled)
                    .onChange(of: spatialAwarenessEnabled) { newValue in
                        robotConnection.sendSpatialAwarenessToggle(newValue)
                    }
                
                Toggle("Adaptive PID", isOn: $adaptivePIDEnabled)
                    .onChange(of: adaptivePIDEnabled) { newValue in
                        robotConnection.sendAdaptivePIDToggle(newValue)
                    }
                
                Toggle("Voice Control", isOn: $voiceControlEnabled)
                    .onChange(of: voiceControlEnabled) { newValue in
                        robotConnection.sendVoiceControlToggle(newValue)
                    }
            }
            
            // Calibration Buttons
            LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 2), spacing: 10) {
                CalibrationButton(
                    title: "IMU Calibration",
                    action: { robotConnection.sendIMUCalibration() }
                )
                
                CalibrationButton(
                    title: "Spatial Calibration",
                    action: { robotConnection.sendSpatialCalibration() }
                )
                
                CalibrationButton(
                    title: "Docking Calibration",
                    action: { robotConnection.sendDockingCalibration() }
                )
                
                CalibrationButton(
                    title: "Motor Test",
                    action: { robotConnection.sendMotorTest() }
                )
            }
            
            // Battery and System Info
            HStack {
                Button("Battery Status") {
                    robotConnection.sendBatteryStatusRequest()
                }
                .buttonStyle(InfoButtonStyle())
                
                Button("System Status") {
                    robotConnection.sendSystemStatusRequest()
                }
                .buttonStyle(InfoButtonStyle())
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(10)
    }
}

// MARK: - Voice Control View
struct VoiceControlView: View {
    @ObservedObject var robotConnection: RobotConnection
    @State private var isListening = false
    
    var body: some View {
        VStack(spacing: 15) {
            Text("Voice Control")
                .font(.headline)
            
            Button(action: {
                // Toggle voice control
                isListening.toggle()
            }) {
                HStack {
                    Image(systemName: isListening ? "mic.fill" : "mic")
                    Text(isListening ? "Listening..." : "Start Voice Control")
                }
                .foregroundColor(.white)
                .padding()
                .background(isListening ? Color.red : Color.blue)
                .cornerRadius(10)
            }
            .disabled(!robotConnection.isOnline)
            
            if isListening {
                Text("Say commands like 'move forward', 'turn left', 'stop'")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(10)
    }
}

// MARK: - Supporting Views
struct QuickActionButton: View {
    let title: String
    let icon: String
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack {
                Image(systemName: icon)
                    .font(.title2)
                Text(title)
                    .font(.caption)
            }
            .foregroundColor(.primary)
            .padding()
            .background(Color(.systemBackground))
            .cornerRadius(8)
        }
    }
}

struct ControlButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .frame(width: 44, height: 44)
            .background(Color.blue)
            .foregroundColor(.white)
            .cornerRadius(22)
            .scaleEffect(configuration.isPressed ? 0.95 : 1.0)
    }
}

struct StopButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.headline)
            .foregroundColor(.white)
            .padding()
            .background(Color.red)
            .cornerRadius(10)
            .scaleEffect(configuration.isPressed ? 0.95 : 1.0)
    }
}

struct CalibrationButton: View {
    let title: String
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.caption)
                .foregroundColor(.primary)
                .padding()
                .background(Color(.systemBackground))
                .cornerRadius(8)
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(Color.blue, lineWidth: 1)
                )
        }
    }
}

struct InfoButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.subheadline)
            .foregroundColor(.blue)
            .padding(.horizontal, 16)
            .padding(.vertical, 8)
            .background(Color(.systemBackground))
            .cornerRadius(8)
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(Color.blue, lineWidth: 1)
            )
            .scaleEffect(configuration.isPressed ? 0.95 : 1.0)
    }
}
