import XCTest
@testable import JobMonitorApp

final class JobTests: XCTestCase {
    func testDecodesJobFromJSON() throws {
        let json = """
        {
          "id": "4B6F0A9E-1F9E-4B67-9F30-8F4B0C9C3F42",
          "title": "Software Engineer",
          "company": "Boeing",
          "location": "Seattle, WA",
          "url": "https://example.com/jobs/1",
          "score": 92,
          "summary": "Build internal tools.",
          "source": "LinkedIn",
          "publishedDate": "2026-07-01",
          "salaryRange": "$120k-$150k"
        }
        """.data(using: .utf8)!

        let job = try JSONDecoder().decode(Job.self, from: json)

        XCTAssertEqual(job.id.uuidString, "4B6F0A9E-1F9E-4B67-9F30-8F4B0C9C3F42")
        XCTAssertEqual(job.title, "Software Engineer")
        XCTAssertEqual(job.company, "Boeing")
        XCTAssertEqual(job.location, "Seattle, WA")
        XCTAssertEqual(job.url, "https://example.com/jobs/1")
        XCTAssertEqual(job.score, 92)
        XCTAssertEqual(job.summary, "Build internal tools.")
        XCTAssertEqual(job.source, "LinkedIn")
        XCTAssertEqual(job.publishedDate, "2026-07-01")
        XCTAssertEqual(job.salaryRange, "$120k-$150k")
    }

    func testDecodesBackendJobShape() throws {
        let json = """
        {
          "title": "Senior Security Engineer",
          "company": "Tencent",
          "location": "Beijing",
          "salary": "40-65K",
          "url": "https://careers.tencent.com/job/123",
          "score": 2
        }
        """.data(using: .utf8)!

        let job = try JSONDecoder().decode(Job.self, from: json)

        XCTAssertEqual(job.title, "Senior Security Engineer")
        XCTAssertEqual(job.company, "Tencent")
        XCTAssertEqual(job.location, "Beijing")
        XCTAssertEqual(job.url, "https://careers.tencent.com/job/123")
        XCTAssertEqual(job.score, 2)
        XCTAssertEqual(job.salaryRange, "40-65K")
        XCTAssertEqual(job.summary, "")
        XCTAssertEqual(job.source, "")
        XCTAssertNil(job.publishedDate)
    }
}
