//
//  SettingsView.swift
//  JobMonitorApp
//
//  Created by Job Monitor on iOS
//

import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var notificationManager: NotificationManager
    @Environment(\.openURL) private var openURL
    
    var body: some View {
        Form {
            Section(header: Text("Notifications")) {
                Toggle("Monthly Report Notification", isOn: Binding(
                    get: { notificationManager.isNotificationEnabled },
                    set: { newValue in
                        if newValue {
                            notificationManager.requestAuthorization()
                        } else {
                            notificationManager.cancelNotifications()
                        }
                    }
                ))
                .onChange(of: notificationManager.isNotificationEnabled) { _ in
                    // 状态已更新
                }
                
                Text("Get notified when a new monthly job report is released (1st day of every month).")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Section(header: Text("About")) {
                HStack {
                    Text("Version")
                    Spacer()
                    Text("1.0.0")
                        .foregroundColor(.secondary)
                }
                
                Link(destination: URL(string: "https://github.com/KyleSKing/monthly-job-monitor")!) {
                    HStack {
                        Text("GitHub Repository")
                        Spacer()
                        Image(systemName: "arrow.up.right.square")
                            .foregroundColor(.blue)
                    }
                }
            }
        }
        .navigationTitle("Settings")
    }
}

#Preview {
    NavigationView {
        SettingsView()
            .environmentObject(NotificationManager.shared)
    }
}
