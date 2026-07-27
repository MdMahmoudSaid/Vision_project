"""spec FR-023: a Guard-role JWT (issued by the local PC, per Feature
001/002's own token scheme) must be rejected by every dashboard-only
endpoint. Guard accounts never receive a cloud_users row at all — the cloud
backend still recognizes the role string solely so it can reject it."""

import pytest
from fastapi.testclient import TestClient

from cloud_attendance.auth.tokens import create_access_token

GUARD_TOKEN = create_access_token(subject="local-guard-1", role="guard")
GUARD_HEADERS = {"Authorization": f"Bearer {GUARD_TOKEN}"}


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/employees"),
        ("get", "/employees/some-id/attendance"),
        ("get", "/attendance/corrections/some-id"),
        ("post", "/attendance/corrections"),
        ("get", "/reports/daily?date=2026-07-27"),
        ("get", "/reports/weekly?week_start=2026-07-27"),
        ("get", "/reports/monthly?month=2026-07"),
        ("get", "/reports/custom?date_from=2026-07-01&date_to=2026-07-27"),
        ("get", "/users"),
        ("post", "/users"),
        ("patch", "/users/some-id"),
    ],
)
def test_guard_role_rejected_on_every_dashboard_endpoint(client: TestClient, method: str, path: str):
    kwargs = {"headers": GUARD_HEADERS}
    if method != "get":
        kwargs["json"] = {}
    response = getattr(client, method)(path, **kwargs)
    assert response.status_code == 403
    assert response.json()["error"] == "forbidden"
