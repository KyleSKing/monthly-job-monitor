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

    enum CodingKeys: String, CodingKey {
        case id
        case title
        case company
        case location
        case url
        case score
        case summary
        case source
        case publishedDate
        case salaryRange
        case salary
    }

    init(id: UUID = UUID(), title: String, company: String, location: String, url: String, score: Int, summary: String = "", source: String = "", publishedDate: String? = nil, salaryRange: String? = nil) {
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

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decodeIfPresent(UUID.self, forKey: .id) ?? UUID()
        title = try container.decode(String.self, forKey: .title)
        company = try container.decode(String.self, forKey: .company)
        location = try container.decode(String.self, forKey: .location)
        url = try container.decode(String.self, forKey: .url)
        score = try container.decode(Int.self, forKey: .score)
        summary = try container.decodeIfPresent(String.self, forKey: .summary) ?? ""
        source = try container.decodeIfPresent(String.self, forKey: .source) ?? ""
        publishedDate = try container.decodeIfPresent(String.self, forKey: .publishedDate)
        salaryRange = try container.decodeIfPresent(String.self, forKey: .salaryRange) ?? container.decodeIfPresent(String.self, forKey: .salary)
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(id, forKey: .id)
        try container.encode(title, forKey: .title)
        try container.encode(company, forKey: .company)
        try container.encode(location, forKey: .location)
        try container.encode(url, forKey: .url)
        try container.encode(score, forKey: .score)
        try container.encode(summary, forKey: .summary)
        try container.encode(source, forKey: .source)
        try container.encodeIfPresent(publishedDate, forKey: .publishedDate)
        try container.encodeIfPresent(salaryRange, forKey: .salaryRange)
    }
}
