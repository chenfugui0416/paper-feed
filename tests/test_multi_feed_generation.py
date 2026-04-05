import datetime
import tempfile
import time
import unittest
from pathlib import Path

import get_RSS


class MultiFeedGenerationTest(unittest.TestCase):
    def setUp(self):
        self.entry = {
            "title": "Autonomous AI agent for materials discovery",
            "summary": "A novel framework for foundation-model-guided discovery.",
            "journal": "Nature Machine Intelligence",
            "id": "paper-1",
            "link": "https://example.com/paper-1",
            "pub_date": datetime.datetime(2026, 4, 3),
        }

    def test_entry_can_be_written_to_multiple_feeds(self):
        buckets = get_RSS.bucket_entries([self.entry], now=datetime.datetime(2026, 4, 4))

        self.assertEqual(len(buckets["ai_core"]), 1)
        self.assertEqual(len(buckets["hot_now"]), 1)
        self.assertEqual(len(buckets["innovation_cross"]), 1)
        self.assertEqual(buckets["ai_core"][0]["quality_label"], "S")

    def test_format_display_title_adds_quality_prefix(self):
        self.assertEqual(get_RSS.format_display_title("Demo", "S"), "【精选S】Demo")
        self.assertEqual(get_RSS.format_display_title("Demo", None), "Demo")

    def test_feed_titles_are_chinese_and_legacy_feed_remains(self):
        self.assertEqual(get_RSS.FEED_DEFINITIONS["ai_core"]["title"], "AI核心")
        self.assertEqual(get_RSS.FEED_DEFINITIONS["hot_now"]["title"], "热点追踪")
        self.assertEqual(get_RSS.FEED_DEFINITIONS["innovation_cross"]["title"], "创新交叉")
        self.assertEqual(get_RSS.LEGACY_OUTPUT_FILE, Path("filtered_feed.xml"))

    def test_generate_rss_xml_writes_feed_title_and_highlight(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "ai_core.xml"
            items = [{**self.entry, "quality_label": "S"}]
            get_RSS.generate_rss_xml(
                items,
                output_path,
                "AI核心",
                "AI相关论文订阅",
                include_quality_label=True,
                guid_prefix="ai_core",
            )
            content = output_path.read_text(encoding="utf-8")

        self.assertIn("<title>AI核心</title>", content)
        self.assertIn("【精选S】", content)
        self.assertIn("<guid isPermaLink=\"false\">ai_core:paper-1</guid>", content)

    def test_category_feeds_use_distinct_guids_for_zotero(self):
        legacy_guid = get_RSS.build_guid(self.entry)
        category_guid = get_RSS.build_guid(self.entry, guid_prefix="hot_now")

        self.assertNotEqual(legacy_guid.guid, category_guid.guid)
        self.assertEqual(category_guid.guid, "hot_now:paper-1")
        self.assertFalse(category_guid.isPermaLink)

    def test_convert_struct_time_handles_pre_epoch_dates(self):
        struct_time = time.struct_time((1774, 3, 1, 0, 0, 0, 1, 60, 0))
        converted = get_RSS.convert_struct_time_to_datetime(struct_time)

        self.assertEqual(converted, datetime.datetime(1774, 3, 1, 0, 0, 0))
