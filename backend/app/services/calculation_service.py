import csv
import uuid
from pathlib import Path

import ezdxf

from ..config import settings
from ..models.schemas import (
    CalculationRequest, CalculationResponse, BinResult,
    ProfilePoint, SectionProfile,
)
from ..core.geometry import extract_layer_polylines
from ..core.segments import (
    _sort_and_merge_groups, _build_segments, apply_scales, build_profile_points,
)
from ..core.mass_balance import compute_mass_balance_bins


def calculate(file_id: str, dxf_path: str, params: CalculationRequest) -> CalculationResponse:
    """Execute mass balance calculation with user-confirmed parameters."""
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    # Extract geometry from chosen layers
    vt_groups = extract_layer_polylines(msp, params.greide_layer)
    pf_groups = extract_layer_polylines(msp, params.terreno_layer)

    vt_chains = _sort_and_merge_groups(vt_groups)
    pf_chains = _sort_and_merge_groups(pf_groups)

    vt_segs_raw = _build_segments(vt_chains)
    pf_segs_raw = _build_segments(pf_chains)

    all_bins: list[BinResult] = []
    all_profiles: list[SectionProfile] = []

    for section in params.sections:
        # Apply scales for this section
        vt_segs = apply_scales(vt_segs_raw, section.h_scale, section.v_scale)
        pf_segs = apply_scales(pf_segs_raw, section.h_scale, section.v_scale)

        # Scale section boundaries too
        x_start = section.x_start * section.h_scale
        x_end = section.x_end * section.h_scale
        bin_width = section.bin_width

        bins = compute_mass_balance_bins(
            vt_segs, pf_segs, x_start, x_end, bin_width,
        )

        current_station = section.initial_station
        for b in bins:
            dist_stations = b["dist_m"] / section.station_interval
            station_start = current_station
            station_end = station_start + dist_stations
            current_station = station_end

            all_bins.append(BinResult(
                section_id=section.id,
                x_start=round(b["x_start"], 4),
                x_end=round(b["x_end"], 4),
                station_start=round(station_start, 4),
                station_end=round(station_end, 4),
                dist_m=round(b["dist_m"], 4),
                dist_stations=round(dist_stations, 4),
                area_vt=round(b["area_vt"], 4),
                area_pf=round(b["area_pf"], 4),
                area_diff=round(b["area_diff"], 4),
                cut=round(b["cut"], 4),
                fill=round(b["fill"], 4),
            ))

        # Build profile points for visualization
        raw_pts = build_profile_points(vt_segs, pf_segs, x_start, x_end)
        profile_points = []
        for pt in raw_pts:
            station = section.initial_station + (pt["x"] - x_start) / section.station_interval
            profile_points.append(ProfilePoint(
                station=round(station, 4),
                elevation_greide=round(pt["y_vt"], 4),
                elevation_terrain=round(pt["y_pf"], 4),
            ))
        all_profiles.append(SectionProfile(
            section_id=section.id,
            points=profile_points,
        ))

    # Generate CSV
    result_id = uuid.uuid4().hex[:12]
    settings.results_dir.mkdir(parents=True, exist_ok=True)
    csv_path = settings.results_dir / f"{result_id}.csv"

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow([
            "trecho", "x_inicio", "x_fim",
            "estaca_inicio", "estaca_fim",
            "distancia_m", "distancia_estacas",
            "area_vt_greide", "area_perfil_recortado",
            "area_diferenca", "area_corte", "area_aterro",
        ])
        for b in all_bins:
            w.writerow([
                b.section_id, b.x_start, b.x_end,
                b.station_start, b.station_end,
                b.dist_m, b.dist_stations,
                b.area_vt, b.area_pf,
                b.area_diff, b.cut, b.fill,
            ])

    total_cut = sum(b.cut for b in all_bins)
    total_fill = sum(b.fill for b in all_bins)
    sections_processed = len(params.sections)

    return CalculationResponse(
        result_id=result_id,
        file_id=file_id,
        total_cut=round(total_cut, 4),
        total_fill=round(total_fill, 4),
        sections_processed=sections_processed,
        bins=all_bins,
        profiles=all_profiles,
    )
