# Tuncay Bayır - 21.08.2026
import re

MIN_SENTENCE_WORDS = 5
MIN_PIPE_COUNT_FOR_TABLE = 2
IDEAL_LENGTH_RANGE = (10, 30)

FREQUENCY_WEIGHT = 0.35
POSITION_WEIGHT = 0.2
LENGTH_WEIGHT = 0.3
NAV_PENALTY_WEIGHT = 0.15

FREQUENCY_CAP = 3
OBJECT_ABSENT_PENALTY = 0.6
CONTEXT_BONUS_WEIGHT = 0.05

WORD_PATTERN = re.compile(r"[a-zA-ZçÇğĞıİöÖşŞüÜ']+")
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")
CITATION_ENTRY_PATTERN = re.compile(r"^-\s*(↑|\d+(\s+\d+)*\s)")
UNRENDERED_TEMPLATE_PATTERN = re.compile(r"%[A-Za-z]\w*%")

NAV_HEADING_PATTERN = re.compile(
    r"^(skip to|page contents|table of contents|so,? what is|so what is|what is a|"
    r"what family|what makes|showing \d+\s*-\s*\d+|shop |select the department|"
    r"deliver to|account & lists|cart\b)",
    re.IGNORECASE,
)
NAV_RUN_PATTERN = re.compile(r"(?:\b[A-Z][a-zA-Z']*\b[ &]?){6,}")
NAV_RUN_COVERAGE_THRESHOLD = 0.35

CONTENT_WORD_OVERLAP_THRESHOLD = 0.6

STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being", "of", "in", "on", "at", "to", "for",
    "and", "or", "but", "with", "as", "by", "from", "that", "this", "these", "those", "it", "its", "its'",
    "also", "often", "called", "known", "which", "who", "what", "when", "where", "how", "why", "not", "no",
    "has", "have", "had", "can", "could", "will", "would", "should", "may", "might", "than", "then", "so",
    "such", "some", "most", "more", "other", "into", "about", "up", "out", "if", "because", "between",
}


def summarize_contents(contents, keywords, object_name, context_terms=(), sentence_count=5):
    keyword_set = _build_keyword_set(keywords, object_name)
    context_set = {token for term in context_terms for token in term.lower().split()}
    object_tokens = set(object_name.lower().split())

    candidates = []
    for content in contents:
        sentences = _split_sentences(content.get("text", ""))
        for index, sentence in enumerate(sentences):
            score = _score_sentence(sentence, index, len(sentences), keyword_set, object_tokens, context_set)
            candidates.append({"sentence": sentence, "score": score, "index": index})

    if not candidates:
        return ""

    ranked = sorted(candidates, key=lambda c: c["score"], reverse=True)

    selected = []
    selected_content_words = []
    for candidate in ranked:
        content_words = _content_words(candidate["sentence"])

        is_dup = any(
            _overlap_coefficient(content_words, other) >= CONTENT_WORD_OVERLAP_THRESHOLD
            for other in selected_content_words
        )
        if is_dup:
            continue

        selected.append(candidate)
        selected_content_words.append(content_words)
        if len(selected) >= sentence_count:
            break

    top_in_order = sorted(selected, key=lambda c: c["index"])
    return " ".join(c["sentence"] for c in top_in_order)


def _content_words(sentence):
    words = WORD_PATTERN.findall(sentence.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 2}


def _overlap_coefficient(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def _split_sentences(text):
    flattened = text.replace("\n", " ")
    sentences = SENTENCE_SPLIT_PATTERN.split(flattened)
    return [s.strip() for s in sentences if _is_usable_sentence(s)]


def _is_usable_sentence(sentence):
    if len(sentence.split()) < MIN_SENTENCE_WORDS:
        return False

    if sentence.count("|") >= MIN_PIPE_COUNT_FOR_TABLE:
        return False

    if UNRENDERED_TEMPLATE_PATTERN.search(sentence):
        return False

    return not CITATION_ENTRY_PATTERN.match(sentence)


def _is_nav_or_question(sentence):
    if sentence.rstrip().endswith("?"):
        return True
    if NAV_HEADING_PATTERN.search(sentence.strip()):
        return True

    matches = NAV_RUN_PATTERN.findall(sentence)
    if matches:
        covered = sum(len(m) for m in matches)
        if covered / max(len(sentence), 1) > NAV_RUN_COVERAGE_THRESHOLD:
            return True

    return False


def _build_keyword_set(keywords, object_name):
    return {
        token
        for term in [*keywords, object_name]
        for token in term.lower().split()
    }


def _score_sentence(sentence, index, total_sentences, keyword_set, object_tokens, context_set=frozenset()):
    words = WORD_PATTERN.findall(sentence.lower())
    if not words:
        return 0.0

    raw_hits = sum(1 for word in words if word in keyword_set)
    frequency_score = min(raw_hits, FREQUENCY_CAP) / len(words)
    if object_tokens and not (set(words) & object_tokens):
        frequency_score *= OBJECT_ABSENT_PENALTY

    position_score = 1 - (index / max(total_sentences, 1))
    length_score = _length_score(len(words))
    nav_penalty = NAV_PENALTY_WEIGHT if _is_nav_or_question(sentence) else 0.0
    context_bonus = CONTEXT_BONUS_WEIGHT if (context_set and set(words) & context_set) else 0.0

    return (
        frequency_score * FREQUENCY_WEIGHT
        + position_score * POSITION_WEIGHT
        + length_score * LENGTH_WEIGHT
        - nav_penalty
        + context_bonus
    )


def _length_score(word_count):
    lower, upper = IDEAL_LENGTH_RANGE

    if lower <= word_count <= upper:
        return 1.0
    if word_count < lower:
        return word_count / lower

    return max(0.0, 1 - (word_count - upper) / upper)
