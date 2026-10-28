from pathlib import Path

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.workbook.workbook import Workbook as WorkbookType


SUPPORTED_EXTENSIONS = {
    ".xlsx",
    ".xlsm",
    ".csv",
    ".tsv",
}

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


def validate_file(file_path: str | Path) -> Path:
    """
    Validate a spreadsheet file before processing.
    """

    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file format: {path.suffix}"
        )

    if path.stat().st_size > MAX_FILE_SIZE:
        raise ValueError(
            "File exceeds the 20 MB upload limit."
        )

    return path


def create_workbook(
    sheet_name: str = "Sheet1",
) -> WorkbookType:
    """
    Create a new Excel workbook.
    """

    workbook = Workbook()

    worksheet = workbook.active
    worksheet.title = sheet_name

    return workbook


def load_spreadsheet(
    file_path: str | Path,
) -> WorkbookType:
    """
    Load an Excel, CSV, or TSV file.

    CSV and TSV files are converted into
    an in-memory Excel workbook.
    """

    path = validate_file(file_path)

    extension = path.suffix.lower()

    if extension in {".xlsx", ".xlsm"}:

        workbook = load_workbook(
            filename=path,
            keep_vba=(extension == ".xlsm"),
            data_only=False,
        )

        return workbook

    separator = "," if extension == ".csv" else "\t"

    dataframe = pd.read_csv(
        path,
        sep=separator,
    )

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Data"

    worksheet.append(
        dataframe.columns.tolist()
    )

    for row in dataframe.itertuples(
        index=False,
        name=None,
    ):
        worksheet.append([
            None if pd.isna(value) else value
            for value in row
        ])

    return workbook


def get_workbook_info(
    workbook: WorkbookType,
) -> dict:
    """
    Return workbook metadata.
    """

    sheets = []

    for worksheet in workbook.worksheets:

        sheets.append({
            "name": worksheet.title,
            "rows": worksheet.max_row,
            "columns": worksheet.max_column,
        })

    return {
        "sheet_count": len(workbook.sheetnames),
        "sheet_names": workbook.sheetnames,
        "sheets": sheets,
    }


def save_workbook(
    workbook: WorkbookType,
    output_path: str | Path,
) -> Path:
    """
    Save a workbook to an Excel file.
    """

    path = Path(output_path)

    if path.suffix.lower() not in {".xlsx", ".xlsm"}:
        raise ValueError(
            "Output must be an .xlsx or .xlsm file."
        )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    workbook.save(path)

    return path