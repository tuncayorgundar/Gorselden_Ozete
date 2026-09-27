# Tuncay Bayır - 19.08.2026
import math

AREA_WEIGHT = 0.7
CONFIDENCE_WEIGHT = 0.3

DOMINANCE_THRESHOLD = 0.55
CANDIDATE_BAND = 0.08

BACKGROUND_PENALTY = 0.45

SURFACE_WIDTH_SPAN = 0.80
SURFACE_BOTTOM_TOLERANCE = 0.03
SUPPORTED_MIN_AREA = 0.02

HELD_MIN_COVERAGE = 0.95
HELD_AREA_RANGE = (0.30, 0.90)


def rank_detections(detections, frame_height, frame_width):
    scored = [
        _with_score(detection, detections, frame_height, frame_width)
        for detection in detections
    ]
    return sorted(scored, key=lambda detection: detection["score"], reverse=True)


def find_ambiguous_candidates(ranked_detections):
    distinct = _unique_by_class(ranked_detections)

    if len(distinct) < 2:
        return None

    top_score = distinct[0]["score"]
    runner_up_score = distinct[1]["score"]

    no_dominant_candidate = top_score < DOMINANCE_THRESHOLD
    top_two_too_close = (top_score - runner_up_score) < CANDIDATE_BAND

    if not (no_dominant_candidate or top_two_too_close):
        return None

    candidates = [detection for detection in distinct if top_score - detection["score"] < CANDIDATE_BAND]

    return candidates if len(candidates) > 1 else None


def _with_score(detection, detections, frame_height, frame_width):

    image_area = frame_height * frame_width

    area_norm = _box_area(detection["box"]) / image_area if image_area else 0
    area_score = math.sqrt(max(area_norm, 0))

    score = AREA_WEIGHT * area_score + CONFIDENCE_WEIGHT * detection["confidence"]

    if _is_background(detection, detections, frame_height, frame_width):
        score *= BACKGROUND_PENALTY

    return {**detection, "score": score}


def _is_background(detection, detections, frame_height, frame_width):

    others = [other for other in detections if other is not detection]

    return (
        _is_support_surface(detection, others, frame_height, frame_width)
        or _holds_another(detection, others)
    )


def _is_support_surface(detection, others, frame_height, frame_width):

    x1, _, x2, y2 = detection["box"]

    spans_frame = frame_width and (x2 - x1) / frame_width >= SURFACE_WIDTH_SPAN
    reaches_bottom = y2 >= frame_height * (1 - SURFACE_BOTTOM_TOLERANCE)

    if not (spans_frame and reaches_bottom):
        return False

    surface_area = _box_area(detection["box"])
    minimum_area = frame_height * frame_width * SUPPORTED_MIN_AREA

    return any(
        minimum_area <= _box_area(other["box"]) < surface_area
        and _intersection_area(detection["box"], other["box"]) > 0
        for other in others
    )


def _holds_another(detection, others):

    holder_area = _box_area(detection["box"])

    if not holder_area:
        return False

    smallest, largest = HELD_AREA_RANGE

    return any(
        smallest <= _box_area(other["box"]) / holder_area <= largest
        and _coverage(other["box"], detection["box"]) >= HELD_MIN_COVERAGE
        for other in others
    )


def _unique_by_class(detections):
    seen = set()
    distinct = []

    for detection in detections:
        if detection["class_name"] in seen:
            continue

        seen.add(detection["class_name"])
        distinct.append(detection)

    return distinct


def _box_area(box):
    x1, y1, x2, y2 = box
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)


def _intersection_area(box, other):
    width = min(box[2], other[2]) - max(box[0], other[0])
    height = min(box[3], other[3]) - max(box[1], other[1])

    return max(0.0, width) * max(0.0, height)


def _coverage(inner, outer):
    inner_area = _box_area(inner)

    return _intersection_area(inner, outer) / inner_area if inner_area else 0.0
