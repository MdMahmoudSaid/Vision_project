from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from cloud_attendance.models import SyncedEmployee


def test_report_pdf_export_html_contents(client: TestClient, db_session: Session, admin_auth_headers: dict):
    # Setup employee
    emp = SyncedEmployee(
        id="emp-pdf-1",
        full_name="PDF User",
        employee_number="P001",
        active=True,
    )
    db_session.add(emp)
    db_session.commit()

    with patch("weasyprint.HTML") as mock_html_class:
        mock_html_instance = mock_html_class.return_value
        mock_html_instance.write_pdf.return_value = b"%PDF-1.4 mock pdf data"

        response = client.get(
            "/reports/export?type=daily&date=2026-07-27&format=pdf",
            headers=admin_auth_headers
        )

        assert response.status_code == 200
        assert response.content == b"%PDF-1.4 mock pdf data"

        # Verify WeasyPrint was called with HTML containing the right elements
        mock_html_class.assert_called_once()
        html_string = mock_html_class.call_args[1]["string"]

        assert "Pointage Facial Inc." in html_string # Company name
        assert "2026-07-27" in html_string # Period / Date
        assert "PDF User" in html_string # Employee in table
        assert "Aucun enregistrement" in html_string # Missing record note
        assert "Généré le :" in html_string # Generation date
        assert "Visa" in html_string # Signature area
