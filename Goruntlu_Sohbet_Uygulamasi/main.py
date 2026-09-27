# Tuncay Bayır - 21.08.2026
import os
import sys

from cli import repl
from content.extractor import ContentExtractor
from content.summarizer import summarize_contents
from conversation_context import ConversationContext
from keywords.keyword_extractor import KeywordExtractor
from pipeline import Pipeline
from repository.json_repository import JsonRepository
from vision.detector import ObjectDetector
from vision.image_source import get_source
from vision.prominence import find_ambiguous_candidates, rank_detections
from web_search.search_client import WebSearchClient

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(PROJECT_ROOT, "data", "models", "yoloe-26l-seg.pt")
DETECTIONS_PATH = os.path.join(PROJECT_ROOT, "data", "detection_records.jsonl")


def build_pipeline():
    keyword_extractor = KeywordExtractor()
    previous_keywords = set()

    def extract_keywords(class_name):
        keywords = keyword_extractor.tag(class_name, exclude=previous_keywords)
        previous_keywords.clear()
        previous_keywords.update(keywords)
        return keywords

    return Pipeline(
        get_source=get_source,
        detector=ObjectDetector(model_path=MODEL_PATH),
        rank_detections=rank_detections,
        find_ambiguous_candidates=find_ambiguous_candidates,
        extract_keywords=extract_keywords,
        conversation_context=ConversationContext(),
        search_client=WebSearchClient(),
        content_extractor=ContentExtractor(),
        summarize_contents=summarize_contents,
        repository=JsonRepository(file_path=DETECTIONS_PATH),
    )


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")

    pipeline = build_pipeline()
    repl(pipeline.run)


if __name__ == "__main__":
    main()
