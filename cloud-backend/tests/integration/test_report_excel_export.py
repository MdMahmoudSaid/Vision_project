import io
from openpyxl import load_workbook
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from cloud_attendance.models import SyncedEmployee


def test_report_excel_export(client: TestClient, db_session: Session, admin_auth_headers: dict):
    # Setup employee
    emp = SyncedEmployee(
        id="emp-excel-1",
        full_name="Excel User",
        employee_number="E001",
        active=True,
    )
    db_session.add(emp)
    db_session.commit()

    response = client.get(
        "/reports/export?type=daily&date=2026-07-27&format=xlsx",
        headers=admin_auth_headers
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    # Load the workbook from response content
    wb = load_workbook(filename=io.BytesIO(response.content))
    ws = wb.active

    assert ws.title == "Rapport de Présence"

    # Read rows
    rows = list(ws.values)
    
    # Header should be in row 6 (index 5)
    # Rows 1-3 are title/meta info, row 4 is empty, row 5 is headers, row 6 starts data.
    header_row_idx = -1
    for i, row in enumerate(rows):
        if "Employé ID" in row:
            header_row_idx = i
            break
            
    assert header_row_idx != -1
    headers = rows[header_row_idx]
    assert "Employé ID" in headers
    assert "Nom" in headers
    
    # The first data row should be right after
    data_row = rows[header_row_idx + 1]
    assert data_row[0] == "emp-excel-1"
    assert data_row[1] == "Excel User"
    assert data_row[2] == "2026-07-27"
    assert data_row[6] == "no_record"
