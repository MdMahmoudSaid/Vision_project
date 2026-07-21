# Pointage Garde PWA

This is the frontend PWA for the Local Attendance System (Feature 002).

## Architecture
- React 18 + Vite
- React Router for navigation
- Mock Service Worker (MSW) for testing
- Vitest + React Testing Library

## Setup
```bash
npm install
```

## Development
```bash
npm run dev
```

## Tests
```bash
npm run test
```

## Deployment / Static Serving
This PWA is designed to be built (`npm run build`) and then served statically by the Feature 001 FastAPI backend. 
The backend automatically mounts the `frontend/dist` directory at its root `/` URL if it exists.

To run against the real backend:
1. Start the FastAPI backend on port 8000.
2. Build this frontend: `npm run build`.
3. Open `http://localhost:8000` to access the PWA served by the backend.
