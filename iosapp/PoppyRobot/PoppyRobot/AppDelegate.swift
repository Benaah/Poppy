//
//  AppDelegate.swift
//  PoppyRobot
//
//  iOS Companion App for Poppy Robot Control
//

import UIKit
import CoreBluetooth

@main
class AppDelegate: UIResponder, UIApplicationDelegate {
    
    var window: UIWindow?
    var bluetoothManager: CBCentralManager?
    
    func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        
        // Initialize Bluetooth manager
        bluetoothManager = CBCentralManager(delegate: self, queue: nil)
        
        // Set up main window
        window = UIWindow(frame: UIScreen.main.bounds)
        let mainViewController = MainViewController()
        let navigationController = UINavigationController(rootViewController: mainViewController)
        window?.rootViewController = navigationController
        window?.makeKeyAndVisible()
        
        return true
    }
    
    func applicationWillResignActive(_ application: UIApplication) {
        // Sent when the application is about to move from active to inactive state
    }
    
    func applicationDidEnterBackground(_ application: UIApplication) {
        // Use this method to release shared resources, save user data, invalidate timers
    }
    
    func applicationWillEnterForeground(_ application: UIApplication) {
        // Called as part of the transition from the background to the active state
    }
    
    func applicationDidBecomeActive(_ application: UIApplication) {
        // Restart any tasks that were paused (or not yet started) while the application was inactive
    }
    
    func applicationWillTerminate(_ application: UIApplication) {
        // Called when the application is about to terminate
    }
}

// MARK: - CBCentralManagerDelegate
extension AppDelegate: CBCentralManagerDelegate {
    func centralManagerDidUpdateState(_ central: CBCentralManager) {
        switch central.state {
        case .poweredOn:
            print("✅ Bluetooth is powered on")
        case .poweredOff:
            print("❌ Bluetooth is powered off")
        case .resetting:
            print("🔄 Bluetooth is resetting")
        case .unauthorized:
            print("❌ Bluetooth is unauthorized")
        case .unsupported:
            print("❌ Bluetooth is unsupported")
        case .unknown:
            print("❓ Bluetooth state is unknown")
        @unknown default:
            print("❓ Unknown Bluetooth state")
        }
    }
}
