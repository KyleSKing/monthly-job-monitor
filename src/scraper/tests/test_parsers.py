import unittest
from src.scraper.parsers import parse_linkedin, parse_zhaopin, parse_51job, generic_parse

class TestParsers(unittest.TestCase):
    def test_linkedin(self):
        html = """<html><head><title>Test</title></head>
        <div class="topcard__title">Security Engineer</div>
        <div class="topcard__org-name-link">腾讯</div>
        <div class="topcard__flavor--bullet">北京</div>
        <div class="description__text">工作描述</div></html>"""
        job = parse_linkedin(html)
        self.assertEqual(job["title"], "Security Engineer")
        self.assertIn("腾讯", job["company"])
        self.assertIn("北京", job["location"])

    def test_zhaopin(self):
        html = """<html><div class="job-name">安全工程师</div>
        <div class="company_name"><a>阿里巴巴</a></div>
        <div class="job-area">北京/远程</div>
        <div class="detail-content">岗位职责</div></html>"""
        job = parse_zhaopin(html)
        self.assertIn("安全工程师", job["title"])
        self.assertIn("阿里巴巴", job["company"])

    def test_51job(self):
        html = """<html><div class="t1"><span>安全研发</span></div>
        <div class="cname"><a>华为</a></div>
        <div class="lname">北京</div>
        <div id="tmsg">职位描述</div></html>"""
        job = parse_51job(html)
        self.assertIn("安全研发", job["title"])
        self.assertIn("华为", job["company"])

    def test_generic(self):
        html = "<html><head><title>Generic Job</title></head><body>描述内容</body></html>"
        job = generic_parse(html)
        self.assertEqual(job["title"], "Generic Job")
        self.assertIn("描述内容", job["description"])