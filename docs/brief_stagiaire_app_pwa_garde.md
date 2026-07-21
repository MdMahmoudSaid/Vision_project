# Cahier des charges — Mission
## Application PWA du garde (système de pointage par reconnaissance faciale)

**Destinataire** : stagiaire (niveau master, frontend)
**Encadrant** : toi (lead du projet)
**Dépôt** : GitHub, squelette du projet déjà en place (Vite + React + plugin PWA) — tu pars sur cette base, pas de zéro

---

## 1. Contexte en une minute

L'entreprise a une caméra fixe reliée à un PC local. Ce PC local fait tout le travail difficile (reconnaissance faciale, base de données). Ta mission ne touche pas à ça — tu construis uniquement l'**application que le garde utilise sur son téléphone** pour piloter le système : choisir un employé, dire s'il arrive ou repart, déclencher la vérification, et voir le résultat.

Le PC local n'est pas encore prêt pendant que tu travailles. Tu vas donc construire contre une **API simulée (mock)** qui respecte exactement le contrat ci-dessous (§4). Le jour où le vrai backend sera prêt, il suffira de changer une adresse — pas de réécrire ton code.

---

## 2. Règle d'or : la simplicité avant tout

L'utilisateur final de cette app est un garde de sécurité qui peut être peu à l'aise avec les applications numériques. Chaque écran doit respecter :

- **Gros boutons**, faciles à toucher, espacés (pas de petits liens texte pour les actions importantes)
- **Peu de texte**, pas de jargon technique — des mots simples et directs
- **2-3 actions maximum par écran**, jamais plus
- **Retour visuel immédiat et sans ambiguïté** : vert = succès, rouge = échec, une icône claire (✓/✗), pas de messages d'erreur techniques ("Error 500")
- Le flux principal (pointer un employé) doit se faire en **3 taps maximum** : choisir l'employé → arrivée/départ → vérifier
- **Aucun écran de configuration ou de paramètres** ne doit être visible pour le garde

Si un écran te semble avoir plus de texte ou plus de choix que nécessaire, simplifie avant de proposer la version finale — c'est le critère le plus important de toute cette mission, plus important que l'esthétique.

---

## 3. Stack technique imposée

| Élément | Choix | Remarque |
|---|---|---|
| Framework | React + Vite (déjà scaffoldé) | Ne pas changer de framework |
| PWA | `vite-plugin-pwa` (déjà configuré) | Manifest et service worker déjà en place, tu n'as pas à y toucher |
| Langage | TypeScript | Type les réponses API selon le contrat §4 |
| Style | Tailwind CSS | Privilégie des composants réutilisables (bouton, carte employé, bannière résultat) plutôt que du CSS dispersé |
| Appels API | `fetch` + un petit hook personnalisé, ou TanStack Query si tu es à l'aise avec | Gère toujours 3 états : chargement / erreur / succès — jamais juste le cas "ça marche" |
| Mock API | **Mock Service Worker (MSW)** | Voir §5 — permet de développer sans backend réel, avec le même code qui marchera plus tard |
| Routing | React Router | Une route par écran (§6) |

Ne pas ajouter d'autre librairie (state manager, UI kit, etc.) sans en parler d'abord — on garde le projet simple à maintenir.

---

## 4. Contrat d'API à respecter (mock)

Toutes les réponses ci-dessous sont ce que ton app doit attendre. Le vrai backend enverra exactement ce format.

### `POST /auth/login`
```json
// Requête
{ "username": "garde1", "password": "••••••" }

// Réponse 200
{ "token": "jwt-exemple", "role": "guard", "full_name": "Ahmed Guard" }

// Réponse 401
{ "detail": "Identifiants invalides" }
```

### `GET /employees?search=...`
```json
// Réponse 200
[
  { "id": 1, "full_name": "Ahmed Mohamed", "employee_number": "EMP-001", "active": true },
  { "id": 2, "full_name": "Fatima Sy", "employee_number": "EMP-002", "active": true }
]
```

### `POST /employees` (créer un employé)
```json
// Requête
{ "full_name": "Nouvel Employé", "employee_number": "EMP-045" }

// Réponse 201
{ "id": 45, "full_name": "Nouvel Employé", "employee_number": "EMP-045", "active": true }
```

### `POST /employees/{id}/capture-face` (déclenche la capture sur la caméra fixe)
```json
// Réponse 200 (succès)
{ "status": "success", "message": "3 photos capturées et enregistrées" }

// Réponse 200 (échec)
{ "status": "failed", "message": "Aucun visage détecté, réessayez" }
```

### `POST /attendance/verify`
```json
// Requête
{ "employee_id": 12, "type": "arrival" }

// Réponse 200 (succès)
{ "result": "success", "employee_name": "Ahmed Mohamed", "timestamp": "2026-07-17T08:04:00", "type": "arrival" }

// Réponse 200 (échec)
{ "result": "failed", "message": "Visage non reconnu, réessayez" }
```

**Important** : dans le mock, fais varier les réponses (parfois succès, parfois échec) pour que tu testes vraiment les deux cas à l'écran — pas seulement le cas où tout marche.

---

## 5. Mettre en place le mock (avant de commencer les écrans)

1. Installer Mock Service Worker : `npm install msw --save-dev`
2. Créer les handlers qui répondent aux 5 endpoints du §4 avec les exemples JSON donnés
3. Démarrer le mock en mode développement uniquement (jamais en production)
4. Vérifier que tu peux appeler chaque endpoint depuis le navigateur (ex. via un test rapide) avant de construire les écrans dessus

Tant que ce n'est pas fait, ne commence pas les écrans — c'est la fondation de toute ta mission.

---

## 6. Écrans à réaliser, dans l'ordre

### Étape 1 — Écran de connexion (`/login`)
- Champ nom d'utilisateur, champ mot de passe, un seul gros bouton "Se connecter"
- Si erreur : message simple sous le formulaire ("Identifiants incorrects"), pas de jargon
- Tient sur un seul écran mobile, sans défilement
- **Terminé quand** : connexion réussie redirige vers l'écran 2, connexion échouée affiche le message d'erreur

### Étape 2 — Sélection de l'employé (`/`)
- Barre de recherche en haut (filtre par nom ou numéro, sur `GET /employees?search=`)
- Liste des employés sous forme de grandes cartes tactiles (nom + numéro, pas besoin de photo pour le MVP)
- Bouton bien visible "+ Ajouter un employé" (mène à l'étape 4)
- Taper sur un employé mène à l'étape 3
- **Terminé quand** : la recherche filtre en temps réel, la liste est facile à toucher sur mobile

### Étape 3 — Choix Arrivée / Départ (`/employee/:id`)
- Nom de l'employé affiché en grand en haut
- Deux gros boutons : "Arrivée" et "Départ" (couleurs distinctes)
- Bouton retour vers la liste
- Le tap sur un bouton lance directement la vérification (étape suivante), pas un écran de confirmation intermédiaire — on reste dans les 3 taps max
- **Terminé quand** : le choix envoie bien `{ employee_id, type }` à `/attendance/verify`

### Étape 4 — Résultat de la vérification
- Pendant l'appel réseau : indicateur de chargement simple ("Vérification en cours...")
- Résultat succès : grande icône ✓ verte, nom de l'employé, heure, "Arrivée enregistrée" ou "Départ enregistré", bouton "Terminé" qui revient à la liste
- Résultat échec : grande icône ✗ rouge, "Visage non reconnu, réessayez", deux boutons : "Réessayer" et "Annuler"
- **Terminé quand** : les deux cas (succès/échec) s'affichent correctement selon la réponse mock

### Étape 5 — Ajout d'un nouvel employé (`/employee/new`)
- Champ "Nom complet" (obligatoire), champ "Numéro employé" (optionnel)
- Bouton "Enregistrer et capturer le visage"
- Après la création (`POST /employees`), enchaîner automatiquement sur `POST /employees/{id}/capture-face` avec un écran d'attente : "Dites à l'employé de regarder la caméra fixe..."
- Résultat : succès ("✓ Employé ajouté") ou échec ("✗ Capture échouée, réessayer" avec bouton pour relancer juste la capture, pas besoin de resaisir le nom)
- **Terminé quand** : le flux complet (création → capture → confirmation) fonctionne dans les deux cas

---

## 7. Ce que tu ne dois PAS faire

- Ne décide jamais toi-même une règle métier (ex. bloquer un double pointage, valider un seuil de correspondance faciale) — si un écran semble en avoir besoin, demande-moi, ne l'invente pas
- Ne modifie pas le contrat d'API du §4 sans en discuter avec moi d'abord
- N'ajoute pas de nouvelle dépendance (librairie UI, state manager, etc.) sans validation
- Ne mets pas de données codées en dur dans les composants — tout doit passer par la couche mock/API, même pendant les tests
- Ne touche pas à la config du service worker / manifest PWA — c'est déjà en place

---

## 8. Workflow Git

1. Une branche par étape, nommée `feat/login-screen`, `feat/employee-list`, etc.
2. Une Pull Request par branche, quand l'étape est "terminée" selon les critères ci-dessus
3. Avant d'ouvrir la PR, vérifie toi-même :
   - Ça marche en cas de succès **et** en cas d'échec (pas juste le chemin heureux)
   - Aucun texte technique visible à l'écran (pas de "undefined", pas de code d'erreur brut)
   - Les boutons sont assez grands pour être touchés facilement sur téléphone
4. Je relis chaque PR avant de merger — n'enchaîne pas sur l'étape suivante avant mon retour sur la précédente, pour éviter de reconstruire deux fois si quelque chose doit changer

---

## 9. Ordre de travail résumé

1. Setup du mock (§5) — rien d'autre avant que ce soit fait
2. Écran de connexion
3. Écran de sélection employé
4. Écran ajout d'un nouvel employé
5. Écran choix arrivée/départ + écran de résultat
6. Petite relecture toi-même de l'ensemble du flux (les 3 taps du garde, de bout en bout)
7. Ouverture de la PR finale, ou une PR par étape si tu préfères itérer au fur et à mesure (recommandé — plus facile à relire)

En cas de doute sur n'importe quel point (design, contrat d'API, règle d'un écran), pose la question avant de deviner — c'est plus rapide que de refaire.
