import re
import shutil
import zipfile
from pathlib import Path
from datetime import date
import openpyxl
from openpyxl.styles import Alignment
from app.config import get_settings

settings = get_settings()

TEMPLATE_PATH = Path("/app/templates/bitacora_base.xlsx")
OUTPUT_DIR = Path("/app/output")
_CLEAN_TEMPLATE: Path | None = None  # cached cleaned template

SHEET_NAME = "Formato Bitácora Individual"
ROW_BITACORA_NUMBER = 11
COL_BITACORA_NUMBER = 2
ROW_PERIOD = 11
COL_PERIOD = 5
ROW_DELIVERY_DATE = 71
COL_DELIVERY_DATE = 8

ACTIVITIES_START_ROW = 47
ACTIVITY_ROW_STEP = 2

COL_DESCRIPTION = 2
COL_COMPETENCIAS = 4
COL_START_DATE = 6
COL_END_DATE = 7
COL_EVIDENCE = 8
COL_OBSERVATIONS = 9


def _strip_drawings(src: Path, dst: Path) -> None:
    """
    Copy xlsx stripping DrawingML and DataValidation elements that cause
    openpyxl to hang. xlsx is a zip — we manipulate the XML directly.
    """
    with zipfile.ZipFile(src, "r") as zin, \
         zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:

        for item in zin.infolist():
            # Skip drawing binary files entirely
            if "drawings/" in item.filename and item.filename != "xl/drawings/":
                continue

            data = zin.read(item.filename)

            # Strip <drawing .../> and <dataValidations ...> from worksheet XML
            if item.filename.startswith("xl/worksheets/") and item.filename.endswith(".xml"):
                txt = data.decode("utf-8", errors="replace")
                txt = re.sub(r"<drawing[^/]*/?>", "", txt)
                txt = re.sub(r"<drawing[^>]*>.*?</drawing>", "", txt, flags=re.DOTALL)
                txt = re.sub(r"<dataValidations[^>]*>.*?</dataValidations>", "", txt, flags=re.DOTALL)
                data = txt.encode("utf-8")

            # Remove drawing Override entries from [Content_Types].xml
            elif item.filename == "[Content_Types].xml":
                txt = data.decode("utf-8", errors="replace")
                txt = re.sub(r'<Override[^>]*[Dd]rawing[^>]*/>', "", txt)
                data = txt.encode("utf-8")

            # Remove drawing Relationship entries from .rels files
            elif item.filename.endswith(".rels"):
                txt = data.decode("utf-8", errors="replace")
                txt = re.sub(r'<Relationship[^>]*[Dd]rawing[^>]*/>', "", txt)
                data = txt.encode("utf-8")

            zout.writestr(item, data)


def _get_clean_template() -> Path:
    """Return a cached drawing-free copy of the template."""
    global _CLEAN_TEMPLATE
    if _CLEAN_TEMPLATE and _CLEAN_TEMPLATE.exists():
        return _CLEAN_TEMPLATE

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    clean = OUTPUT_DIR / "_bitacora_template_clean.xlsx"
    _strip_drawings(TEMPLATE_PATH, clean)
    _CLEAN_TEMPLATE = clean
    return clean


def generate_excel(
    bitacora_number: int,
    period_start: date,
    period_end: date,
    activities: list[dict],
    delivery_date: date | None = None,
) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"Bitacora{bitacora_number}_DuvanYairArciniegas.xlsx"

    clean_template = _get_clean_template()
    shutil.copy2(clean_template, output_path)

    wb = openpyxl.load_workbook(str(output_path))
    ws = wb[SHEET_NAME]

    ws.cell(row=ROW_BITACORA_NUMBER, column=COL_BITACORA_NUMBER).value = str(bitacora_number)

    period_label = (
        f"Desde {period_start.strftime('%d/%m/%Y')} "
        f"hasta {period_end.strftime('%d/%m/%Y')}"
    )
    ws.cell(row=ROW_PERIOD, column=COL_PERIOD).value = period_label

    if delivery_date:
        ws.cell(row=ROW_DELIVERY_DATE, column=COL_DELIVERY_DATE).value = (
            delivery_date.strftime("%d/%m/%Y")
        )

    wrap_alignment = Alignment(wrap_text=True, vertical="top")

    for i, activity in enumerate(activities):
        row = ACTIVITIES_START_ROW + (i * ACTIVITY_ROW_STEP)

        desc_cell = ws.cell(row=row, column=COL_DESCRIPTION)
        desc_cell.value = f"{activity.get('title', '')}\n{activity.get('description', '')}"
        desc_cell.alignment = wrap_alignment

        comp_cell = ws.cell(row=row, column=COL_COMPETENCIAS)
        comp_cell.value = activity.get("competencias", "")
        comp_cell.alignment = wrap_alignment

        if activity.get("start_date"):
            start = activity["start_date"]
            if isinstance(start, str):
                from datetime import datetime as dt
                start = dt.strptime(start, "%Y-%m-%d").date()
            ws.cell(row=row, column=COL_START_DATE).value = start.strftime("%d/%m/%y")

        if activity.get("end_date"):
            end = activity["end_date"]
            if isinstance(end, str):
                from datetime import datetime as dt
                end = dt.strptime(end, "%Y-%m-%d").date()
            ws.cell(row=row, column=COL_END_DATE).value = end.strftime("%d/%m/%y")

        ev_cell = ws.cell(row=row, column=COL_EVIDENCE)
        ev_cell.value = activity.get("evidence_description", "")
        ev_cell.alignment = wrap_alignment

        obs_cell = ws.cell(row=row, column=COL_OBSERVATIONS)
        obs_cell.value = activity.get("observations", "")
        obs_cell.alignment = wrap_alignment

    wb.save(str(output_path))
    wb.close()

    return output_path
