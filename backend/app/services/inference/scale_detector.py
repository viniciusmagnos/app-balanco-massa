import statistics
from collections import Counter

from ...models.domain import ScaleInfo
from .text_parser import find_elevation_texts, find_station_texts, is_utm_or_irrelevant


def _group_by_coord(
    texts: list[dict], key: str, tolerance: float = 5.0, min_size: int = 2
) -> list[list[dict]]:
    """Group texts by a coordinate (x or y) within a tolerance.

    Returns groups with at least `min_size` members.
    """
    if not texts:
        return []

    sorted_texts = sorted(texts, key=lambda t: t[key])
    groups: list[list[dict]] = []
    current: list[dict] = [sorted_texts[0]]

    for t in sorted_texts[1:]:
        if t[key] - current[-1][key] <= tolerance:
            current.append(t)
        else:
            if len(current) >= min_size:
                groups.append(current)
            current = [t]

    if len(current) >= min_size:
        groups.append(current)

    return groups


def _mode_filter(ratios: list[float], tolerance_pct: float = 0.5) -> list[float]:
    """Keep only ratios within tolerance_pct of the most common value."""
    if not ratios:
        return ratios
    rounded = [round(r, 4) for r in ratios]
    most_common_val = Counter(rounded).most_common(1)[0][0]
    filtered = [
        r for r in ratios
        if (1 - tolerance_pct) * most_common_val <= r <= (1 + tolerance_pct) * most_common_val
    ]
    return filtered if filtered else ratios


def _compute_confidence(ratios: list[float], median: float) -> float:
    if len(ratios) >= 3:
        try:
            stdev = statistics.stdev(ratios)
            return max(0.2, min(1.0, 1.0 - stdev / median))
        except statistics.StatisticsError:
            return 0.5
    return 0.3 if ratios else 0.1


def detect_vertical_scale(texts: list[dict]) -> tuple[float, float]:
    """Infer vertical scale from elevation texts aligned in vertical columns.

    Ruler tick marks (e.g. 725, 730, 735, 740...) share the same X position
    and vary only in Y.  The vertical scale is:  v_scale = d_elevation / dy_graphic

    Returns (v_scale, confidence).
    """
    elevation_texts = find_elevation_texts(texts)
    if len(elevation_texts) < 2:
        return 1.0, 0.1

    # Cotas are in vertical columns: same X, different Y.
    groups = _group_by_coord(elevation_texts, key="x", tolerance=5.0, min_size=3)

    ratios = []
    for group in groups:
        group.sort(key=lambda t: t["y"])
        for i in range(len(group) - 1):
            dy = group[i + 1]["y"] - group[i]["y"]
            d_elev = group[i + 1]["elevation_value"] - group[i]["elevation_value"]
            if abs(dy) > 1.0 and abs(d_elev) > 0.1:
                ratio = abs(d_elev / dy)
                if 0.001 <= ratio <= 100.0:
                    ratios.append(ratio)

    if not ratios:
        return 1.0, 0.1

    ratios = _mode_filter(ratios)
    median_ratio = statistics.median(ratios)
    confidence = _compute_confidence(ratios, median_ratio)

    return round(median_ratio, 6), round(confidence, 3)


def _remove_vertical_column_texts(
    texts: list[dict], tolerance: float = 5.0, min_column_size: int = 3
) -> list[dict]:
    """Remove texts that form vertical columns (same X, different Y).

    These are ruler tick marks (elevation labels), not station labels.
    A vertical column is 3+ texts sharing the same X within tolerance.
    """
    if not texts:
        return texts

    # Group by X to find vertical columns
    x_groups = _group_by_coord(texts, key="x", tolerance=tolerance, min_size=min_column_size)

    # Collect texts that belong to any vertical column
    column_texts = set()
    for group in x_groups:
        for t in group:
            column_texts.add(id(t))

    return [t for t in texts if id(t) not in column_texts]


def detect_horizontal_scale(
    station_texts: list[dict], station_interval: float = 20.0
) -> tuple[float, float]:
    """Infer horizontal scale from station texts aligned in horizontal rows.

    Station labels (e.g. 1280, 1285, 1290...) share the same Y position and
    vary only in X.  The horizontal scale is:
        h_scale = (d_station × station_interval) / dx_graphic

    Returns (h_scale, confidence).
    """
    if len(station_texts) < 2:
        return 1.0, 0.1

    # Remove elevation ruler texts (vertical columns: same X, different values)
    filtered_texts = _remove_vertical_column_texts(station_texts)
    if len(filtered_texts) < 2:
        filtered_texts = station_texts  # fallback to all if too aggressive

    # Stations are in horizontal rows: same Y, different X.
    # Use a wider tolerance for Y because at section breaks the labels have
    # a slight Y offset to avoid overlap.
    groups = _group_by_coord(filtered_texts, key="y", tolerance=15.0, min_size=3)

    ratios = []
    for group in groups:
        group.sort(key=lambda t: t["x"])
        for i in range(len(group) - 1):
            dx = group[i + 1]["x"] - group[i]["x"]
            d_station = group[i + 1]["station_value"] - group[i]["station_value"]
            if dx > 1.0 and d_station > 0:
                real_dist = d_station * station_interval
                ratio = real_dist / dx
                if 0.01 <= ratio <= 1000.0:
                    ratios.append(ratio)

    if not ratios:
        # Fallback: use all station texts sorted by X (no Y grouping)
        sorted_texts = sorted(station_texts, key=lambda t: t["x"])
        for i in range(len(sorted_texts) - 1):
            dx = sorted_texts[i + 1]["x"] - sorted_texts[i]["x"]
            d_station = sorted_texts[i + 1]["station_value"] - sorted_texts[i]["station_value"]
            if dx > 1.0 and d_station > 0:
                real_dist = d_station * station_interval
                ratio = real_dist / dx
                if 0.01 <= ratio <= 1000.0:
                    ratios.append(ratio)

    if not ratios:
        return 1.0, 0.1

    ratios = _mode_filter(ratios)
    median_ratio = statistics.median(ratios)
    confidence = _compute_confidence(ratios, median_ratio)

    return round(median_ratio, 6), round(confidence, 3)


def detect_scales(
    texts: list[dict],
    station_texts: list[dict],
    station_interval: float = 20.0,
) -> ScaleInfo:
    """Detect both horizontal and vertical scales."""
    v_scale, v_conf = detect_vertical_scale(texts)
    h_scale, h_conf = detect_horizontal_scale(station_texts, station_interval)

    return ScaleInfo(
        h_scale=h_scale,
        v_scale=v_scale,
        h_confidence=h_conf,
        v_confidence=v_conf,
    )
