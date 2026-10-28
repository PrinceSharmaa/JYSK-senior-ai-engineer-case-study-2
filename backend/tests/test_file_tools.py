import pandas as pd
import pytest

from backend.app.tools.file_tools import (
    create_workbook,
    get_workbook_info,
    load_spreadsheet,
    save_workbook,
    validate_file,
)


def test_create_workbook():

    workbook = create_workbook(
        sheet_name="Sales"
    )

    assert workbook.sheetnames == ["Sales"]


def test_save_and_load_workbook(tmp_path):

    workbook = create_workbook("Sales")

    worksheet = workbook["Sales"]

    worksheet["A1"] = "Product"
    worksheet["B1"] = "Revenue"

    worksheet["A2"] = "Laptop"
    worksheet["B2"] = 1500

    file_path = tmp_path / "sales.xlsx"

    save_workbook(
        workbook,
        file_path,
    )

    loaded = load_spreadsheet(file_path)

    assert loaded["Sales"]["A2"].value == "Laptop"

    assert loaded["Sales"]["B2"].value == 1500


def test_get_workbook_info():

    workbook = create_workbook("Sales")

    worksheet = workbook["Sales"]

    worksheet.append([
        "Product",
        "Revenue",
    ])

    worksheet.append([
        "Laptop",
        1500,
    ])

    info = get_workbook_info(workbook)

    assert info["sheet_count"] == 1

    assert info["sheet_names"] == ["Sales"]

    assert info["sheets"][0]["rows"] == 2

    assert info["sheets"][0]["columns"] == 2


def test_load_csv(tmp_path):

    dataframe = pd.DataFrame({
        "Product": ["Laptop", "Mouse"],
        "Revenue": [1500, 50],
    })

    csv_path = tmp_path / "sales.csv"

    dataframe.to_csv(
        csv_path,
        index=False,
    )

    workbook = load_spreadsheet(csv_path)

    worksheet = workbook["Data"]

    assert worksheet["A1"].value == "Product"

    assert worksheet["A2"].value == "Laptop"

    assert worksheet["B3"].value == 50


def test_load_tsv(tmp_path):

    dataframe = pd.DataFrame({
        "Region": ["North", "South"],
        "Sales": [1000, 2000],
    })

    tsv_path = tmp_path / "sales.tsv"

    dataframe.to_csv(
        tsv_path,
        sep="\t",
        index=False,
    )

    workbook = load_spreadsheet(tsv_path)

    worksheet = workbook["Data"]

    assert worksheet["A2"].value == "North"

    assert worksheet["B3"].value == 2000


def test_validate_missing_file(tmp_path):

    missing_file = tmp_path / "missing.xlsx"

    with pytest.raises(FileNotFoundError):
        validate_file(missing_file)


def test_validate_unsupported_file(tmp_path):

    invalid_file = tmp_path / "malware.exe"

    invalid_file.write_text("invalid")

    with pytest.raises(ValueError):
        validate_file(invalid_file)


def test_invalid_output_extension(tmp_path):

    workbook = create_workbook()

    with pytest.raises(ValueError):
        save_workbook(
            workbook,
            tmp_path / "output.csv",
        )