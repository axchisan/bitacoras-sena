import shutil
from pathlib import Path
from datetime import date
import openpyxl
from openpyxl.styles import Alignment
from app.config import get_settings

settings = get_settings()

TEMPLATE_PATH = Path("/app/templates/bitacora_base.xlsx")
OUTPUT_DIR = Path("/app/output")

# Column mapping in the activity table (based on Bitacora1 analysis)
SHEET_NAME = "Formato Bitácora Individual"
ROW_BITACORA_NUMBER = 11
COL_BITACORA_NUMBER = 2   # Column B
ROW_PERIOD = 11
COL_PERIOD = 5            # Column E
ROW_DELIVERY_DATE = 71
COL_DELIVERY_DATE = 8     # Column H

# Activity table starts at row 47, each activity occupies 2 rows (content + spacer)
ACTIVITIES_START_ROW = 47
ACTIVITY_ROW_STEP = 2

# Column indices for activity table
COL_DESCRIPTION = 2       # B
COL_COMPETENCIAS = 4      # D
COL_START_DATE = 6        # F
COL_END_DATE = 7          # G
COL_EVIDENCE = 8          # H
COL_OBSERVATIONS = 9      # I


def generate_excel(
    bitacora_number: int,
    period_start: date,
    period_end: date,
    activities: list[dict],
    delivery_date: date | None = None,
) -> Path:
    """
    Generates a filled Excel bitácora from the base template.
    Returns the path to the generated file.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"Bitacora{bitacora_number}_DuvanYairArciniegas.xlsx"

    shutil.copy2(TEMPLATE_PATH, output_path)

    wb = openpyxl.load_workbook(str(output_path))
    ws = wb[SHEET_NAME]

    # ── Update header fields ──────────────────────────────────────────────────
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

    # ── Clear existing activity rows (47 onwards until ARL section at ~row 58) ─
    for row_idx in range(ACTIVITIES_START_ROW, 57):
        for col_idx in [COL_DESCRIPTION, COL_COMPETENCIAS, COL_START_DATE,
                        COL_END_DATE, COL_EVIDENCE, COL_OBSERVATIONS]:
            cell = ws.cell(row=row_idx, column=col_idx)
            if cell.value and row_idx >= ACTIVITIES_START_ROW:
                # Only clear cells that were activity content
                pass

    # ── Write activities ──────────────────────────────────────────────────────
    wrap_alignment = Alignment(wrap_text=True, vertical="top")

    for i, activity in enumerate(activities):
        row = ACTIVITIES_START_ROW + (i * ACTIVITY_ROW_STEP)

        # Description (B)
        desc_cell = ws.cell(row=row, column=COL_DESCRIPTION)
        desc_cell.value = f"{activity.get('title', '')}\n{activity.get('description', '')}"
        desc_cell.alignment = wrap_alignment

        # Competencias (D)
        comp_cell = ws.cell(row=row, column=COL_COMPETENCIAS)
        comp_cell.value = activity.get("competencias", "")
        comp_cell.alignment = wrap_alignment

        # Start date (F)
        if activity.get("start_date"):
            start = activity["start_date"]
            if isinstance(start, str):
                from datetime import datetime as dt
                start = dt.strptime(start, "%Y-%m-%d").date()
            ws.cell(row=row, column=COL_START_DATE).value = start.strftime("%d/%m/%y")

        # End date (G)
        if activity.get("end_date"):
            end = activity["end_date"]
            if isinstance(end, str):
                from datetime import datetime as dt
                end = dt.strptime(end, "%Y-%m-%d").date()
            ws.cell(row=row, column=COL_END_DATE).value = end.strftime("%d/%m/%y")

        # Evidence (H)
        ev_cell = ws.cell(row=row, column=COL_EVIDENCE)
        ev_cell.value = activity.get("evidence_description", "")
        ev_cell.alignment = wrap_alignment

        # Observations (I)
        obs_cell = ws.cell(row=row, column=COL_OBSERVATIONS)
        obs_cell.value = activity.get("observations", "")
        obs_cell.alignment = wrap_alignment

    wb.save(str(output_path))
    wb.close()

    return output_path
