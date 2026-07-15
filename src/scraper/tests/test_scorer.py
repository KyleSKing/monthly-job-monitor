import unittest
from src.scraper.scorer import score_job


class TestScorer(unittest.TestCase):
    def test_all_match(self):
        # Security(+1) + Tencent 民营科技巨头(+4) + 北京(+1) = 6
        job = {"title": "Security Engineer", "company": "Tencent", "location": "北京"}
        self.assertEqual(score_job(job), 6)

    def test_compliance_outranks_security(self):
        # 信息安全合规岗(+3) 应高于纯安全技术岗(+1),同公司同地点
        base = {"company": "Tencent", "location": "北京"}
        compliance = score_job({**base, "title": "信息安全合规经理"})
        security = score_job({**base, "title": "Security Engineer"})
        self.assertGreater(compliance, security)

    def test_exclude_legal_roles(self):
        # 法务/律师岗即使含"合规"字样,标题也不加分(方向护栏)
        base = {"company": "Tencent", "location": "北京"}  # 公司+4 地点+1 = 5
        self.assertEqual(score_job({**base, "title": "合规法务律师"}), 5)
        self.assertEqual(score_job({**base, "title": "Legal Counsel Compliance"}), 5)
        # 审计/财务合规也属非 IT 方向,标题不加分
        self.assertEqual(score_job({**base, "title": "审计合规岗"}), 5)
        self.assertEqual(score_job({**base, "title": "财务合规专员"}), 5)
        # HR/人力资源/招聘/薪酬合规属非 IT 方向,标题不加分
        self.assertEqual(score_job({**base, "title": "HR合规经理"}), 5)
        self.assertEqual(score_job({**base, "title": "人力资源合规"}), 5)
        self.assertEqual(score_job({**base, "title": "招聘合规"}), 5)
        # "hr" 不应误命中含 hr 的信息安全词(如 threat);用含限定词的真岗验证
        self.assertGreater(
            score_job({**base, "title": "网络安全 Threat 合规工程师"}), 5
        )
        # 对照:纯信息安全合规岗标题加分
        self.assertEqual(score_job({**base, "title": "数据合规专员"}), 8)

    def test_partial_match(self):
        # 无标题词 + Tencent(+4) + 上海(0) = 4
        job = {"title": "Software Engineer", "company": "Tencent", "location": "上海"}
        self.assertEqual(score_job(job), 4)

    def test_no_match(self):
        job = {"title": "产品经理", "company": "Facebook", "location": "上海"}
        self.assertEqual(score_job(job), 0)

    def test_industry_compliance_excluded(self):
        # 各行业"X合规"岗不含 IT 信息安全限定词,标题不加分(方向护栏)
        base = {"company": "Tencent", "location": "北京"}  # 公司+4 地点+1 = 5
        for title in [
            "质量合规专员",
            "质量合规工程师",
            "环保合规经理",
            "贸易合规专员",
            "医疗合规专员",
            "银行合规专员",
            "反洗钱合规专员",
            "生产合规专员",
        ]:
            self.assertEqual(score_job({**base, "title": title}), 5, title)

    def test_it_compliance_still_scores(self):
        # 含 IT 信息安全限定词的合规岗仍加分
        base = {"company": "Tencent", "location": "北京"}  # 公司+4 地点+1 = 5
        for title in [
            "信息安全合规工程师",
            "数据合规专员",
            "网络安全合规经理",
            "IT Compliance Officer",
            "隐私合规专员",
        ]:
            self.assertGreater(score_job({**base, "title": title}), 5, title)

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
