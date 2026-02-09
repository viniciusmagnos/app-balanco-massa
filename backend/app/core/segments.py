def _sort_and_merge_groups(groups):
    if not groups:
        return []
    sorted_groups = sorted(groups, key=lambda g: g[0][0])

    chains = []
    if not sorted_groups:
        return chains

    current_chain = []

    def append_to_chain(chain, points):
        for p in points:
            if not chain or chain[-1] != p:
                chain.append(p)

    append_to_chain(current_chain, sorted_groups[0])

    for g in sorted_groups[1:]:
        if not g:
            continue
        if current_chain and current_chain[-1] == g[0]:
            append_to_chain(current_chain, g)
        else:
            if current_chain:
                chains.append(current_chain)
            current_chain = []
            append_to_chain(current_chain, g)

    if current_chain:
        chains.append(current_chain)

    return chains


def _build_segments(chains):
    segs = []
    for pts in chains:
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            if x2 == x1:
                continue
            if x2 < x1:
                x1, y1, x2, y2 = x2, y2, x1, y1
            segs.append((x1, y1, x2, y2))
    return segs


def _y_interp(x1, y1, x2, y2, x):
    t = (x - x1) / (x2 - x1)
    return y1 + t * (y2 - y1)


def _integrate_segments(segs, a, b):
    if not segs or b <= a:
        return 0.0
    area = 0.0
    for x1, y1, x2, y2 in segs:
        xa = max(a, x1)
        xb = min(b, x2)
        if xb <= xa:
            continue
        ya = _y_interp(x1, y1, x2, y2, xa)
        yb = _y_interp(x1, y1, x2, y2, xb)
        area += (xb - xa) * (ya + yb) / 2.0
    return area


def apply_scales(segments, h_scale: float, v_scale: float):
    """Apply horizontal and vertical scales to segments."""
    return [
        (x1 * h_scale, y1 * v_scale, x2 * h_scale, y2 * v_scale)
        for x1, y1, x2, y2 in segments
    ]


def _y_on_segs(segs, x):
    """Interpolate y at x across segments. Returns None if x is not covered."""
    for x1, y1, x2, y2 in segs:
        if x1 <= x <= x2:
            return _y_interp(x1, y1, x2, y2, x)
    return None


def build_profile_points(vt_segs, pf_segs, x_start, x_end):
    """Build array of {x, y_vt, y_pf} for profile visualization.

    Collects all segment endpoints + regular samples, interpolates both
    profiles at each x, and returns only points where both profiles exist.
    """
    xs = set()
    for x1, _, x2, _ in vt_segs:
        if x2 >= x_start and x1 <= x_end:
            xs.add(max(x1, x_start))
            xs.add(min(x2, x_end))
    for x1, _, x2, _ in pf_segs:
        if x2 >= x_start and x1 <= x_end:
            xs.add(max(x1, x_start))
            xs.add(min(x2, x_end))

    # Add regular samples every ~2 graphic units for smoothness
    step = 2.0
    x = x_start
    while x <= x_end:
        xs.add(x)
        x += step

    xs = sorted(xs)

    points = []
    for x in xs:
        y_vt = _y_on_segs(vt_segs, x)
        y_pf = _y_on_segs(pf_segs, x)
        if y_vt is not None and y_pf is not None:
            points.append({"x": x, "y_vt": y_vt, "y_pf": y_pf})

    return points
