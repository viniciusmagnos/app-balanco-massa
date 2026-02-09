import uuid
import shutil
from pathlib import Path

from fastapi import UploadFile

from ..config import settings


def _ensure_dirs():
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.converted_dir.mkdir(parents=True, exist_ok=True)
    settings.results_dir.mkdir(parents=True, exist_ok=True)


async def save_upload(file: UploadFile) -> tuple[str, Path]:
    """Save uploaded file, return (file_id, saved_path)."""
    _ensure_dirs()
    file_id = uuid.uuid4().hex[:12]
    suffix = Path(file.filename).suffix.lower()
    dest = settings.upload_dir / f"{file_id}{suffix}"
    with open(dest, "wb") as f:
        content = await file.read()
        f.write(content)
    return file_id, dest


def get_upload_path(file_id: str) -> Path | None:
    """Find the uploaded file by file_id."""
    for ext in (".dwg", ".dxf"):
        p = settings.upload_dir / f"{file_id}{ext}"
        if p.exists():
            return p
    return None


def get_dxf_path(file_id: str) -> Path | None:
    """Get the DXF path (original or converted)."""
    # Check if original upload is DXF
    dxf_upload = settings.upload_dir / f"{file_id}.dxf"
    if dxf_upload.exists():
        return dxf_upload
    # Check converted directory
    dxf_converted = settings.converted_dir / f"{file_id}.dxf"
    if dxf_converted.exists():
        return dxf_converted
    return None


def get_result_path(result_id: str) -> Path | None:
    p = settings.results_dir / f"{result_id}.csv"
    return p if p.exists() else None


def cleanup(file_id: str, result_id: str | None = None):
    """Remove all files associated with a file_id (and optionally a result_id)."""
    for ext in (".dwg", ".dxf"):
        p = settings.upload_dir / f"{file_id}{ext}"
        if p.exists():
            p.unlink()
    dxf_conv = settings.converted_dir / f"{file_id}.dxf"
    if dxf_conv.exists():
        dxf_conv.unlink()
    if result_id:
        csv_p = settings.results_dir / f"{result_id}.csv"
        if csv_p.exists():
            csv_p.unlink()


def cleanup_old_files(max_age_hours: int = 24):
    """Remove files older than max_age_hours from all temp directories."""
    import time

    now = time.time()
    cutoff = now - max_age_hours * 3600
    for d in (settings.upload_dir, settings.converted_dir, settings.results_dir):
        if not d.exists():
            continue
        for f in d.iterdir():
            if f.is_file() and f.stat().st_mtime < cutoff:
                f.unlink()
