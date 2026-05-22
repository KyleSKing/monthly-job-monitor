import unittest
from src.scraper.scorer import score_job, KEYWORDS

class TestScorer(unittest.TestCase):
    def test_all_match(self):
        job = {"title": "Security Engineer", "company": "Tencent", "location": "北京"}
        self.assertEqual(score_job(job), 3)

    def test_partial_match(self):
        job = {"title": "Software Engineer", "company": "Tencent", "location": "上海"}
        self.assertEqual(score_job(job), 1)

    def test_no_match(self):
        job = {"title": "产品经理", "company": "字节跳动", "location": "广州"}
        self.assertEqual(score_job(job), 0)