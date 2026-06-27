//
//  JobListView.swift
//  JobMonitorApp
//
//  Created by Job Monitor on iOS
//

import SwiftUI

struct JobListView: View {
    @StateObject private var viewModel = JobListViewModel()
    @StateObject private var notificationManager = NotificationManager.shared
    @State private var selectedJob: Job?
    @State private var minScore: Int = 7
    
    var body: some View {
        TabView {
            NavigationView {
                List {
                    ScoreFilterView(minScore: $minScore)
                        .listRowInsets(EdgeInsets())
                        .listRowBackground(Color.clear)
                    
                    if viewModel.isLoading {
                        ProgressView()
                    } else if let error = viewModel.errorMessage {
                        Text("Error: \(error)")
                            .foregroundColor(.red)
                    } else {
                        ForEach(viewModel.filteredJobs(minScore: minScore)) { job in
                            NavigationLink {
                                JobDetailView(job: job)
                            } label: {
                                JobRowView(job: job)
                            }
                        }
                    }
                }
                .navigationTitle("Job Monitor")
                .refreshable {
                    viewModel.fetchJobs()
                }
                .onAppear {
                    if viewModel.jobs.isEmpty {
                        viewModel.fetchJobs()
                    }
                }
            }
            .tabItem {
                Image(systemName: "list.bullet")
                Text("Jobs")
            }
            
            NavigationView {
                SettingsView()
            }
            .tabItem {
                Image(systemName: "gear")
                Text("Settings")
            }
        }
        .environmentObject(notificationManager)
    }
}

struct JobRowView: View {
    let job: Job
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(job.title)
                    .font(.headline)
                Spacer()
                Text("\(job.score)/10")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
            
            Text(job.company)
                .font(.subheadline)
                .foregroundColor(.secondary)
            
            if let salary = job.salaryRange, !salary.isEmpty {
                Text("💰 " + salary)
                    .font(.caption)
                    .foregroundColor(.green)
            }
            
            Text(job.location)
                .font(.caption)
                .foregroundColor(.blue)
        }
        .padding(.vertical, 4)
    }
}

#Preview {
    JobListView()
}