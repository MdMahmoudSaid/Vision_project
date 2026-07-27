# Système de pointage par reconnaissance faciale

Système de gestion de présence par reconnaissance faciale : un poste local (PC + webcam) enregistre les pointages des employés en local, une app PWA sert d'interface pour le garde, et une synchronisation en tâche de fond pousse les données vers un dashboard cloud de management (rôles, rapports, corrections, export PDF/Excel).

## Architecture

```
┌──────────────────┐        réseau local (WiFi)        ┌──────────────────┐
│   frontend/      │ ───────────────────────────────▶  │   backend/       │
│   App PWA garde  │ ◀───────────────────────────────  │   FastAPI+SQLite │
│   (React + Vite) │        servie par backend/         │   + webcam/DeepFace│
└──────────────────┘                                    └────────┬─────────┘
                                                                   │ sync (HTTPS,
                                                                   │  quand internet
                                                                   │  disponible)
                                                                   ▼
┌──────────────────┐        HTTPS (API séparée)        ┌──────────────────┐
│ cloud-dashboard/ │ ───────────────────────────────▶  │  cloud-backend/  │
│ Dashboard mgmt   │ ◀───────────────────────────────  │  FastAPI+Postgres│
│ (React + Vite)   │                                    └──────────────────┘
└──────────────────┘
```

- **`backend/`** — Service local (PC du site) : authentification garde/admin, gestion employés, enrôlement facial, vérification de présence (webcam + DeepFace), et une tâche de fond qui pousse les nouveaux enregistrements vers `cloud-backend/`. Fonctionne entièrement **sans internet** — la synchronisation cloud est en plus, jamais bloquante.
- **`frontend/`** — App PWA utilisée par le garde sur son téléphone (même réseau WiFi local que le PC). En production, elle est **servie directement par `backend/`** (pas un déploiement séparé).
- **`cloud-backend/`** — API de management cloud (PostgreSQL en prod) : reçoit la synchronisation depuis un ou plusieurs sites, sert les comptes Owner/Admin/Viewer, les rapports (jour/semaine/mois/période), les corrections manuelles avec audit trail, et l'export PDF/Excel. **Déployée séparément** de `cloud-dashboard/`.
- **`cloud-dashboard/`** — Dashboard web pour les comptes Owner/Admin/Viewer (pas les gardes). Appelle `cloud-backend/` sur une vraie origine HTTP configurable.
- **`docs/`** — Cahier des charges et plan de projet.

## Prérequis

| Outil | Version | Requis pour |
|---|---|---|
| Python | **3.11.x exactement** | `backend/` (contrainte de `deepface`/TensorFlow — une version plus récente échoue à l'installation avec une erreur de résolution de dépendances peu claire) |
| Python | 3.11+ (toute version récente convient) | `cloud-backend/` (pas de dépendance DeepFace/TensorFlow) |
| Node.js | 18+ (testé avec Node 25) | `frontend/`, `cloud-dashboard/` |
| Homebrew (macOS) / apt (Linux) | — | libs système de `backend/` et `cloud-backend/`, voir plus bas |

macOS : `brew install python@3.11` si `python3.11 --version` échoue.

## Démarrage rapide

L'ordre ci-dessous fonctionne de bout en bout sans erreur, y compris pour un premier clone du dépôt.

### 1. `backend/` — service local

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # ajuster LOCAL_ATTENDANCE_JWT_SECRET avant tout déploiement réel
alembic upgrade head
python scripts/create_local_user.py --username admin --password <choisir-un-mdp> --role admin
python scripts/create_local_user.py --username guard --password <choisir-un-mdp> --role guard
uvicorn local_attendance.main:app --reload
```

Sert l'API sur `http://localhost:8000`. `opencv-python` et `deepface` sont nécessaires pour une vraie webcam/reconnaissance faciale (pas pour la suite de tests, qui utilise des doublures). Le premier vrai appel de détection télécharge ~120 Mo de poids de modèles depuis GitHub — connexion internet requise une fois, puis fonctionne hors-ligne.

La détection anti-usurpation (liveness, voir `backend/README.md`) télécharge en plus ~4 Mo de poids `MiniFASNet` au premier vrai usage et nécessite `torch` (déjà dans `pyproject.toml`, installé par `pip install -e ".[dev]"`).

### 2. `frontend/` — app PWA du garde

```bash
cd frontend
npm install
npm run build
```

Une fois buildée (`frontend/dist/`), `backend/` la sert automatiquement à la racine `http://localhost:8000`. Pas de déploiement séparé.

Pour développer avec rechargement à chaud à la place : `npm run dev` (proxy vers `backend/` sur le port 8000, voir `vite.config.ts`).

### 3. `cloud-backend/` — API de management cloud

```bash
cd cloud-backend
python3 -m venv .venv        # toute version Python 3.11+ convient ici
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # ajuster CLOUD_ATTENDANCE_JWT_SECRET
alembic upgrade head
python scripts/create_owner.py owner@example.com <choisir-un-mdp>
uvicorn cloud_attendance.main:app --reload --port 8001
```

Sert l'API sur `http://localhost:8001` (distinct du port 8000 de `backend/` pour pouvoir faire tourner les deux en même temps).

**Export PDF** : nécessite les bibliothèques système Pango/Cairo/GDK-Pixbuf (WeasyPrint), pas seulement un paquet pip :

```bash
brew install pango gdk-pixbuf   # macOS
# Linux : apt-get install libpango-1.0-0 libpangocairo-1.0-0 libcairo2 libgdk-pixbuf2.0-0
```

Sans ces bibliothèques, `import weasyprint` échoue avec une `OSError` au moment de l'export — l'export Excel (`openpyxl`) n'a lui aucune dépendance système et fonctionne toujours. Le `Dockerfile` de `cloud-backend/` installe déjà ces libs pour la production.

### 4. `cloud-dashboard/` — dashboard cloud

```bash
cd cloud-dashboard
npm install
npm run dev
```

Sert le dashboard sur `http://localhost:5173` par défaut (Vite), avec un proxy dev vers `cloud-backend/` sur le port 8001 (voir `vite.config.ts` — `cloud-backend/` doit tourner en parallèle).

Pour un build de production : `npm run build`, puis servir `dist/` comme un site statique séparé, avec `VITE_API_BASE_URL` pointant vers l'origine réelle de `cloud-backend/` (voir `.env.example` — contrairement à `frontend/`, ce n'est **pas** co-hébergé avec son backend).

### Relier `backend/` à `cloud-backend/` (synchronisation)

Les deux services s'authentifient via une clé d'API partagée (pas un JWT utilisateur) — à faire correspondre :

```bash
# backend/.env
LOCAL_ATTENDANCE_SYNC_TARGET_URL=http://localhost:8001
LOCAL_ATTENDANCE_SYNC_API_KEY=une-cle-partagee

# cloud-backend/.env
CLOUD_ATTENDANCE_SYNC_API_KEYS={"default-site": "une-cle-partagee"}
```

## Ports par défaut

| Service | Port | URL |
|---|---|---|
| `backend/` (+ `frontend/` buildé) | 8000 | http://localhost:8000 |
| `cloud-backend/` | 8001 | http://localhost:8001 |
| `cloud-dashboard/` (dev) | 5173 (Vite par défaut) | http://localhost:5173 |
| `frontend/` (dev, optionnel) | 5173, ou le port suivant libre si les deux dev servers tournent en même temps | affiché au démarrage de `npm run dev` |

Ni `frontend/` ni `cloud-dashboard/` ne fixent de port dans leur config Vite ; si les deux serveurs de dev tournent en parallèle, Vite choisit automatiquement le premier port libre à partir de 5173 pour le second — regarder la sortie du terminal pour l'URL réelle.

## Tests

Chaque service a sa propre suite, décrite dans son README :

```bash
cd backend && pytest                 # nécessite le venv Python 3.11 activé
cd cloud-backend && pytest           # nécessite son propre venv activé
cd frontend && npx vitest run
cd cloud-dashboard && npm test       # alias de `vitest run`
```

Aucune suite ne touche à du vrai matériel (webcam) ni à une vraie base PostgreSQL — doublures/mocks partout (voir chaque README pour le détail).

## Comptes par défaut

Il n'existe **aucun endpoint d'inscription publique** sur aucun des deux backends, par choix de conception : tous les comptes sont créés via script (`backend/scripts/create_local_user.py`, `cloud-backend/scripts/create_owner.py`) ou, pour les comptes cloud suivants, invités depuis le dashboard par un compte Owner déjà existant.

## Dépannage

- **`backend/` : `pip install` échoue avec une erreur de résolution de dépendances** → mauvaise version de Python. Vérifier `python3.11 --version` avant de créer le venv.
- **`backend/` : `sqlite3.OperationalError: no such column ...`** → une migration Alembic n'a pas été appliquée sur la base réelle. Relancer `alembic upgrade head` dans `backend/` (avec le venv activé) avant de redémarrer `uvicorn`.
- **Export PDF téléchargé mais illisible/corrompu** → bibliothèques système WeasyPrint manquantes, voir section `cloud-backend/` ci-dessus.
- **Le dashboard cloud n'affiche pas le lien "Utilisateurs"** → seul un compte de rôle `owner` le voit ; un compte `admin` ne l'a pas. Recréer un compte via `create_owner.py` si besoin.
- **`cloud-dashboard/` : erreurs `ECONNREFUSED` en dev** → `cloud-backend/` doit tourner sur le port 8001 en parallèle (le proxy Vite ne démarre pas de serveur, il relaie seulement).

## Autre

Ce dépôt contient uniquement le code nécessaire pour faire tourner et développer le projet (`backend/`, `frontend/`, `cloud-backend/`, `cloud-dashboard/`, `docs/`). Les artefacts de planification (specs, plans, tâches) et les outils d'assistance IA utilisés pendant le développement existent en local sur les postes de l'équipe mais ne sont pas publiés dans ce dépôt.
