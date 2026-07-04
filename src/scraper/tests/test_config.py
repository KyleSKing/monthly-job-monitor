import unittest
from src.scraper import load_config, ScraperConfig


class TestConfig(unittest.TestCase):
    def test_load_config(self):
        cfg = load_config()
        self.assertIsInstance(cfg, ScraperConfig)
        self.assertTrue(hasattr(cfg, "tavily_api_key"))
        self.assertIsInstance(cfg.targets, list)
