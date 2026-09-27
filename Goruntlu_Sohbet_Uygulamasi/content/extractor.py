# Tuncay Bayır - 20.08.2026
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
import re

import requests
import trafilatura

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
DEFAULT_TIMEOUT_SECONDS = 10
DEFAULT_MIN_SUCCESSFUL = 3
DEFAULT_MIN_WORD_COUNT = 200
DEFAULT_MAX_WORKERS = 5

REFERENCE_PAGE_PATTERN = re.compile(
    r"part of speech|synonyms? for|definitions? for|stand for|"
    r"thesaurus|pronunciation|scrabble|word (?:analysis|finder)|"
    r"how common|syllables",
    re.IGNORECASE,
)
REFERENCE_PATTERN_LIMIT = 1
MAX_WORDS_PER_SENTENCE = 60
DEFAULT_MIN_TOPIC_DENSITY = 0.005
TEXT_WORD_PATTERN = re.compile(r"[a-z']+")
COMMERCIAL_SPAM_PATTERN = re.compile(
    r"add to cart|buy now|shop now|free shipping|limited time offer|"
    r"\d+%\s*off|discount code|subscribe (?:to|now)|newsletter|"
    r"text\w* \w+ to \d+|autodialer|recurring marketing|checkout now|"
    r"flash sale|clearance sale",
    re.IGNORECASE,
)
COMMERCIAL_SPAM_LIMIT = 2
AUTHORITY_DOMAIN_PATTERN = re.compile(r"(?:^|\.)(wikipedia\.org|[\w-]+\.edu|[\w-]+\.gov)$")
AUTHORITY_DENSITY_DISCOUNT = 3


def _build_object_pattern(object_name):
    words = [re.escape(word) for word in object_name.split()]
    return re.compile(r"\b" + r"[\s-]*".join(words) + r"\b", re.IGNORECASE)


def _topic_density(text, object_name, keywords):
    terms = {
        token
        for term in [object_name, *keywords]
        for token in term.lower().split()
    }
    words = TEXT_WORD_PATTERN.findall(text.lower())
    if not words:
        return 0.0

    return sum(1 for word in words if word in terms) / len(words)


def _in_batches(items, size):
    for start in range(0, len(items), size):
        yield items[start:start + size]


def is_authority_domain(url):
    return bool(AUTHORITY_DOMAIN_PATTERN.search(urlparse(url).netloc.lower()))


class ContentExtractor:
    def __init__(
        self,
        user_agent=DEFAULT_USER_AGENT,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
        min_successful=DEFAULT_MIN_SUCCESSFUL,
        min_word_count=DEFAULT_MIN_WORD_COUNT,
        max_workers=DEFAULT_MAX_WORKERS,
        min_topic_density=DEFAULT_MIN_TOPIC_DENSITY,
    ):
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self.min_successful = min_successful
        self.min_word_count = min_word_count
        self.max_workers = max_workers
        self.min_topic_density = min_topic_density

    def extract(self, urls, object_name, keywords=()):
        object_pattern = _build_object_pattern(object_name)
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for batch in _in_batches(urls, self.max_workers):
                extracted = executor.map(
                    lambda url: self._extract_one(url, object_pattern, object_name, keywords), batch
                )
                results.extend(content for content in extracted if content is not None)

                if len(results) >= self.min_successful:
                    break

        return results

    def _extract_one(self, url, object_pattern, object_name, keywords):
        html = self._fetch_html(url)
        if not html:
            return None
        try:
            text = trafilatura.extract(html, url=url)
        except Exception:
            return None

        if not text or len(text.split()) < self.min_word_count:
            return None

        if self._is_reference_page(text):
            return None

        if not object_pattern.search(text):
            return None

        is_authority = is_authority_domain(url)


        if not is_authority and len(COMMERCIAL_SPAM_PATTERN.findall(text)) >= COMMERCIAL_SPAM_LIMIT:
            return None

        required_density = self.min_topic_density
        if is_authority:
            required_density /= AUTHORITY_DENSITY_DISCOUNT
        if self._topic_density(text, object_name, keywords) < required_density:
            return None

        return {"url": url, "text": text}

    @staticmethod
    def _topic_density(text, object_name, keywords):
        return _topic_density(text, object_name, keywords)

    @staticmethod
    def _is_reference_page(text):
        if len(REFERENCE_PAGE_PATTERN.findall(text)) >= REFERENCE_PATTERN_LIMIT:
            return True

        sentence_count = text.count(".") + text.count("!") + text.count("?")
        words_per_sentence = len(text.split()) / max(sentence_count, 1)
        return words_per_sentence > MAX_WORDS_PER_SENTENCE

    def _fetch_html(self, url):
        try:
            response = requests.get(url, headers={"User-Agent": self.user_agent}, timeout=self.timeout_seconds)
            response.raise_for_status()
            return response.text
        except Exception:
            return None
