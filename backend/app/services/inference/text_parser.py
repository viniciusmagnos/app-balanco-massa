import re

import ezdxf


# Patterns for technical text extraction
PK_PATTERN = re.compile(r"Pk\s*=\s*([\d.]+)", re.IGNORECASE)
PE_PATTERN = re.compile(r"Pe\s*=\s*([\d.]+)", re.IGNORECASE)
SLOPE_PATTERN = re.compile(r"i\s*=\s*([\d.]+)\s*%", re.IGNORECASE)
LENGTH_PATTERN = re.compile(r"Pd\s*=\s*([\d.]+)\s*m", re.IGNORECASE)
ELEVATION_PATTERN = re.compile(r"Y\s*=\s*([\d.]+)", re.IGNORECASE)
UTM_PATTERN = re.compile(r"^[EN]\s*=\s*\d{6,}")
STATION_PATTERN = re.compile(r"^\d{3,4}$")


def extract_texts(msp) -> list[dict]:
    """Extract all TEXT and MTEXT entities with position and content."""
    texts = []
    for e in msp:
        if not hasattr(e, "dxf"):
            continue
        dt = e.dxftype()
        if dt == "TEXT":
            content = e.dxf.text.strip()
            x, y, _ = e.dxf.insert
            texts.append({"text": content, "x": x, "y": y, "layer": e.dxf.layer})
        elif dt == "MTEXT":
            content = e.plain_text().strip()
            x, y, _ = e.dxf.insert
            texts.append({"text": content, "x": x, "y": y, "layer": e.dxf.layer})
    return texts


def is_utm_or_irrelevant(text: str) -> bool:
    """Check if text is UTM coordinate or irrelevant."""
    if UTM_PATTERN.match(text):
        return True
    try:
        val = float(text.replace(",", "."))
        if abs(val) > 100_000:
            return True
    except ValueError:
        pass
    return False


def filter_relevant_texts(texts: list[dict]) -> list[dict]:
    """Filter out UTM coordinates and irrelevant texts."""
    return [t for t in texts if not is_utm_or_irrelevant(t["text"])]


def find_station_texts(texts: list[dict]) -> list[dict]:
    """Find texts that look like station numbers (3-4 digit integers)."""
    results = []
    for t in texts:
        txt = t["text"].strip()
        if STATION_PATTERN.match(txt):
            try:
                val = int(txt)
                if 100 <= val <= 9999:
                    results.append({**t, "station_value": val})
            except ValueError:
                pass
    return results


def find_elevation_texts(texts: list[dict]) -> list[dict]:
    """Find texts that look like elevation values (3-4 digit numbers, possibly with decimals)."""
    results = []
    for t in texts:
        txt = t["text"].strip().replace(",", ".")
        try:
            val = float(txt)
            if 10 <= val <= 9999 and not is_utm_or_irrelevant(t["text"]):
                results.append({**t, "elevation_value": val})
        except ValueError:
            pass
    return results


def parse_technical_texts(texts: list[dict]) -> dict:
    """Parse known technical patterns from texts."""
    parsed = {"pk": [], "pe": [], "slopes": [], "lengths": [], "elevations": []}
    for t in texts:
        txt = t["text"]
        m = PK_PATTERN.search(txt)
        if m:
            parsed["pk"].append({**t, "value": float(m.group(1))})
        m = PE_PATTERN.search(txt)
        if m:
            parsed["pe"].append({**t, "value": float(m.group(1))})
        m = SLOPE_PATTERN.search(txt)
        if m:
            parsed["slopes"].append({**t, "value": float(m.group(1))})
        m = LENGTH_PATTERN.search(txt)
        if m:
            parsed["lengths"].append({**t, "value": float(m.group(1))})
        m = ELEVATION_PATTERN.search(txt)
        if m:
            parsed["elevations"].append({**t, "value": float(m.group(1))})
    return parsed
