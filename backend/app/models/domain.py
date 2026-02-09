from pydantic import BaseModel


class LayerCandidate(BaseModel):
    name: str
    role: str  # "greide" or "terreno"
    confidence: float
    entity_count: int = 0
    total_length: float = 0.0


class SectionInfo(BaseModel):
    id: int
    x_start: float
    x_end: float
    initial_station: float = 1000.0
    station_interval: float = 20.0
    bin_width: float = 100.0
    h_scale: float = 1.0
    v_scale: float = 1.0
    confidence: float = 0.0


class ScaleInfo(BaseModel):
    h_scale: float = 1.0
    v_scale: float = 1.0
    h_confidence: float = 0.0
    v_confidence: float = 0.0
