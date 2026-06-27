//
//  PreviewData.swift
//  JobMonitorApp
//
//  Created by Job Monitor on iOS
//

import Foundation

extension Job {
    static let sample = Job(
        title: "Senior Information Security Officer",
        company: "ByteDance",
        location: "Beijing",
        url: "https://job.bytedance.com/job/12345",
        score: 9,
        summary: """
        We are looking for an experienced Information Security Officer to join our team. You will be responsible for:
        
        • Develop and implement security policies and procedures
        • Conduct security assessments and audits
        • Respond to security incidents
        • Manage vendor security assessments
        • Collaborate with engineering teams to build secure products
        
        Requirements:
        • 5+ years of experience in information security
        • Deep understanding of network security and application security
        • Experience with compliance requirements (GDPR, ISO 27001, etc.)
        • Excellent communication and problem-solving skills
        """,
        source: "bytedance",
        publishedDate: "2026-06-01",
        salaryRange: "¥400K - 600K/year"
    )
    
    static let sampleList: [Job] = [
        sample,
        Job(
            title: "Compliance Director",
            company: "Tencent",
            location: "Shenzhen",
            url: "https://careers.tencent.com/job/67890",
            score: 8,
            summary: "Lead the compliance team to ensure all business operations comply with regulatory requirements.",
            source: "tencent",
            publishedDate: "2026-06-02",
            salaryRange: "¥350K - 500K/year"
        )
    ]
}