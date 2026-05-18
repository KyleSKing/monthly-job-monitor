#!/usr/bin/env python3
"""
Job Scoring Module
Implements dynamic job ranking through weighted scoring system
"""

import yaml
from typing import List, Dict
from datetime import datetime

class JobScorer:
    """Calculate weighted scores for job listings"""
    
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.weights = self.config.get('scoring', {
            'salary': 0.30,
            'benefits': 0.20,
            'work_env': 0.15,
            'career_growth': 0.25
        })
    
    def score_job(self, job: Dict) -> float:
        """Calculate weighted score for a single job"""
        salary_score = self._score_salary(job.get('salary', 'N/A'))
        benefits_score = self._score_benefits(job.get('benefits', {}))
        work_env_score = self._score_work_env(job.get('work_env', 'office'))
        career_growth_score = self._score_career_growth(job.get('career_growth', 'moderate'))
        
        total_score = (
            salary_score * self.weights['salary'] +
            benefits_score * self.weights['benefits'] +
            work_env_score * self.weights['work_env'] +
            career_growth_score * self.weights['career_growth']
        )
        return round(total_score, 3)
    
    def _score_salary(self, value: str) -> float:
        """Convert salary string to score (0-1)"""
        if not value or 'N/A' in value:
            return 0.3  # Baseline score for unspecified
        
        try:
            # Extract numeric value
            import re
            numeric = re.search(r'\d+', str(value))
            if numeric:
                salary = int(numeric.group())
                # Scoring tiers based on 2023 Chinese tech market data
                if salary >= 8000:
                    return 1.0
                elif salary >= 5000:
                    return 0.8
                elif salary >= 3000:
                    return 0.6
                else:
                    return 0.4
        except:
            pass
        return 0.3
    
    def _score_benefits(self, benefits: Dict) -> float:
        """Score benefits package (0-1)"""
        if not benefits:
            return 0.4  # Baseline
        
        score = 0.0
        # Medical insurance (max 0.4)
        score += min(benefits.get('medical', 0) * 0.2, 0.4)
        # Stock options (max 0.3)
        score += min(benefits.get('stock', 0) * 0.15, 0.3)
        # Retirement (max 0.15)
        score += min(benefits.get('retirement', 0) * 0.15, 0.15)
        # Bonus (max 0.15)
        score += min(benefits.get('bonus', 0) * 0.15, 0.15)
        
        return min(score, 1.0)
    
    def _score_work_env(self, env: str) -> float:
        """Score work environment"""
        env_scores = {
            'remote': 1.0,
            'hybrid': 0.8,
            'flexible': 0.7,
            'office': 0.5
        }
        return env_scores.get(env.lower(), 0.5)
    
    def _score_career_growth(self, growth: str) -> float:
        """Score career growth potential"""
        growth_scores = {
            'excellent': 1.0,
            'strong': 0.8,
            'moderate': 0.6,
            'limited': 0.3
        }
        return growth_scores.get(growth.lower(), 0.6)
    
    def rank_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Rank jobs by score, return sorted list with scores"""
        scored_jobs = []
        for job in jobs:
            job_copy = job.copy()
            job_copy['score'] = self.score_job(job)
            scored_jobs.append(job_copy)
        
        # Sort by score descending
        return sorted(scored_jobs, key=lambda x: x['score'], reverse=True)

# Mock data for demonstration
def generate_mock_jobs():
    return [
        {
            'title': 'Senior Security Engineer',
            'company': 'TechCorp',
            'location': 'Beijing',
            'salary': '25000',
            'benefits': {'medical': 2, 'stock': 2, 'retirement': 1, 'bonus': 1},
            'work_env': 'hybrid',
            'career_growth': 'excellent',
            'url': 'https://example.com/job1'
        },
        {
            'title': 'Compliance Analyst',
            'company': 'FinTech Inc',
            'location': 'Shanghai',
            'salary': '18000',
            'benefits': {'medical': 1, 'stock': 1, 'retirement': 0, 'bonus': 1},
            'work_env': 'office',
            'career_growth': 'moderate',
            'url': 'https://example.com/job2'
        },
        {
            'title': 'Data Governance Specialist',
            'company': 'CloudTech',
            'location': 'Remote',
            'salary': '15000',
            'benefits': {'medical': 1, 'stock': 0, 'retirement': 1, 'bonus': 0},
            'work_env': 'remote',
            'career_growth': 'strong',
            'url': 'https://example.com/job3'
        },
        {
            'title': 'Risk Management Consultant',
            'company': 'Big4 Consulting',
            'location': 'Guangzhou',
            'salary': '22000',
            'benefits': {'medical': 2, 'stock': 1, 'retirement': 2, 'bonus': 2},
            'work_env': 'flexible',
            'career_growth': 'excellent',
            'url': 'https://example.com/job4'
        },
        {
            'title': 'GRC Junior',
            'company': 'StartupXYZ',
            'location': 'Beijing',
            'salary': '12000',
            'benefits': {'medical': 0, 'stock': 1, 'retirement': 0, 'bonus': 0},
            'work_env': 'office',
            'career_growth': 'limited',
            'url': 'https://example.com/job5'
        }
    ]

def main():
    """Demonstrate job scoring and ranking"""
    scorer = JobScorer()
    
    # Use mock data
    jobs = generate_mock_jobs()
    
    print("=" * 60)
    print("Job Scoring & Ranking Demo")
    print("=" * 60)
    print(f"\nWeight Configuration:")
    for k, v in scorer.weights.items():
        print(f"  {k}: {v * 100}%")
    
    print("\n" + "-" * 60)
    print("Ranked Jobs (by weighted score):")
    print("-" * 60)
    
    ranked = scorer.rank_jobs(jobs)
    
    for i, job in enumerate(ranked, 1):
        print(f"\n#{i} Score: {job['score']}")
        print(f"    Title: {job['title']}")
        print(f"    Company: {job['company']}")
        print(f"    Location: {job['location']}")
        print(f"    Salary: {job['salary']}")
        print(f"    Benefits: {job['benefits']}")
        print(f"    Work Env: {job['work_env']}")
        print(f"    Growth: {job['career_growth']}")

if __name__ == '__main__':
    main()