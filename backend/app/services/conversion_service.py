import subprocess
import shutil
import tempfile
from pathlib import Path

from ..config import settings


def convert_dwg_to_dxf(dwg_path: Path, file_id: str) -> Path:
    """Convert a single DWG file to DXF using ODA File Converter.

    ODA requires input/output directories, so we use temp dirs
    and move the result to our converted dir.
    """
    oda = settings.oda_converter_path
    settings.converted_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp_in, tempfile.TemporaryDirectory() as tmp_out:
        # Copy DWG to temp input dir
        tmp_dwg = Path(tmp_in) / dwg_path.name
        shutil.copy2(dwg_path, tmp_dwg)

        subprocess.run(
            [oda, tmp_in, tmp_out, "ACAD2013", "DXF", "0", "1"],
            check=True,
            timeout=120,
        )

        # Find the converted DXF
        converted_files = list(Path(tmp_out).glob("*.dxf"))
        if not converted_files:
            raise RuntimeError(f"ODA conversion produced no DXF output for {dwg_path.name}")

        dest = settings.converted_dir / f"{file_id}.dxf"
        shutil.move(str(converted_files[0]), str(dest))

    return dest
