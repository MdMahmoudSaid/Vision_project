# Alertes françaises spécifiques pour le pointage et l'enrôlement facial

## Contexte

Le flux de pointage (`AttendancePage.tsx`) et d'enrôlement facial
(`FaceEnrollmentPage.tsx`, `EmployeeManagementPage.tsx`) affichent déjà
certains messages français distincts ("Aucun visage détecté", "Visage non
authentifié") via `describeError()` dans `frontend/src/api/client.ts`. Mais
plusieurs cas retombent sur le message brut renvoyé par le backend (en
anglais) :

- Le visage capturé ne correspond pas à l'employé sélectionné pendant le
  pointage (résultat backend `"failed"`, cause `face_mismatch` — une réponse
  200, pas une exception, donc elle ne passe pas par `describeError`).
- Caméra indisponible (`capture_unusable`), employé inactif
  (`employee_inactive`), aucune référence faciale enregistrée
  (`missing_reference`), employé introuvable (`employee_not_found`),
  matricule déjà utilisé (`duplicate_employee_number`), données invalides
  (`invalid_employee_data`).

## Objectif

Chaque cas d'échec du pointage ou de la création/enrôlement d'un employé
affiche un message français spécifique à sa cause, pas un message générique
ni un texte en anglais.

## Portée

Frontend uniquement (`frontend/src/`). Aucun changement backend : tous les
codes d'erreur nécessaires existent déjà dans les réponses API.

## Conception

### 1. `frontend/src/api/client.ts` — `describeError()`

Étendre la table de correspondance code d'erreur → affichage pour couvrir
tous les codes atteignables depuis le pointage et la création d'employé :

| Code backend | Type de bannière | Titre | Message |
|---|---|---|---|
| `spoof_detected` | `spoof` | *(inchangé)* | *(inchangé)* |
| `face_not_detected` / `no_face_detected` | `no-face` | *(inchangé)* | *(inchangé)* |
| `capture_unusable` | `failure` | "Caméra indisponible" | "La caméra n'a pas pu capturer une image utilisable. Vérifiez le branchement et l'éclairage, puis réessayez." |
| `employee_inactive` | `failure` | "Employé inactif" | "Cet employé est marqué comme inactif et ne peut pas pointer." |
| `missing_reference` | `failure` | "Visage non enregistré" | "Aucun visage de référence n'est enregistré pour cet employé. Enrôlez-le d'abord." |
| `employee_not_found` | `failure` | "Employé introuvable" | "Cet employé n'existe pas ou a été supprimé." |
| `duplicate_employee_number` | `failure` | "Matricule déjà utilisé" | "Ce matricule est déjà attribué à un autre employé." |
| `invalid_employee_data` | `failure` | "Données invalides" | "Le nom complet ne peut pas être vide." |

Les cas non listés ci-dessus (ex. `employee_has_history`) gardent leur
gestion actuelle, indépendante de `describeError`.

### 2. `frontend/src/components/ResultBanner.tsx` — nouveau type `wrong-face`

Ajouter `'wrong-face'` à l'union `ResultType` et son icône dans `ICONS`
(ex. `⊘`), pour distinguer visuellement "visage différent" de l'échec
générique.

### 3. `frontend/src/styles/tokens.css`

Ajouter un bloc `.gate-result--wrong-face` suivant le même patron que
`.gate-result--spoof` (couleur `--stop`, même structure).

### 4. `frontend/src/pages/AttendancePage.tsx`

Le cas `res.result === 'failed'` (uniquement atteignable pour un
`face_mismatch`, les autres causes d'échec étant déjà interceptées en 400
par le backend avant ce point) devient :

```
setResult({
  type: 'wrong-face',
  title: 'Visage non reconnu',
  message: `Le visage détecté ne correspond pas à celui de ${employeeName}. Vérifiez l'identité de la personne et réessayez.`
});
```

Ajouter `'wrong-face'` à la liste des types qui affichent le bouton
"Réessayer".

### 5. `FaceEnrollmentPage.tsx` / `EmployeeManagementPage.tsx`

Aucun changement de code : ces pages utilisent déjà `describeError()`, donc
elles héritent automatiquement des nouveaux messages français dès que (1)
est en place.

## Tests

- Tests unitaires/intégration existants du frontend (`frontend/tests/`) ne
  doivent pas régresser.
- Vérification manuelle via l'app en dev : simuler chaque code d'erreur
  (mock API ou backend local) et confirmer le message affiché.

## Hors périmètre

- Pas de changement des codes d'erreur ou messages backend.
- Pas de nouvelle icône/couleur pour les cas secondaires (caméra, employé
  inactif, référence manquante, etc.) — ils réutilisent la bannière
  d'échec générique avec un texte spécifique.
