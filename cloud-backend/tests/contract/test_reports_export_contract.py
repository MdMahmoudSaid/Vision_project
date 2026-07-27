from fastapi.testclient import TestClient

def test_reports_export_pdf_contract(client: TestClient, admin_auth_headers: dict):
    response = client.get(
        "/reports/export?type=daily&date=2026-07-27&format=pdf",
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"

def test_reports_export_excel_contract(client: TestClient, admin_auth_headers: dict):
    response = client.get(
        "/reports/export?type=monthly&month=2026-07&format=xlsx",
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
