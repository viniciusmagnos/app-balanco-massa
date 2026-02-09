import math
import ezdxf


def line_points(e):
    x1, y1, _ = e.dxf.start
    x2, y2, _ = e.dxf.end
    return [(x1, y1), (x2, y2)]


def arc_points(e, max_seg_len=0.5):
    cx, cy, _ = e.dxf.center
    r = float(e.dxf.radius)
    sa = math.radians(float(e.dxf.start_angle))
    ea = math.radians(float(e.dxf.end_angle))
    delta = ea - sa
    if delta < 0:
        delta += 2 * math.pi
    arc_len = abs(delta) * r
    n = max(2, int(math.ceil(arc_len / max_seg_len)))
    pts = []
    for i in range(n + 1):
        a = sa + delta * (i / n)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def explode_to_points(e, max_seg_len=0.5):
    pts = []
    dt = e.dxftype()
    if dt in ("LWPOLYLINE", "POLYLINE"):
        for prim in e.virtual_entities():
            if prim.dxftype() == "LINE":
                pts.extend(line_points(prim))
            elif prim.dxftype() == "ARC":
                pts.extend(arc_points(prim, max_seg_len))
    elif dt == "LINE":
        pts.extend(line_points(e))
    elif dt == "ARC":
        pts.extend(arc_points(e, max_seg_len))
    return pts


def extract_layer_polylines(msp, layer_name: str) -> list[list[tuple[float, float]]]:
    """Extract points from all entities on a given layer."""
    groups = []
    for e in msp:
        if not hasattr(e, "dxf") or e.dxf.layer != layer_name:
            continue
        pts = explode_to_points(e, max_seg_len=0.5)
        if pts:
            groups.append(pts)
    return groups
