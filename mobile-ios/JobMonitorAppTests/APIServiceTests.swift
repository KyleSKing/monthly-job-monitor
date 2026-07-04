import XCTest
import Alamofire
@testable import JobMonitorApp

final class APIServiceTests: XCTestCase {
    private let service = APIService.shared

    private func sampleJob() -> Job {
        Job(
            id: UUID(uuidString: "4B6F0A9E-1F9E-4B67-9F30-8F4B0C9C3F42")!,
            title: "Senior Security Engineer",
            company: "Tencent",
            location: "Beijing",
            url: "https://careers.tencent.com/job/123",
            score: 2,
            salaryRange: "40-65K"
        )
    }

    // iOS test 2: Job encodes write payloads with salaryRange
    func testEncodeUsesSalaryRange() throws {
        let data = try JSONEncoder().encode(sampleJob())
        let object = try JSONSerialization.jsonObject(with: data) as! [String: Any]
        XCTAssertEqual(object["salaryRange"] as? String, "40-65K")
        XCTAssertNil(object["salary"])
    }

    // iOS test 3: create uses POST /jobs with a body
    func testCreateRequestUsesPost() throws {
        let request = try service.makeRequest(path: "/jobs", method: .post, body: sampleJob())
        XCTAssertEqual(request.httpMethod, "POST")
        XCTAssertEqual(request.url?.absoluteString, "\(service.baseURL)/jobs")
        XCTAssertNotNil(request.httpBody)
    }

    // iOS test 3: update uses PUT /jobs/{id} with a body
    func testUpdateRequestUsesPutWithId() throws {
        let job = sampleJob()
        let request = try service.makeRequest(path: "/jobs/\(job.id.uuidString)", method: .put, body: job)
        XCTAssertEqual(request.httpMethod, "PUT")
        XCTAssertEqual(request.url?.absoluteString, "\(service.baseURL)/jobs/\(job.id.uuidString)")
        XCTAssertNotNil(request.httpBody)
    }

    // iOS test 3: delete uses DELETE /jobs/{id} with no body
    func testDeleteRequestUsesDeleteWithId() throws {
        let job = sampleJob()
        let request = try service.makeRequest(path: "/jobs/\(job.id.uuidString)", method: .delete)
        XCTAssertEqual(request.httpMethod, "DELETE")
        XCTAssertEqual(request.url?.absoluteString, "\(service.baseURL)/jobs/\(job.id.uuidString)")
        XCTAssertNil(request.httpBody)
    }
}
