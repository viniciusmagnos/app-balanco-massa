from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from ..models.schemas import (
    UploadResponse,
    AnalysisResult,
    CalculationRequest,
    CalculationResponse,
)
from ..services import file_service
from ..services.inference.agent import analyze_dxf
from ..services.calculation_service import calculate

router = APIRouter(prefix="/api")


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload a DXF file."""
    if not file.filename:
        raise HTTPException(400, "No filename provided")

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext == "dwg":
        raise HTTPException(
            400,
            "Apenas arquivos .dxf são aceitos. Exporte como DXF no AutoCAD.",
        )
    if ext != "dxf":
        raise HTTPException(400, "Only .dxf files are accepted")

    file_id, saved_path = await file_service.save_upload(file)

    return UploadResponse(file_id=file_id, filename=file.filename, file_type=ext)


@router.post("/analyze/{file_id}", response_model=AnalysisResult)
async def analyze_file(file_id: str):
    """Run inference agent on uploaded file."""
    dxf_path = file_service.get_dxf_path(file_id)
    if not dxf_path:
        raise HTTPException(404, "File not found or not yet converted")

    try:
        result = analyze_dxf(file_id, str(dxf_path))
    except Exception as e:
        raise HTTPException(500, f"Analysis failed: {e}")

    return result


@router.post("/calculate/{file_id}", response_model=CalculationResponse)
async def calculate_file(file_id: str, params: CalculationRequest):
    """Execute mass balance calculation with confirmed parameters."""
    dxf_path = file_service.get_dxf_path(file_id)
    if not dxf_path:
        raise HTTPException(404, "File not found")

    try:
        result = calculate(file_id, str(dxf_path), params)
    except Exception as e:
        raise HTTPException(500, f"Calculation failed: {e}")

    return result


@router.get("/results/{result_id}")
async def download_result(result_id: str):
    """Download generated CSV."""
    csv_path = file_service.get_result_path(result_id)
    if not csv_path:
        raise HTTPException(404, "Result not found")

    return FileResponse(
        path=str(csv_path),
        media_type="text/csv",
        filename=f"balanco_massa_{result_id}.csv",
    )


@router.delete("/cleanup/{file_id}")
async def cleanup_file(file_id: str):
    """Clean up temporary files."""
    file_service.cleanup(file_id)
    return {"status": "ok"}
