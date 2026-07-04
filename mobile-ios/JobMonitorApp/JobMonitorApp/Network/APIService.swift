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
    
    private let baseURL: String
    
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
}

struct JobReport: Codable, Identifiable {
    let id: String
    let date: String
    let totalJobs: Int
    let highScoreJobs: Int
    let jobs: [Job]
    let summary: String
}
