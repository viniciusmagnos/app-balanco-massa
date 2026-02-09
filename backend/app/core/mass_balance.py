from .segments import _y_interp, _integrate_segments


def _x_lines_intercept(x1, y1, x2, y2, x3, y3, x4, y4):
    a1 = (y2 - y1) / (x2 - x1) if x2 != x1 else float('inf')
    a2 = (y4 - y3) / (x4 - x3) if x4 != x3 else float('inf')
    if a1 == a2:
        return None
    if a1 == float('inf'):
        return x1
    if a2 == float('inf'):
        return x3
    b1 = y1 - a1 * x1
    b2 = y3 - a2 * x3
    return (b2 - b1) / (a1 - a2)


def _y_on_segments(segs, x, s):
    for x1, y1, x2, y2 in segs:
        if s == 'l' and x == x2:
            continue
        if s == 'r' and x == x1:
            continue
        if x1 <= x <= x2:
            return _y_interp(x1, y1, x2, y2, x)
    return None


def _fill_cut_between(vt_segs, pf_segs, a, b):
    if b <= a:
        return 0.0, 0.0
    breaks = {a, b}
    for x1, _, x2, _ in vt_segs:
        if x2 <= a or x1 >= b:
            continue
        breaks.add(max(a, x1))
        breaks.add(min(b, x2))
    for x1, _, x2, _ in pf_segs:
        if x2 <= a or x1 >= b:
            continue
        breaks.add(max(a, x1))
        breaks.add(min(b, x2))
    xs = sorted(breaks)
    fill = 0.0
    cut = 0.0
    for xL, xR in zip(xs, xs[1:]):
        if xR <= xL:
            continue
        vtL = _y_on_segments(vt_segs, xL, 'l')
        vtR = _y_on_segments(vt_segs, xR, 'r')
        pfL = _y_on_segments(pf_segs, xL, 'l')
        pfR = _y_on_segments(pf_segs, xR, 'r')
        if None in (vtL, vtR, pfL, pfR):
            continue

        if ((vtL - pfL) * (vtR - pfR)) < 0:
            x_int = _x_lines_intercept(xL, vtL, xR, vtR, xL, pfL, xR, pfR)
            if x_int is None or x_int <= xL or x_int >= xR:
                dL = vtL - pfL
                dR = vtR - pfR
                area = (xR - xL) * (dL + dR) / 2.0
                if area > 0:
                    fill += area
                else:
                    cut += -area
            else:
                dL = vtL - pfL
                area1 = (x_int - xL) * (dL + 0.0) / 2.0
                if dL > 0:
                    fill += area1
                else:
                    cut += -area1
                dR = vtR - pfR
                area2 = (xR - x_int) * (0.0 + dR) / 2.0
                if dR > 0:
                    fill += area2
                else:
                    cut += -area2
        else:
            dL = vtL - pfL
            dR = vtR - pfR
            area = (xR - xL) * (dL + dR) / 2.0
            if area > 0:
                fill += area
            else:
                cut += -area
    return fill, cut


def compute_mass_balance_bins(
    vt_segs, pf_segs, x_start, x_end, bin_width,
) -> list[dict]:
    """Compute cut/fill areas in bins, returning a list of dicts."""
    results = []
    x_cur = x_start
    while x_cur < x_end - 1e-9:
        a = x_cur
        b = min(x_cur + bin_width, x_end)

        area_vt = _integrate_segments(vt_segs, a, b)
        area_pf = _integrate_segments(pf_segs, a, b)
        area_diff = area_vt - area_pf
        fill_bin, cut_bin = _fill_cut_between(vt_segs, pf_segs, a, b)

        results.append({
            "x_start": a,
            "x_end": b,
            "dist_m": b - a,
            "area_vt": area_vt,
            "area_pf": area_pf,
            "area_diff": area_diff,
            "cut": cut_bin,
            "fill": fill_bin,
        })
        x_cur += bin_width

    return results
