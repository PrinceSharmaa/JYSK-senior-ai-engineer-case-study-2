from io import BytesIO

from openpyxl import load_workbook
from openpyxl.workbook.workbook import Workbook


def clone_workbook(workbook: Workbook) -> Workbook:
    """
    Create an independent workbook copy using an
    in-memory Excel file.
    """

    buffer = BytesIO()

    workbook.save(buffer)

    buffer.seek(0)

    cloned_workbook = load_workbook(
        buffer,
        data_only=False,
    )

    return cloned_workbook


def commit_workbook(
    original: Workbook,
    modified: Workbook,
) -> None:
    """
    Replace the original workbook's contents after
    successful execution.
    """

    original._sheets = modified._sheets

    for sheet in original._sheets:
        sheet._parent = original

    original.calculation = modified.calculation