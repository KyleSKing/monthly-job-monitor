//
//  Job.swift
//  JobMonitorApp
//
//  Created by Job Monitor on iOS
//

import Foundation

struct Job: Codable, Identifiable {
    let id: UUID
    let title: String
    let company: String
    let location: String
    let url: String
    let score: Int
    let summary: String
    let source: String
    let publishedDate: String?
    let salaryRange: String?
    
    init(id: UUID = UUID(), title: String, company: String, location: String, url: String, score: Int, summary: String, source: String, publishedDate: String? = nil, salaryRange: String? = nil) {
        self.id = id
        self.title = title
        self.company = company
        self.location = location
        self.url = url
        self.score = score
        self.summary = summary
        self.source = source
        self.publishedDate = publishedDate
        self.salaryRange = salaryRange
    }
}
