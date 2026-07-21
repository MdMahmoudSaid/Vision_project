# Contrat API Réel (Feature 002) - v2

Ce document détaille le vrai contrat de l'API backend FastAPI, à utiliser pour le frontend PWA. Tous les IDs sont des chaînes de caractères (UUID).

## `POST /auth/login`

**Requête :**
```json
{
  "username": "garde1",
  "password": "my_password"
}
```

**Réponse 200 (Succès) :**
```json
{
  "access_token": "eyJhbGciOiJIUzI1...",
  "token_type": "bearer",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "username": "garde1",
    "full_name": "Ahmed Guard",
    "role": "guard"
  }
}
```

**Réponse 401 (Échec) :**
```json
{
  "detail": "Incorrect username or password"
}
```

---

## `GET /employees`

**Requête :**
Paramètre de recherche : `?query=Ahmed`

**Réponse 200 :**
```json
[
  {
    "id": "223e4567-e89b-12d3-a456-426614174001",
    "full_name": "Ahmed Mohamed",
    "employee_number": "EMP-001",
    "department": "Security",
    "active": true,
    "has_face_reference": true
  }
]
```

---

## `POST /employees`

**Requête :**
```json
{
  "full_name": "Nouvel Employé",
  "employee_number": "EMP-045"
}
```

**Réponse 201 (Succès) :**
```json
{
  "id": "323e4567-e89b-12d3-a456-426614174002",
  "full_name": "Nouvel Employé",
  "employee_number": "EMP-045",
  "department": null,
  "active": true,
  "has_face_reference": false,
  "job_title": null,
  "phone": null,
  "notes": null,
  "registration_date": "2026-07-20",
  "created_at": "2026-07-20T22:00:00Z",
  "updated_at": "2026-07-20T22:00:00Z"
}
```

---

## `POST /employees/{employee_id}/face` (Enrôlement facial)

**Requête :**
*(Optionnel, par défaut 3 échantillons)*
```json
{
  "sample_count": 3
}
```

**Réponse 200 (Succès) :**
```json
{
  "employee_id": "323e4567-e89b-12d3-a456-426614174002",
  "status": "usable",
  "sample_count": 3,
  "enrolled_at": "2026-07-20T22:05:00Z"
}
```

**Réponse 400 (Échec technique) :**
```json
{
  "detail": {
    "error": "capture_unusable",
    "message": "Camera could not capture a usable frame"
  }
}
```

---

## `POST /attendance/verify` (Pointage)

**Requête :**
```json
{
  "employee_id": "223e4567-e89b-12d3-a456-426614174001",
  "type": "arrival"
}
```

**Réponse 200 (Succès) :**
```json
{
  "result": "success",
  "message": "Attendance recorded",
  "verification_attempt": {
    "id": "423e4567-e89b-12d3-a456-426614174003",
    "employee_id": "223e4567-e89b-12d3-a456-426614174001",
    "guard_id": "123e4567-e89b-12d3-a456-426614174000",
    "type_requested": "arrival",
    "timestamp": "2026-07-20T22:10:00Z",
    "result": "success",
    "similarity_score": 0.95,
    "failure_reason": null,
    "attendance_event_id": "523e4567-e89b-12d3-a456-426614174004"
  },
  "attendance_event": {
    "id": "523e4567-e89b-12d3-a456-426614174004",
    "employee_id": "223e4567-e89b-12d3-a456-426614174001",
    "guard_id": "123e4567-e89b-12d3-a456-426614174000",
    "type": "arrival",
    "timestamp": "2026-07-20T22:10:00Z",
    "verification_attempt_id": "423e4567-e89b-12d3-a456-426614174003",
    "source": "auto"
  }
}
```

**Réponse 200 (Échec de correspondance - Visage différent de l'employé attendu) :**
```json
{
  "result": "failed",
  "message": "Face verification failed",
  "verification_attempt": {
    "id": "623e4567-e89b-12d3-a456-426614174005",
    "employee_id": "223e4567-e89b-12d3-a456-426614174001",
    "guard_id": "123e4567-e89b-12d3-a456-426614174000",
    "type_requested": "arrival",
    "timestamp": "2026-07-20T22:15:00Z",
    "result": "failed",
    "similarity_score": 0.40,
    "failure_reason": "face_mismatch",
    "attendance_event_id": null
  },
  "attendance_event": null
}
```

**Réponse 400 (Échec technique - Caméra ou aucun visage détecté) :**
```json
{
  "detail": {
    "error": "face_not_detected",
    "message": "No usable face detected in the capture"
  }
}
```

---

## `GET /attendance/shift-activity`

**Requête :**
*(Aucun paramètre obligatoire)*

**Réponse 200 :**
```json
[
  {
    "kind": "attendance",
    "employee_id": "223e4567-e89b-12d3-a456-426614174001",
    "employee_name": "Ahmed Mohamed",
    "type": "arrival",
    "timestamp": "2026-07-20T22:10:00Z",
    "guard_username": "garde1",
    "outcome": "success",
    "failure_reason": null,
    "attendance_event_id": "523e4567-e89b-12d3-a456-426614174004"
  }
]
```
