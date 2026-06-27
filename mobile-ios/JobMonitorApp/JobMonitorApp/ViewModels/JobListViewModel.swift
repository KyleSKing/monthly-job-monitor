//
//  JobListViewModel.swift
//  JobMonitorApp
//
//  Created by Job Monitor on iOS
//

import Foundation
import Combine

class JobListViewModel: ObservableObject {
    @Published var jobs: [Job] = []
    @Published var isLoading: Bool = false
    @Published var errorMessage: String?
    @Published var latestReport: JobReport?
    
    private var cancellables = Set<AnyCancellable>()
    
    func fetchJobs() {
        isLoading = true
        errorMessage = nil
        
        APIService.shared.fetchLatestReport { [weak self] result in
            guard let self = self else { return }
            
            DispatchQueue.main.async {
                self.isLoading = false
                
                switch result {
                case .success(let report):
                    self.latestReport = report
                    self.jobs = report.jobs
                case .failure(let error):
                    self.errorMessage = error.localizedDescription
                    // 加载预览数据
                    self.jobs = [Job.sample]
                }
            }
        }
    }
    
    func filteredJobs(minScore: Int) -> [Job] {
        return jobs.filter { $0.score >= minScore }
    }
}
