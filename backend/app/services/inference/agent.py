import logging

import ezdxf

from ...models.domain import LayerCandidate, SectionInfo, ScaleInfo
from ...models.schemas import AnalysisResult
from .text_parser import extract_texts, filter_relevant_texts, find_station_texts
from .layer_detector import detect_layers
from .section_detector import detect_sections
from .scale_detector import detect_scales
from . import llm_fallback

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.5


def analyze_dxf(file_id: str, dxf_path: str) -> AnalysisResult:
    """Run the full inference pipeline on a DXF file.

    Flow: heuristics first -> GPT fallback if confidence < threshold.
    """
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    # 1. Extract all text entities
    all_texts = extract_texts(msp)
    relevant_texts = filter_relevant_texts(all_texts)
    station_texts = find_station_texts(relevant_texts)

    # 2. Detect layers
    greide_candidates, terreno_candidates = detect_layers(doc)

    # LLM fallback for layers if top confidence is low
    if (
        (not greide_candidates or greide_candidates[0].confidence < CONFIDENCE_THRESHOLD)
        or (not terreno_candidates or terreno_candidates[0].confidence < CONFIDENCE_THRESHOLD)
    ):
        logger.info("Layer confidence low, trying LLM fallback")
        _try_llm_layer_fallback(doc, msp, greide_candidates, terreno_candidates)

    # 3. Detect sections (using best greide candidate)
    best_greide = greide_candidates[0].name if greide_candidates else ""
    sections = []
    if best_greide:
        sections = detect_sections(msp, best_greide, station_texts)

    # LLM fallback for sections
    if not sections or all(s.confidence < CONFIDENCE_THRESHOLD for s in sections):
        logger.info("Section confidence low, trying LLM fallback")
        _try_llm_section_fallback(sections, msp, all_texts)

    # 4. Detect scales for each section
    for section in sections:
        section_station_texts = [
            t for t in station_texts
            if section.x_start - 50 <= t["x"] <= section.x_end + 50
        ]
        scale_info = detect_scales(
            relevant_texts, section_station_texts, section.station_interval
        )
        section.h_scale = scale_info.h_scale
        section.v_scale = scale_info.v_scale
        # Update confidence incorporating scale confidence
        scale_conf = (scale_info.h_confidence + scale_info.v_confidence) / 2.0
        section.confidence = round((section.confidence + scale_conf) / 2.0, 3)

    # If no sections found at all, create a default one
    if not sections:
        sections = _create_default_section(msp, best_greide)

    # Calculate overall confidence
    all_confs = []
    if greide_candidates:
        all_confs.append(greide_candidates[0].confidence)
    if terreno_candidates:
        all_confs.append(terreno_candidates[0].confidence)
    all_confs.extend(s.confidence for s in sections)
    overall = sum(all_confs) / len(all_confs) if all_confs else 0.0

    all_layers = [layer.dxf.name for layer in doc.layers]

    return AnalysisResult(
        file_id=file_id,
        layers=all_layers,
        greide_candidates=greide_candidates[:5],
        terreno_candidates=terreno_candidates[:5],
        sections=sections,
        overall_confidence=round(overall, 3),
    )


def _try_llm_layer_fallback(doc, msp, greide_candidates, terreno_candidates):
    """Try LLM fallback for layer detection."""
    entities_by_layer: dict[str, dict] = {}
    for e in msp:
        if not hasattr(e, "dxf"):
            continue
        layer = e.dxf.layer
        if layer not in entities_by_layer:
            entities_by_layer[layer] = {"entity_types": set(), "count": 0}
        entities_by_layer[layer]["entity_types"].add(e.dxftype())
        entities_by_layer[layer]["count"] += 1

    layer_stats = {
        k: {"entity_types": list(v["entity_types"]), "count": v["count"]}
        for k, v in entities_by_layer.items()
    }

    result = llm_fallback.analyze_layers(layer_stats)
    if result:
        if "greide" in result and not any(
            c.name == result["greide"] for c in greide_candidates
        ):
            greide_candidates.insert(0, LayerCandidate(
                name=result["greide"], role="greide", confidence=0.6
            ))
        if "terreno" in result and not any(
            c.name == result["terreno"] for c in terreno_candidates
        ):
            terreno_candidates.insert(0, LayerCandidate(
                name=result["terreno"], role="terreno", confidence=0.6
            ))


def _try_llm_section_fallback(sections, msp, texts):
    """Try LLM fallback for section detection."""
    geometry_summary = {"entity_count": sum(1 for _ in msp)}
    text_dicts = [{"text": t["text"], "x": round(t["x"], 1), "y": round(t["y"], 1)} for t in texts[:50]]

    result = llm_fallback.analyze_sections(geometry_summary, text_dicts)
    if result and isinstance(result, list):
        for i, s in enumerate(result):
            sections.append(SectionInfo(
                id=len(sections) + 1,
                x_start=s.get("x_start", 0),
                x_end=s.get("x_end", 0),
                initial_station=s.get("initial_station", 1000),
                confidence=0.5,
            ))


def _create_default_section(msp, greide_layer: str) -> list[SectionInfo]:
    """Create a default section spanning all geometry."""
    from ...core.geometry import extract_layer_polylines
    from ...core.segments import _sort_and_merge_groups

    if not greide_layer:
        return [SectionInfo(id=1, x_start=0, x_end=1000, confidence=0.1)]

    groups = extract_layer_polylines(msp, greide_layer)
    chains = _sort_and_merge_groups(groups)

    if not chains:
        return [SectionInfo(id=1, x_start=0, x_end=1000, confidence=0.1)]

    all_x = [p[0] for chain in chains for p in chain]
    return [SectionInfo(
        id=1,
        x_start=round(min(all_x), 2),
        x_end=round(max(all_x), 2),
        confidence=0.2,
    )]
