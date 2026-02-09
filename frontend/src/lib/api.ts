const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, options);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  return res.json();
}

export interface UploadResponse {
  file_id: string;
  filename: string;
  file_type: string;
}

export interface LayerCandidate {
  name: string;
  role: string;
  confidence: number;
  entity_count: number;
  total_length: number;
}

export interface SectionInfo {
  id: number;
  x_start: number;
  x_end: number;
  initial_station: number;
  station_interval: number;
  bin_width: number;
  h_scale: number;
  v_scale: number;
  confidence: number;
}

export interface AnalysisResult {
  file_id: string;
  layers: string[];
  greide_candidates: LayerCandidate[];
  terreno_candidates: LayerCandidate[];
  sections: SectionInfo[];
  overall_confidence: number;
}

export interface SectionParams {
  id: number;
  x_start: number;
  x_end: number;
  initial_station: number;
  station_interval: number;
  bin_width: number;
  h_scale: number;
  v_scale: number;
}

export interface CalculationRequest {
  greide_layer: string;
  terreno_layer: string;
  sections: SectionParams[];
}

export interface BinResult {
  section_id: number;
  x_start: number;
  x_end: number;
  station_start: number;
  station_end: number;
  dist_m: number;
  dist_stations: number;
  area_vt: number;
  area_pf: number;
  area_diff: number;
  cut: number;
  fill: number;
}

export interface ProfilePoint {
  station: number;
  elevation_greide: number;
  elevation_terrain: number;
}

export interface SectionProfile {
  section_id: number;
  points: ProfilePoint[];
}

export interface CalculationResponse {
  result_id: string;
  file_id: string;
  total_cut: number;
  total_fill: number;
  sections_processed: number;
  bins: BinResult[];
  profiles: SectionProfile[];
}

export async function uploadFile(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  return request<UploadResponse>("/upload", {
    method: "POST",
    body: form,
  });
}

export async function analyzeFile(fileId: string): Promise<AnalysisResult> {
  return request<AnalysisResult>(`/analyze/${fileId}`, { method: "POST" });
}

export async function calculateFile(
  fileId: string,
  params: CalculationRequest
): Promise<CalculationResponse> {
  return request<CalculationResponse>(`/calculate/${fileId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
}

export function getResultDownloadUrl(resultId: string): string {
  return `${BASE_URL}/results/${resultId}`;
}

export async function cleanupFile(fileId: string): Promise<void> {
  await request(`/cleanup/${fileId}`, { method: "DELETE" });
}
