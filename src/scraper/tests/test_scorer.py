import unittest
from src.scraper.scorer import score_job


class TestScorer(unittest.TestCase):
    def test_all_match(self):
        # Security(+2) + Tencent 民营科技巨头(+4) + 北京(+1) = 7
        job = {"title": "Security Engineer", "company": "Tencent", "location": "北京"}
        self.assertEqual(score_job(job), 7)

    def test_partial_match(self):
        # 无标题词 + Tencent(+4) + 上海(0) = 4
        job = {"title": "Software Engineer", "company": "Tencent", "location": "上海"}
        self.assertEqual(score_job(job), 4)

    def test_no_match(self):
        job = {"title": "产品经理", "company": "Facebook", "location": "上海"}
        self.assertEqual(score_job(job), 0)

    def test_company_tiers(self):
        base = {"title": "x", "location": "上海"}
        self.assertEqual(score_job({**base, "company": "Microsoft"}), 4)  # 外企科技
        self.assertEqual(score_job({**base, "company": "Siemens"}), 3)  # 外企传统
        self.assertEqual(score_job({**base, "company": "China Mobile"}), 2)  # 央企
        self.assertEqual(score_job({**base, "company": "Stripe"}), 1)  # 独角兽

    def test_salary_tiers(self):
        base = {"title": "x", "company": "unknown", "location": "上海"}
        self.assertEqual(score_job({**base, "salary": "6万/月"}), 4)  # >=5万
        self.assertEqual(score_job({**base, "salary": "4万"}), 3)  # 3.5-5万
        self.assertEqual(score_job({**base, "salary": "3万"}), 2)  # 2-3.5万
        self.assertEqual(score_job({**base, "salary": "15000元"}), 1)  # 1-2万
        self.assertEqual(score_job({**base, "salary": "8000元"}), 0)  # <1万
        self.assertEqual(score_job({**base, "salary": "N/A"}), 0)  # 无法解析
        self.assertEqual(score_job({**base, "salary": "28万/年"}), 2)  # 年薪→月薪≈2.3万
