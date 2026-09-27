# Tuncay Bayır - 21.08.2026
import re

from content.extractor import is_authority_domain

_DISAMBIGUATION_SUFFIX = re.compile(r"\s*\([^)]*\)\s*$")

def _search_name(class_name):
    return _DISAMBIGUATION_SUFFIX.sub("", class_name).strip() or class_name

class Pipeline:
    def __init__(
        self,
        get_source,
        detector,
        rank_detections,
        find_ambiguous_candidates,
        extract_keywords,
        conversation_context,
        search_client,
        content_extractor,
        summarize_contents,
        repository,
    ):
        self.get_source = get_source
        self.detector = detector
        self.rank_detections = rank_detections
        self.find_ambiguous_candidates = find_ambiguous_candidates
        self.extract_keywords = extract_keywords
        self.conversation_context = conversation_context
        self.search_client = search_client
        self.content_extractor = content_extractor
        self.summarize_contents = summarize_contents
        self.repository = repository

    def run(self, source, on_stage=None, choose_object=None):
        notify = on_stage or (lambda message, kind="stage": None)

        notify("Reading image")
        frame = self.get_source(source)

        notify("Detecting objects")
        result = self.detector.detect(frame)
        detections = result["detections"]

        if not result["confident"]:
            notify("Not confident, closest guesses found")
            self.repository.save(detections, source=source)
            return result

        height, width = frame.shape[:2]
        ranked = self.rank_detections(detections, height, width)
        primary, was_selected = self._select_primary(ranked, notify, choose_object)
        notify(f"Detected: {primary['class_name']}", kind="result")

        self._enrich(primary, notify)

        notify("Saving results")
        self.repository.save(ranked, source=source)

        return {"confident": True, "detections": ranked, "primary": primary, "was_selected": was_selected}

    def _select_primary(self, ranked, notify, choose_object):
        candidates = self.find_ambiguous_candidates(ranked)
        if candidates is None:
            return ranked[0], False

        notify("No single dominant object found, requesting selection")

        if choose_object is None:
            return ranked[0], False

        return choose_object(candidates), True

    def _enrich(self, detection, notify):
        class_name = detection["class_name"]

        notify("Extracting keywords")
        detection["keywords"] = self.extract_keywords(class_name)
        notify(f"Keywords: {', '.join(detection['keywords'])}", kind="result")

        context_terms = self.conversation_context.previous_terms(class_name, detection["keywords"])
        detection["context_terms"] = context_terms

        if context_terms:
            notify(f"Continuing context with {', '.join(context_terms)}")

        search_name = _search_name(class_name)
        query = " ".join([search_name, *detection["keywords"], *context_terms])

        notify("Searching the web")
        urls = self.search_client.search(query)
        tried_urls = list(urls)

        if not urls:
            notify("Web search returned no results")

        notify("Fetching content")
        contents = self.content_extractor.extract(urls, search_name, detection["keywords"])

        min_successful = self.content_extractor.min_successful
        if len(contents) < min_successful and urls:
            notify("Not enough usable pages, searching more")
            more_urls = self.search_client.search(query, min_results=len(urls) * 2, exclude=urls)
            tried_urls += more_urls
            if more_urls:
                contents += self.content_extractor.extract(more_urls, search_name, detection["keywords"])

        if not any(is_authority_domain(c["url"]) for c in contents):
            notify("No authoritative source found, trying a definitional query")
            definitional_urls = self.search_client.search(f"what is a {search_name}", exclude=tried_urls)
            if definitional_urls:
                contents += self.content_extractor.extract(definitional_urls, search_name, detection["keywords"])

        notify("Summarizing")

        detection["summary"] = self.summarize_contents(
            contents, detection["keywords"], search_name, context_terms=context_terms
        )

        self.conversation_context.remember(class_name, detection["keywords"])
