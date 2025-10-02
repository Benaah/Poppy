//
//  SettingsViewController.swift
//  PoppyRobot
//
//  Settings view controller for robot configuration
//

import UIKit

class SettingsViewController: UIViewController {
    
    private let tableView = UITableView(frame: .zero, style: .grouped)
    private let settingsData = SettingsData()
    
    override func viewDidLoad() {
        super.viewDidLoad()
        setupUI()
    }
    
    private func setupUI() {
        title = "Settings"
        view.backgroundColor = .systemBackground
        
        // Add close button
        navigationItem.leftBarButtonItem = UIBarButtonItem(
            barButtonSystemItem: .done,
            target: self,
            action: #selector(closeTapped)
        )
        
        // Setup table view
        tableView.delegate = self
        tableView.dataSource = self
        tableView.register(UITableViewCell.self, forCellReuseIdentifier: "Cell")
        tableView.register(SwitchTableViewCell.self, forCellReuseIdentifier: "SwitchCell")
        tableView.register(TextFieldTableViewCell.self, forCellReuseIdentifier: "TextFieldCell")
        
        view.addSubview(tableView)
        tableView.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            tableView.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
            tableView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            tableView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            tableView.bottomAnchor.constraint(equalTo: view.bottomAnchor)
        ])
    }
    
    @objc private func closeTapped() {
        dismiss(animated: true)
    }
}

// MARK: - UITableViewDataSource
extension SettingsViewController: UITableViewDataSource {
    func numberOfSections(in tableView: UITableView) -> Int {
        return settingsData.sections.count
    }
    
    func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        return settingsData.sections[section].items.count
    }
    
    func tableView(_ tableView: UITableView, titleForHeaderInSection section: Int) -> String? {
        return settingsData.sections[section].title
    }
    
    func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        let item = settingsData.sections[indexPath.section].items[indexPath.row]
        
        switch item.type {
        case .switch:
            let cell = tableView.dequeueReusableCell(withIdentifier: "SwitchCell", for: indexPath) as! SwitchTableViewCell
            cell.configure(with: item)
            return cell
            
        case .textField:
            let cell = tableView.dequeueReusableCell(withIdentifier: "TextFieldCell", for: indexPath) as! TextFieldTableViewCell
            cell.configure(with: item)
            return cell
            
        case .action:
            let cell = tableView.dequeueReusableCell(withIdentifier: "Cell", for: indexPath)
            cell.textLabel?.text = item.title
            cell.accessoryType = .disclosureIndicator
            return cell
        }
    }
}

// MARK: - UITableViewDelegate
extension SettingsViewController: UITableViewDelegate {
    func tableView(_ tableView: UITableView, didSelectRowAt indexPath: IndexPath) {
        tableView.deselectRow(at: indexPath, animated: true)
        
        let item = settingsData.sections[indexPath.section].items[indexPath.row]
        
        switch item.type {
        case .action:
            handleAction(item)
        default:
            break
        }
    }
    
    private func handleAction(_ item: SettingsItem) {
        switch item.identifier {
        case "connection":
            showConnectionSettings()
        case "calibration":
            showCalibrationOptions()
        case "about":
            showAbout()
        default:
            break
        }
    }
    
    private func showConnectionSettings() {
        let alert = UIAlertController(title: "Connection Settings", message: "Configure robot connection", preferredStyle: .alert)
        
        alert.addTextField { textField in
            textField.placeholder = "Robot IP Address"
            textField.text = "192.168.1.100"
        }
        
        alert.addTextField { textField in
            textField.placeholder = "Port"
            textField.text = "9999"
        }
        
        alert.addAction(UIAlertAction(title: "Save", style: .default) { _ in
            // Save connection settings
        })
        
        alert.addAction(UIAlertAction(title: "Cancel", style: .cancel))
        
        present(alert, animated: true)
    }
    
    private func showCalibrationOptions() {
        let alert = UIAlertController(title: "Calibration", message: "Choose calibration option", preferredStyle: .actionSheet)
        
        alert.addAction(UIAlertAction(title: "IMU Calibration", style: .default) { _ in
            // Start IMU calibration
        })
        
        alert.addAction(UIAlertAction(title: "Motor Calibration", style: .default) { _ in
            // Start motor calibration
        })
        
        alert.addAction(UIAlertAction(title: "Cancel", style: .cancel))
        
        present(alert, animated: true)
    }
    
    private func showAbout() {
        let alert = UIAlertController(
            title: "About Poppy Robot",
            message: "Version 1.0\n\nPoppy is an interactive, educational, and intelligent robot that can communicate through physical movements and vocal speeches.",
            preferredStyle: .alert
        )
        
        alert.addAction(UIAlertAction(title: "OK", style: .default))
        
        present(alert, animated: true)
    }
}

// MARK: - Settings Data Model
struct SettingsData {
    let sections: [SettingsSection]
    
    init() {
        sections = [
            SettingsSection(
                title: "Connection",
                items: [
                    SettingsItem(
                        identifier: "connection",
                        title: "Connection Settings",
                        type: .action
                    ),
                    SettingsItem(
                        identifier: "auto_connect",
                        title: "Auto-connect on launch",
                        type: .switch,
                        isOn: true
                    )
                ]
            ),
            SettingsSection(
                title: "Robot Control",
                items: [
                    SettingsItem(
                        identifier: "calibration",
                        title: "Calibration",
                        type: .action
                    ),
                    SettingsItem(
                        identifier: "safety_mode",
                        title: "Safety Mode",
                        type: .switch,
                        isOn: true
                    ),
                    SettingsItem(
                        identifier: "voice_control",
                        title: "Voice Control",
                        type: .switch,
                        isOn: true
                    )
                ]
            ),
            SettingsSection(
                title: "Advanced",
                items: [
                    SettingsItem(
                        identifier: "debug_mode",
                        title: "Debug Mode",
                        type: .switch,
                        isOn: false
                    ),
                    SettingsItem(
                        identifier: "log_level",
                        title: "Log Level",
                        type: .textField,
                        placeholder: "INFO"
                    )
                ]
            ),
            SettingsSection(
                title: "About",
                items: [
                    SettingsItem(
                        identifier: "about",
                        title: "About",
                        type: .action
                    )
                ]
            )
        ]
    }
}

struct SettingsSection {
    let title: String
    let items: [SettingsItem]
}

struct SettingsItem {
    let identifier: String
    let title: String
    let type: SettingsItemType
    let isOn: Bool?
    let placeholder: String?
    
    init(identifier: String, title: String, type: SettingsItemType, isOn: Bool? = nil, placeholder: String? = nil) {
        self.identifier = identifier
        self.title = title
        self.type = type
        self.isOn = isOn
        self.placeholder = placeholder
    }
}

enum SettingsItemType {
    case switch
    case textField
    case action
}

// MARK: - Custom Table View Cells
class SwitchTableViewCell: UITableViewCell {
    private let switchControl = UISwitch()
    
    override init(style: UITableViewCell.CellStyle, reuseIdentifier: String?) {
        super.init(style: .default, reuseIdentifier: reuseIdentifier)
        setupUI()
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
    private func setupUI() {
        accessoryView = switchControl
        selectionStyle = .none
    }
    
    func configure(with item: SettingsItem) {
        textLabel?.text = item.title
        switchControl.isOn = item.isOn ?? false
    }
}

class TextFieldTableViewCell: UITableViewCell {
    private let textField = UITextField()
    
    override init(style: UITableViewCell.CellStyle, reuseIdentifier: String?) {
        super.init(style: .default, reuseIdentifier: reuseIdentifier)
        setupUI()
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
    private func setupUI() {
        textField.placeholder = "Enter value"
        textField.textAlignment = .right
        textField.borderStyle = .none
        contentView.addSubview(textField)
        
        textField.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            textField.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            textField.centerYAnchor.constraint(equalTo: contentView.centerYAnchor),
            textField.leadingAnchor.constraint(equalTo: textLabel!.trailingAnchor, constant: 16)
        ])
    }
    
    func configure(with item: SettingsItem) {
        textLabel?.text = item.title
        textField.placeholder = item.placeholder
    }
}
