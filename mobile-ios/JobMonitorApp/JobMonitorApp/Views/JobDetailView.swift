//
//  JobDetailView.swift
//  JobMonitorApp
//
//  Created by Job Monitor on iOS
//

import SwiftUI

struct JobDetailView: View {
    let job: Job
    @Environment(\.openURL) private var openURL
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                // Header
                VStack(alignment: .leading, spacing: 8) {
                    Text(job.title)
                        .font(.title)
                        .bold()
                    
                    Text(job.company)
                        .font(.headline)
                        .foregroundColor(.secondary)
                    
                    Text(job.location)
                        .font(.subheadline)
                        .foregroundColor(.blue)
                }
                
                // Salary
                if let salary = job.salaryRange, !salary.isEmpty {
                    HStack {
                        Image(systemName: "dollarsign.circle.fill")
                            .foregroundColor(.green)
                        Text("💰 " + salary)
                            .font(.headline)
                            .foregroundColor(.green)
                    }
                }
                
                // Score
                HStack {
                    Text("Score: \(job.score)/10")
                        .font(.headline)
                    Spacer()
                    if job.score >= 8 {
                        Text("High Value")
                            .font(.caption)
                            .padding(6)
                            .background(Color.green.opacity(0.2))
                            .cornerRadius(6)
                    }
                }
                
                Divider()
                
                // Description
                if !job.summary.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Job Description")
                            .font(.headline)
                        Text(job.summary)
                            .font(.body)
                            .foregroundColor(.secondary)
                            .multilineTextAlignment(.leading)
                    }
                }
                
                if let date = job.publishedDate {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Published: \(date)")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        Text("Source: \(job.source)")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
                
                Spacer(minLength: 32)
                
                // Apply Button
                Button {
                    if let url = URL(string: job.url) {
                        openURL(url)
                    }
                } label: {
                    HStack {
                        Spacer()
                        Text("Apply Now")
                            .font(.headline)
                            .foregroundColor(.white)
                        Spacer()
                    }
                    .padding()
                    .background(Color.blue)
                    .cornerRadius(10)
                }
            }
            .padding()
        }
        .navigationTitle("Job Detail")
        .navigationBarTitleDisplayMode(.inline)
    }
}

#Preview {
    NavigationView {
        JobDetailView(job: Job.sample)
    }
}