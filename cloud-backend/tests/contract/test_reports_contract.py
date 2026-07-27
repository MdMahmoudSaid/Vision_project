from fastapi.testclient import TestClient

def test_reports_daily_contract(client: TestClient, admin_auth_headers: dict):
    response = client.get(
        "/reports/daily?date=2026-07-27",
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "scope" in data
    assert "period" in data
    assert "rows" in data
    assert "generated_at" in data
    assert "may_be_incomplete" in data

def test_reports_weekly_contract(client: TestClient, admin_auth_headers: dict):
    response = client.get(
        "/reports/weekly?week_start=2026-07-27",
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "period" in data
    assert data["period"]["granularity"] == "week"

def test_reports_monthly_contract(client: TestClient, admin_auth_headers: dict):
    response = client.get(
        "/reports/monthly?month=2026-07",
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "period" in data
    assert data["period"]["granularity"] == "month"

def test_reports_custom_contract(client: TestClient, admin_auth_headers: dict):
    response = client.get(
        "/reports/custom?date_from=2026-07-01&date_to=2026-07-27",
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "period" in data
    assert data["period"]["granularity"] == "custom"
