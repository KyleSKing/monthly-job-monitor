//
//  APIService.swift
//  JobMonitorApp
//
//  Created by Job Monitor on iOS
//

import Foundation
import Alamofire

class APIService {
    static let shared = APIService()
    
    let baseURL: String
    
    private init() {
        #if DEBUG
        // M3 模拟器验收：临时指向线上 Vercel，确保列表有数据（本地无 output/ 报告）
        self.baseURL = "https://monthly-job-monitor.vercel.app/api"
        #else
        // Vercel 自动分配的域名格式: https://monthly-job-monitor-yourusername.vercel.app/api
        self.baseURL = "https://monthly-job-monitor.vercel.app/api"
        #endif
    }
    
    func fetchJobs(completion: @escaping (Result<[Job], Error>) -> Void) {
        let endpoint = "\(baseURL)/jobs"
        
        AF.request(endpoint)
            .validate()
            .responseDecodable(of: [Job].self) { response in
                switch response.result {
                case .success(let jobs):
                    completion(.success(jobs))
                case .failure(let error):
                    completion(.failure(error))
                }
            }
    }
    
    func fetchLatestReport(completion: @escaping (Result<JobReport, Error>) -> Void) {
        let endpoint = "\(baseURL)/latest-report"

        AF.request(endpoint)
            .validate()
            .responseDecodable(of: JobReport.self) { response in
                switch response.result {
                case .success(let report):
                    completion(.success(report))
                case .failure(let error):
                    completion(.failure(error))
                }
            }
    }

    // MARK: - CRUD

    /// Builds a request for CRUD endpoints. Pure and testable: no network call.
    func makeRequest(path: String, method: HTTPMethod, body: Job? = nil) throws -> URLRequest {
        var request = try URLRequest(url: "\(baseURL)\(path)", method: method)
        if let body = body {
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.httpBody = try JSONEncoder().encode(body)
        }
        return request
    }

    func createJob(_ job: Job, completion: @escaping (Result<Job, Error>) -> Void) {
        request(try? makeRequest(path: "/jobs", method: .post, body: job), completion: completion)
    }

    func updateJob(_ job: Job, completion: @escaping (Result<Job, Error>) -> Void) {
        request(try? makeRequest(path: "/jobs/\(job.id.uuidString)", method: .put, body: job), completion: completion)
    }

    func deleteJob(id: UUID, completion: @escaping (Result<Void, Error>) -> Void) {
        guard let urlRequest = try? makeRequest(path: "/jobs/\(id.uuidString)", method: .delete) else {
            completion(.failure(AFError.invalidURL(url: "\(baseURL)/jobs/\(id.uuidString)")))
            return
        }
        AF.request(urlRequest)
            .validate()
            .response { response in
                switch response.result {
                case .success:
                    completion(.success(()))
                case .failure(let error):
                    completion(.failure(error))
                }
            }
    }

    private func request(_ urlRequest: URLRequest?, completion: @escaping (Result<Job, Error>) -> Void) {
        guard let urlRequest = urlRequest else {
            completion(.failure(AFError.invalidURL(url: baseURL)))
            return
        }
        AF.request(urlRequest)
            .validate()
            .responseDecodable(of: Job.self) { response in
                switch response.result {
                case .success(let job):
                    completion(.success(job))
                case .failure(let error):
                    completion(.failure(error))
                }
            }
    }
}

struct JobReport: Codable, Identifiable {
    let id: String
    let date: String
    let totalJobs: Int
    let highScoreJobs: Int
    let jobs: [Job]
    let summary: String
}
