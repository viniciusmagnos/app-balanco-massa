import re
import ezdxf

from ...models.domain import LayerCandidate
from ...core.geometry import explode_to_points


GREIDE_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [r"GREIDE", r"GRADE", r"PROJETO", r"EIXO", r"VT", r"DESIGN"]
]
TERRENO_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [r"TERRENO", r"TN", r"NATURAL", r"EXISTENTE", r"GROUND", r"PERFIL"]
]


def _pattern_score(layer_name: str, patterns: list[re.Pattern]) -> float:
    """Score based on pattern matching (0.0-1.0)."""
    matches = sum(1 for p in patterns if p.search(layer_name))
    return min(1.0, matches / 2.0)


def _geometric_score(entities: list) -> tuple[float, int, float]:
    """Analyze geometric properties of layer entities.

    Returns (score, entity_count, total_length).
    Prefers layers with few long open polylines (typical of profiles).
    """
    if not entities:
        return 0.0, 0, 0.0

    polyline_count = 0
    open_polyline_count = 0
    max_length = 0.0
    total_length = 0.0

    for e in entities:
        dt = e.dxftype()
        if dt in ("LWPOLYLINE", "POLYLINE"):
            polyline_count += 1
            try:
                is_closed = e.is_closed if dt == "LWPOLYLINE" else e.is_closed
                if not is_closed:
                    open_polyline_count += 1
            except Exception:
                open_polyline_count += 1

            pts = explode_to_points(e)
            if len(pts) >= 2:
                xs = [p[0] for p in pts]
                length = max(xs) - min(xs)
                max_length = max(max_length, length)
                total_length += length

    if polyline_count == 0:
        return 0.1, len(entities), 0.0

    # Prefer: few polylines (1-3), mostly open, long
    count_score = 1.0 if 1 <= open_polyline_count <= 3 else max(0.0, 1.0 - (open_polyline_count - 3) * 0.1)
    length_score = min(1.0, max_length / 500.0)  # normalize by expected min length

    score = 0.5 * count_score + 0.5 * length_score
    return score, len(entities), total_length


def detect_layers(doc) -> tuple[list[LayerCandidate], list[LayerCandidate]]:
    """Detect greide and terreno layer candidates.

    Returns (greide_candidates, terreno_candidates) sorted by confidence desc.
    """
    msp = doc.modelspace()

    # Group entities by layer
    entities_by_layer: dict[str, list] = {}
    for e in msp:
        if not hasattr(e, "dxf"):
            continue
        layer = e.dxf.layer
        entities_by_layer.setdefault(layer, []).append(e)

    all_layers = [layer.dxf.name for layer in doc.layers]

    greide_candidates = []
    terreno_candidates = []

    for layer_name in all_layers:
        ents = entities_by_layer.get(layer_name, [])
        geo_score, entity_count, total_length = _geometric_score(ents)

        # Greide scoring
        pat_score = _pattern_score(layer_name, GREIDE_PATTERNS)
        if pat_score > 0 or geo_score > 0.3:
            confidence = 0.4 * pat_score + 0.6 * geo_score
            if confidence > 0.05:
                greide_candidates.append(LayerCandidate(
                    name=layer_name,
                    role="greide",
                    confidence=round(confidence, 3),
                    entity_count=entity_count,
                    total_length=round(total_length, 2),
                ))

        # Terreno scoring
        pat_score = _pattern_score(layer_name, TERRENO_PATTERNS)
        if pat_score > 0 or geo_score > 0.3:
            confidence = 0.4 * pat_score + 0.6 * geo_score
            if confidence > 0.05:
                terreno_candidates.append(LayerCandidate(
                    name=layer_name,
                    role="terreno",
                    confidence=round(confidence, 3),
                    entity_count=entity_count,
                    total_length=round(total_length, 2),
                ))

    greide_candidates.sort(key=lambda c: c.confidence, reverse=True)
    terreno_candidates.sort(key=lambda c: c.confidence, reverse=True)

    return greide_candidates, terreno_candidates
