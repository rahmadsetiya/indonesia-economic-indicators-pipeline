import unittest
from pathlib import Path

from indonesia_economic_indicators.common.config import load_sources, source_by_id


ROOT = Path(__file__).resolve().parents[1]


class ConfigTests(unittest.TestCase):
    def test_registry_and_unique_source(self):
        registry = load_sources(ROOT / "config" / "sources.yaml")
        source = source_by_id(registry, "demo_bi_inflation")
        self.assertEqual(source["status"], "VALIDATED")
        self.assertTrue(source["enabled"])


if __name__ == "__main__":
    unittest.main()
