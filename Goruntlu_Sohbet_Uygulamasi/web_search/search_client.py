# Tuncay Bayır - 20.08.2026
import time

from ddgs import DDGS

DEFAULT_MIN_RESULTS = 5
DEFAULT_DELAY_SECONDS = 1.5
DEFAULT_MAX_ATTEMPTS = 5


class WebSearchClient:
    def __init__(
        self,
        min_results=DEFAULT_MIN_RESULTS,
        delay_seconds=DEFAULT_DELAY_SECONDS,
        max_attempts=DEFAULT_MAX_ATTEMPTS,
    ):
        self.min_results = min_results
        self.delay_seconds = delay_seconds
        self.max_attempts = max_attempts

    def search(self, query, min_results=None, exclude=()):

        target = min_results or self.min_results
        exclude = set(exclude)
        urls = []
        seen = set(exclude)

        for _ in range(self.max_attempts):
            for result in self._search_once(query, target):
                url = result.get("href")
                if url and url not in seen:
                    seen.add(url)
                    urls.append(url)

            if len(urls) >= target:
                break

            time.sleep(self.delay_seconds)

        return urls

    def _search_once(self, query, target):
        requested_results = max(target * 2, target + 5)
        try:
            return DDGS().text(query, max_results=requested_results)
        except Exception:
            return []
