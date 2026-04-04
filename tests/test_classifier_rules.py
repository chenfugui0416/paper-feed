import datetime
import unittest

from classifier_rules import classify_entry


class ClassifierRulesTest(unittest.TestCase):
    def test_ai_hot_innovation_overlap_gets_quality_label(self):
        entry = {
            "title": "Autonomous AI agent for materials discovery",
            "summary": "A novel framework for foundation-model-guided discovery.",
            "journal": "Nature Machine Intelligence",
            "pub_date": datetime.datetime(2026, 4, 3),
        }

        result = classify_entry(entry, now=datetime.datetime(2026, 4, 4))

        self.assertTrue(result["in_ai_core"])
        self.assertTrue(result["in_hot_now"])
        self.assertTrue(result["in_innovation_cross"])
        self.assertEqual(result["quality_label"], "S")

    def test_non_ai_entry_is_not_forced_into_all_buckets(self):
        entry = {
            "title": "Electrochemical behavior of lithium salts",
            "summary": "A steady experimental study on transport behavior.",
            "journal": "Solid State Ionics",
            "pub_date": datetime.datetime(2025, 1, 1),
        }

        result = classify_entry(entry, now=datetime.datetime(2026, 4, 4))

        self.assertFalse(result["in_ai_core"])
        self.assertFalse(result["in_hot_now"])
        self.assertFalse(result["in_innovation_cross"])
        self.assertIsNone(result["quality_label"])
