from pydantic import BaseModel
from .domain import LayerCandidate, SectionInfo


class UploadResponse(BaseModel):
    file_id: str
    filename: str
    file_type: str  # "dwg" or "dxf"


class AnalysisResult(BaseModel):
    file_id: str
    layers: list[str]
    greide_candidates: list[LayerCandidate]
    terreno_candidates: list[LayerCandidate]
    sections: list[SectionInfo]
    overall_confidence: float


class SectionParams(BaseModel):
    id: int
    x_start: float
    x_end: float
    initial_station: float
    station_interval: float
    bin_width: float = 100.0
    h_scale: float = 1.0
    v_scale: float = 1.0


class CalculationRequest(BaseModel):
    greide_layer: str
    terreno_layer: str
    sections: list[SectionParams]


class BinResult(BaseModel):
    section_id: int
    x_start: float
    x_end: float
    station_start: float
    station_end: float
    dist_m: float
    dist_stations: float
    area_vt: float
    area_pf: float
    area_diff: float
    cut: float
    fill: float


class ProfilePoint(BaseModel):
    station: float
    elevation_greide: float
    elevation_terrain: float


class SectionProfile(BaseModel):
    section_id: int
    points: list[ProfilePoint]


class CalculationResponse(BaseModel):
    result_id: str
    file_id: str
    total_cut: float
    total_fill: float
    sections_processed: int
    bins: list[BinResult]
    profiles: list[SectionProfile] = []


class ResultInfo(BaseModel):
    result_id: str
    filename: str
