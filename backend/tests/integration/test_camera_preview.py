def test_camera_preview_returns_jpeg_for_guard(client, guard_auth_headers):
    response = client.get("/attendance/camera-preview", headers=guard_auth_headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert response.content == b"fake-jpeg-bytes"


def test_camera_preview_returns_jpeg_for_admin(client, admin_auth_headers):
    response = client.get("/attendance/camera-preview", headers=admin_auth_headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"


def test_camera_preview_requires_authentication(client):
    response = client.get("/attendance/camera-preview")
    assert response.status_code == 401


def test_camera_preview_returns_capture_unusable_on_camera_error(client, guard_auth_headers, fake_camera):
    fake_camera.raise_error = True
    response = client.get("/attendance/camera-preview", headers=guard_auth_headers)
    assert response.status_code == 400
    assert response.json()["error"] == "capture_unusable"
