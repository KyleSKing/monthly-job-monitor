//
//  NotificationManager.swift
//  JobMonitorApp
//
//  Created by Job Monitor on iOS
//

import Foundation
import UserNotifications

class NotificationManager: ObservableObject {
    static let shared = NotificationManager()
    
    @Published var isNotificationEnabled: Bool = false
    
    private init() {
        checkAuthorizationStatus()
    }
    
    func checkAuthorizationStatus() {
        UNUserNotificationCenter.current().getNotificationSettings { settings in
            DispatchQueue.main.async {
                self.isNotificationEnabled = settings.authorizationStatus == .authorized
            }
        }
    }
    
    func requestAuthorization() {
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge]) { granted, error in
            DispatchQueue.main.async {
                self.isNotificationEnabled = granted
                if granted {
                    self.scheduleMonthlyReportNotification()
                }
            }
        }
    }
    
    func scheduleMonthlyReportNotification() {
        // 每月1日下午4点（北京时间）推送新报告通知
        let content = UNMutableNotificationContent()
        content.title = "New Job Report Available"
        content.body = "Check out the latest security & compliance job positions"
        content.sound = .default
        
        var dateComponents = DateComponents()
        dateComponents.day = 1
        dateComponents.hour = 16 // UTC+8 16:00 = 08:00 UTC
        dateComponents.minute = 0
        
        let trigger = UNCalendarNotificationTrigger(dateMatching: dateComponents, repeats: true)
        let request = UNNotificationRequest(identifier: "monthly-job-report", content: content, trigger: trigger)
        
        UNUserNotificationCenter.current().add(request)
    }
    
    func cancelNotifications() {
        UNUserNotificationCenter.current().removeAllPendingNotificationRequests()
        isNotificationEnabled = false
    }
}
