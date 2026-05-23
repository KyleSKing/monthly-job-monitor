import unittest
from src.scraper.scorer import score_job

class TestScorer(unittest.TestCase):
    def test_all_match(self):
        job = {"title": "Security Engineer", "company": "Tencent", "location": "北京"}
        self.assertEqual(score_job(job), 5)

    def test_partial_match(self):
        job = {"title": "Software Engineer", "company": "Tencent", "location": "上海"}
        self.assertEqual(score_job(job), 2)

    def test_no_match(self):
        job = {"title": "产品经理", "company": "Facebook", "location": "上海"}
        self.assertEqual(score_job(job), 0)