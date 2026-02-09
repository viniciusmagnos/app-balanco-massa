import statistics

from ...models.domain import SectionInfo
from ...core.geometry import extract_layer_polylines
from ...core.segments import _sort_and_merge_groups
from .text_parser import find_station_texts


def _detect_gaps(chains, gap_threshold: float = 50.0, y_gap_threshold: float = 20.0) -> list[tuple[float, float]]:
    """Detect sections by finding gaps between chains.

    Gaps are detected both by X-axis discontinuities (horizontal gaps) and by
    Y-axis discontinuities at shared X boundaries (vertical jumps indicating
    a break in the profile, e.g. station 1309 → 1320).
    """
    if not chains:
        return []

    # Build (x_min, x_max, y_at_end, y_at_start) for each chain
    chain_info = []
    for chain in chains:
        xs = [p[0] for p in chain]
        x_min, x_max = min(xs), max(xs)
        # Find y at the rightmost x (end of chain)
        rightmost = max(chain, key=lambda p: p[0])
        # Find y at the leftmost x (start of chain)
        leftmost = min(chain, key=lambda p: p[0])
        chain_info.append((x_min, x_max, leftmost[1], rightmost[1]))

    chain_info.sort(key=lambda c: c[0])

    sections = [(chain_info[0][0], chain_info[0][1])]
    prev_y_end = chain_info[0][3]  # y at the right end of previous chain

    for x_start, x_end, y_start, y_end in chain_info[1:]:
        prev_x_end = sections[-1][1]
        x_gap = x_start - prev_x_end

        if x_gap > gap_threshold:
            # Clear horizontal gap → new section
            sections.append((x_start, x_end))
        elif abs(x_gap) <= gap_threshold and abs(y_start - prev_y_end) > y_gap_threshold:
            # Chains touch/overlap in X but have a large Y jump → new section
            sections.append((x_start, x_end))
        else:
            # Continuous → extend current section
            sections[-1] = (sections[-1][0], max(sections[-1][1], x_end))

        prev_y_end = y_end

    return sections


def _infer_station_interval(
    station_texts: list[dict], x_start: float, x_end: float, tolerance: float = 50.0
) -> tuple[float, float]:
    """Infer station interval from station texts within a section range.

    Returns (interval, confidence).
    """
    # Filter texts within this section's x range (with tolerance)
    relevant = [
        t for t in station_texts
        if x_start - tolerance <= t["x"] <= x_end + tolerance
    ]

    if len(relevant) < 2:
        return 20.0, 0.1  # default

    # Sort by x position
    relevant.sort(key=lambda t: t["x"])

    intervals = []
    for i in range(len(relevant) - 1):
        dx = relevant[i + 1]["x"] - relevant[i]["x"]
        d_station = relevant[i + 1]["station_value"] - relevant[i]["station_value"]
        if d_station != 0 and dx > 0:
            interval = dx / d_station
            if 1.0 <= interval <= 100.0:  # sanity check
                intervals.append(interval)

    if not intervals:
        return 20.0, 0.1

    median_interval = statistics.median(intervals)
    # Confidence based on consistency
    if len(intervals) >= 3:
        try:
            stdev = statistics.stdev(intervals)
            confidence = max(0.1, min(1.0, 1.0 - stdev / median_interval))
        except statistics.StatisticsError:
            confidence = 0.5
    else:
        confidence = 0.4

    return round(median_interval, 2), round(confidence, 3)


def _find_initial_station(
    station_texts: list[dict], x_start: float, x_end: float,
    tolerance: float = 100.0,
) -> tuple[float, float]:
    """Find the initial station for a section.

    At a section break, two station texts may share the same X: the last station
    of the previous section and the first of the new one. We pick the smallest
    station value whose text lies within this section's X range.

    Returns (station_value, confidence).
    """
    # Find texts near x_start
    near_start = [
        t for t in station_texts
        if abs(t["x"] - x_start) <= tolerance
    ]

    if not near_start:
        return 1000.0, 0.1

    # Sort by proximity to x_start
    near_start.sort(key=lambda t: abs(t["x"] - x_start))
    closest_dist = abs(near_start[0]["x"] - x_start)

    # Get all candidates at the same (closest) distance
    closest_group = [
        t for t in near_start
        if abs(abs(t["x"] - x_start) - closest_dist) < 1.0
    ]

    if len(closest_group) > 1:
        # Multiple station texts at the same X (break point).
        # The smaller value is the end of the previous section, the larger is the
        # start of this section.  Pick the largest that still looks like a "start"
        # (i.e. the minimum station whose text is at or after x_start).
        after = [t for t in closest_group if t["x"] >= x_start - 1.0]
        if after:
            # Pick the max station value — it's the start of the new section
            best = max(after, key=lambda t: t["station_value"])
        else:
            best = closest_group[0]
    else:
        best = closest_group[0]

    distance = abs(best["x"] - x_start)
    confidence = max(0.2, 1.0 - distance / tolerance)

    return float(best["station_value"]), round(confidence, 3)


def detect_sections(
    msp, greide_layer: str, station_texts: list[dict] | None = None
) -> list[SectionInfo]:
    """Detect sections from greide layer polylines."""
    groups = extract_layer_polylines(msp, greide_layer)
    chains = _sort_and_merge_groups(groups)

    if not chains:
        return []

    section_ranges = _detect_gaps(chains)

    if station_texts is None:
        station_texts = []

    sections = []
    for i, (x_start, x_end) in enumerate(section_ranges):
        initial_station, st_conf = _find_initial_station(station_texts, x_start, x_end)
        station_interval, int_conf = _infer_station_interval(
            station_texts, x_start, x_end
        )
        confidence = (st_conf + int_conf) / 2.0

        sections.append(SectionInfo(
            id=i + 1,
            x_start=round(x_start, 2),
            x_end=round(x_end, 2),
            initial_station=initial_station,
            station_interval=station_interval,
            confidence=round(confidence, 3),
        ))

    return sections
