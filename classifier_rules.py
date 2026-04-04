import datetime
import json
from functools import lru_cache
from pathlib import Path


AI_KEYWORDS = [
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "large language model",
    "language model",
    "llm",
    "foundation model",
    "multimodal",
    "benchmark",
    "agent",
    "agentic",
    "autonomous discovery",
    "scientific agent",
    "materials informatics",
]

AI_JOURNAL_MARKERS = [
    "nature machine intelligence",
    "artificial intelligence chemistry",
    "apl machine learning",
    "digital discovery",
    "ai agent",
]

INNOVATION_KEYWORDS = [
    "novel",
    "first",
    "framework",
    "autonomous",
    "cross-disciplinary",
    "cross disciplinary",
    "discovery",
    "platform",
    "agent for",
    "foundation-model-guided",
]

AI_SCIENCE_PAIRS = [
    ("ai", "materials"),
    ("agent", "materials"),
    ("machine learning", "chemistry"),
    ("machine learning", "materials"),
    ("foundation model", "discovery"),
    ("autonomous", "discovery"),
]

SOURCE_HEAT_MARKERS = [
    "featured",
    "editor's choice",
    "editors' choice",
    "highlight",
    "recommended",
    "most read",
    "most viewed",
    "research highlight",
    "cover",
]


@lru_cache(maxsize=1)
def load_hot_topics():
    path = Path(__file__).with_name("hot_topics.json")
    if not path.exists():
        return {"topic_keywords": [], "source_markers": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _build_text(entry):
    parts = [
        entry.get("title", ""),
        entry.get("summary", ""),
        entry.get("journal", ""),
    ]
    return " ".join(parts).lower()


def _count_hits(text, keywords):
    return sum(1 for keyword in keywords if keyword in text)


def _recentness_score(pub_date, now):
    if not pub_date:
        return 0
    if now is None:
        now = datetime.datetime.now()
    age = now - pub_date
    age_days = age.days
    if age_days <= 7:
        return 4
    if age_days <= 30:
        return 3
    if age_days <= 90:
        return 1
    return 0


def classify_entry(entry, now=None):
    text = _build_text(entry)
    hot_topics = load_hot_topics()

    ai_score = _count_hits(text, AI_KEYWORDS)
    ai_score += _count_hits(text, AI_JOURNAL_MARKERS) * 2

    topic_heat_score = _count_hits(text, hot_topics.get("topic_keywords", []))
    source_heat_score = _count_hits(
        text,
        SOURCE_HEAT_MARKERS + hot_topics.get("source_markers", []),
    )
    recentness_score = _recentness_score(entry.get("pub_date"), now)
    hot_score = topic_heat_score + source_heat_score + recentness_score

    innovation_score = _count_hits(text, INNOVATION_KEYWORDS)
    innovation_score += sum(1 for left, right in AI_SCIENCE_PAIRS if left in text and right in text)

    in_ai_core = ai_score >= 2
    in_hot_now = hot_score >= 3
    in_innovation_cross = innovation_score >= 3

    overlap_bonus = sum([in_ai_core, in_hot_now, in_innovation_cross]) * 2
    quality_score = ai_score + hot_score + innovation_score + overlap_bonus

    quality_label = None
    if quality_score >= 12 and sum([in_ai_core, in_hot_now, in_innovation_cross]) >= 2:
        quality_label = "S"
    elif quality_score >= 7 and any([in_ai_core, in_hot_now, in_innovation_cross]):
        quality_label = "A"

    return {
        "ai_score": ai_score,
        "hot_score": hot_score,
        "innovation_score": innovation_score,
        "quality_score": quality_score,
        "quality_label": quality_label,
        "in_ai_core": in_ai_core,
        "in_hot_now": in_hot_now,
        "in_innovation_cross": in_innovation_cross,
    }
