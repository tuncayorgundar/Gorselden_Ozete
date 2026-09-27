# Tuncay Bayır - 20.08.2026
DEFAULT_HISTORY_SIZE = 3
DEFAULT_KEYWORDS_PER_ENTRY = 1
DEFAULT_MAX_CONTEXT_TERMS = 4


class ConversationContext:
    def __init__(
        self,
        history_size=DEFAULT_HISTORY_SIZE,
        keywords_per_entry=DEFAULT_KEYWORDS_PER_ENTRY,
        max_context_terms=DEFAULT_MAX_CONTEXT_TERMS,
    ):
        self.history_size = history_size
        self.keywords_per_entry = keywords_per_entry
        self.max_context_terms = max_context_terms
        self._entries = []

    def remember(self, object_name, keywords):
        self._entries.append((object_name, list(keywords)))
        self._entries = self._entries[-self.history_size:]

    def previous_terms(self, object_name, keywords):
        seen = {term.lower() for term in [object_name, *keywords]}
        terms = []

        for past_name, past_keywords in reversed(self._entries):
            for term in [past_name, *past_keywords[:self.keywords_per_entry]]:
                if term.lower() in seen:
                    continue

                seen.add(term.lower())
                terms.append(term)

                if len(terms) >= self.max_context_terms:
                    return terms

        return terms
