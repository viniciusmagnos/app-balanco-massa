# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Mass balance calculator ("balanço de massa") for civil engineering earthwork analysis. Reads DWG/DXF road profile drawings, extracts geometric data from specific CAD layers, and computes cut/fill volumes between a design grade line ("greide") and the existing terrain profile, outputting results as a semicolon-delimited CSV.

## Running

```bash
python main.py
```

Requires DWG files in `dwg_teste/` directory. The script auto-converts DWG→DXF (into `dxf_teste/`) using ODA File Converter, then processes each DXF. Output: `areas_por_arquivo_100m.csv`.

## Dependencies

- **ezdxf** — DXF file parsing
- **ODA File Converter** — external executable for DWG→DXF conversion (hardcoded path: `C:\Program Files\ODA\ODAFileConverter 26.10.0\ODAFileConverter.exe`)

No `requirements.txt` exists. Install with: `pip install ezdxf`

## Architecture (single file: main.py)

The processing pipeline:

1. **DWG→DXF conversion** (`convert_dwg_to_dxf`): shells out to ODA File Converter
2. **Geometry extraction** (`explode_to_points`, `line_points`, `arc_points`): decomposes CAD entities (LWPOLYLINE, POLYLINE, LINE, ARC) into discrete (x,y) point lists; arcs are tessellated with configurable segment length
3. **Chain building** (`_sort_and_merge_groups`, `_build_segments`): sorts point groups by x-coordinate, merges adjacent chains, builds directed line segments
4. **Area computation** (`_integrate_segments`, `_fill_cut_between`): trapezoidal integration over 100m bins; computes signed areas (cut vs fill) by comparing VT greide segments against terrain profile segments, handling line intersections within bins
5. **CSV output**: one row per 100m bin with station numbers, distances, and area values

## Key Domain Concepts

- **Layers**: `F-VT-GREIDE` (design vertical grade) and `08-PERFIL RECORTADO$0$Pg-Pf-Terreno` (terrain profile)
- **Stations** ("estacas"): road stationing system; starts at `INITIAL_STATION=1000`, increments by `STATION_INTERVAL=20.0`m
- **Cut** ("corte"): terrain above grade (material to remove); **Fill** ("aterro"): grade above terrain (material to add)
- Areas are divided by 10 (unit conversion from drawing units)
- Processing is done in 100m horizontal bins along the x-axis
