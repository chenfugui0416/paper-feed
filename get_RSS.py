import datetime
import os
import re
from pathlib import Path

import feedparser
from rfeed import Feed, Guid, Item, Serializable

from classifier_rules import classify_entry
from journal_map import clean_title, get_abbr


class DcSource(Serializable):
    """
    rfeed extension that writes <dc:source>value</dc:source> into an RSS item.
    Zotero reads this as the publicationTitle field.
    """

    def __init__(self, source):
        Serializable.__init__(self)
        self.source = source

    def publish(self, handler):
        Serializable.publish(self, handler)
        self._write_element("dc:source", self.source)


LEGACY_OUTPUT_FILE = Path("filtered_feed.xml")
OUTPUT_DIR = Path("feeds")
MAX_ITEMS = 1000
LEGACY_FEED_TITLE = "论文总订阅"
FEED_DEFINITIONS = {
    "ai_core": {
        "title": "AI核心",
        "description": "AI相关论文订阅",
        "path": OUTPUT_DIR / "ai_core.xml",
    },
    "hot_now": {
        "title": "热点追踪",
        "description": "近期热点论文订阅",
        "path": OUTPUT_DIR / "hot_now.xml",
    },
    "innovation_cross": {
        "title": "创新交叉",
        "description": "跨学科创新论文订阅",
        "path": OUTPUT_DIR / "innovation_cross.xml",
    },
}


def get_repo_url():
    """Infer the public repository URL for the generated feed metadata."""
    if os.environ.get("RSS_REPO_URL"):
        return os.environ["RSS_REPO_URL"]

    repo = os.environ.get("GITHUB_REPOSITORY")
    if repo:
        server = os.environ.get("GITHUB_SERVER_URL", "https://github.com").rstrip("/")
        return f"{server}/{repo}"

    return "https://github.com/your_username/your_repo"


def load_config(filename, env_var_name=None):
    """Load line-based configuration from an env var or local file."""
    if env_var_name and os.environ.get(env_var_name):
        print(f"Loading config from environment variable: {env_var_name}")
        content = os.environ[env_var_name]
        if "\n" in content:
            return [line.strip() for line in content.split("\n") if line.strip()]
        return [line.strip() for line in content.split(";") if line.strip()]

    if os.path.exists(filename):
        print(f"Loading config from local file: {filename}")
        with open(filename, "r", encoding="utf-8") as handle:
            return [
                line.strip()
                for line in handle
                if line.strip() and not line.startswith("#")
            ]

    return []


def remove_illegal_xml_chars(text):
    """Remove XML 1.0 unsupported ASCII control characters."""
    if not text:
        return ""
    illegal_chars = r"[\x00-\x08\x0b\x0c\x0e-\x1f]"
    return re.sub(illegal_chars, "", text)


def convert_struct_time_to_datetime(struct_time):
    if not struct_time:
        return datetime.datetime.now()
    try:
        return datetime.datetime(
            struct_time.tm_year,
            struct_time.tm_mon,
            struct_time.tm_mday,
            struct_time.tm_hour,
            struct_time.tm_min,
            struct_time.tm_sec,
        )
    except (AttributeError, OverflowError, ValueError):
        return datetime.datetime.now()


def parse_rss(rss_url, retries=3):
    print(f"Fetching: {rss_url}...")
    for _ in range(retries):
        try:
            feed = feedparser.parse(rss_url)
            entries = []
            journal_title = feed.feed.get("title", "Unknown Journal")

            for entry in feed.entries:
                pub_struct = entry.get("published_parsed", entry.get("updated_parsed"))
                pub_date = convert_struct_time_to_datetime(pub_struct)
                entries.append(
                    {
                        "title": entry.get("title", ""),
                        "link": entry.get("link", ""),
                        "pub_date": pub_date,
                        "summary": entry.get("summary", entry.get("description", "")),
                        "journal": journal_title,
                        "id": entry.get("id", entry.get("link", "")),
                    }
                )
            return entries
        except Exception as exc:
            print(f"Error parsing {rss_url}: {exc}")
            time.sleep(2)
    return []


def get_existing_items():
    """Load accumulated items from the legacy aggregate feed."""
    if not LEGACY_OUTPUT_FILE.exists():
        return []

    print(f"Loading existing items from {LEGACY_OUTPUT_FILE}...")
    try:
        feed = feedparser.parse(str(LEGACY_OUTPUT_FILE))
        if getattr(feed, "bozo", 0) == 1:
            print("Warning: Existing XML file might be corrupted. Ignoring old items.")

        entries = []
        for entry in feed.entries:
            pub_struct = entry.get("published_parsed")
            pub_date = convert_struct_time_to_datetime(pub_struct)
            entries.append(
                {
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "pub_date": pub_date,
                    "summary": entry.get("summary", ""),
                    "journal": entry.get("dc_source", "") or entry.get("author", ""),
                    "id": entry.get("id", entry.get("link", "")),
                    "is_old": True,
                }
            )
        return entries
    except Exception as exc:
        print(f"Error reading existing file: {exc}")
        return []


def match_entry(entry, queries):
    text_to_search = (entry["title"] + " " + entry["summary"]).lower()
    for query in queries:
        keywords = [keyword.strip().lower() for keyword in query.split("AND")]
        if all(keyword in text_to_search for keyword in keywords):
            return True
    return False


def format_display_title(title, quality_label):
    if not quality_label:
        return title
    if title.startswith("【精选"):
        return title
    return f"【精选{quality_label}】{title}"


def normalize_item_title(item, include_quality_label=False):
    raw_journal = item["journal"]
    item_title = clean_title(item["title"], raw_journal)
    if include_quality_label:
        item_title = format_display_title(item_title, item.get("quality_label"))
    return remove_illegal_xml_chars(item_title)


def normalize_item_source(item):
    return remove_illegal_xml_chars(get_abbr(item["journal"]))


def build_rss_items(items, include_quality_label=False):
    rss_items = []
    sorted_items = sorted(items, key=lambda item: item["pub_date"], reverse=True)[:MAX_ITEMS]

    for item in sorted_items:
        rss_items.append(
            Item(
                title=normalize_item_title(item, include_quality_label=include_quality_label),
                link=item["link"],
                description=remove_illegal_xml_chars(item["summary"]),
                guid=Guid(item["id"]),
                pubDate=item["pub_date"],
                extensions=[DcSource(normalize_item_source(item))],
            )
        )
    return rss_items


def generate_rss_xml(
    items,
    output_path,
    feed_title,
    description,
    include_quality_label=False,
):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    feed = Feed(
        title=feed_title,
        link=get_repo_url(),
        description=description,
        language="zh-CN",
        lastBuildDate=datetime.datetime.now(),
        items=build_rss_items(items, include_quality_label=include_quality_label),
    )

    output_path.write_text(feed.rss(), encoding="utf-8")
    print(f"Successfully generated {output_path} with {min(len(items), MAX_ITEMS)} items.")


def bucket_entries(entries, now=None):
    buckets = {name: [] for name in FEED_DEFINITIONS}
    for entry in entries:
        classification = classify_entry(entry, now=now)
        enriched_entry = {
            **entry,
            "quality_label": classification["quality_label"],
            "quality_score": classification["quality_score"],
            "ai_score": classification["ai_score"],
            "hot_score": classification["hot_score"],
            "innovation_score": classification["innovation_score"],
        }
        if classification["in_ai_core"]:
            buckets["ai_core"].append(enriched_entry.copy())
        if classification["in_hot_now"]:
            buckets["hot_now"].append(enriched_entry.copy())
        if classification["in_innovation_cross"]:
            buckets["innovation_cross"].append(enriched_entry.copy())
    return buckets


def write_all_feeds(all_entries, now=None):
    generate_rss_xml(
        all_entries,
        LEGACY_OUTPUT_FILE,
        LEGACY_FEED_TITLE,
        "全部命中论文订阅",
        include_quality_label=False,
    )

    buckets = bucket_entries(all_entries, now=now)
    for key, definition in FEED_DEFINITIONS.items():
        generate_rss_xml(
            buckets[key],
            definition["path"],
            definition["title"],
            definition["description"],
            include_quality_label=True,
        )


def main():
    rss_urls = load_config("journals.dat", "RSS_JOURNALS")
    queries = load_config("keywords.dat", "RSS_KEYWORDS")

    if not rss_urls or not queries:
        print("Error: Configuration files are empty or missing.")
        return

    existing_entries = get_existing_items()
    seen_ids = {entry["id"] for entry in existing_entries}
    all_entries = existing_entries.copy()
    new_count = 0

    print("Starting RSS fetch from remote...")
    for url in rss_urls:
        fetched_entries = parse_rss(url)
        for entry in fetched_entries:
            if entry["id"] in seen_ids:
                continue
            if not match_entry(entry, queries):
                continue

            all_entries.append(entry)
            seen_ids.add(entry["id"])
            new_count += 1
            print(f"Match found: {entry['title'][:50]}...")

    print(f"Added {new_count} new entries.")
    write_all_feeds(all_entries)


if __name__ == "__main__":
    main()
