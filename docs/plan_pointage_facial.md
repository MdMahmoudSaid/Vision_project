# Plan final — Système de pointage par reconnaissance faciale (caméra fixe + PC local)

**Statut** : version finale consolidée, réconciliant le cahier de charge client (`Employee Attendance Facial Verification System Report.pdf`) et le draft d'architecture (`plan_final_pointage_facial.md`).
**Architecture confirmée** : caméra fixe dédiée (webcam USB) → PC local (backend + traitement facial) → app PWA du garde (réseau local uniquement) ; synchronisation vers un dashboard cloud de management quand internet est disponible. La caméra dédiée reste par ailleurs une caméra de vidéosurveillance normale, enregistrée par le **NVR/système de surveillance existant du client, indépendant de notre système** (pas d'intégration vidéo à développer — voir §9).
**Équipe** : toi (lead, tâches critiques et logique métier) + 1 stagiaire niveau master (autonome sur le frontend UI, une fois les contrats d'API figés).
**Portée V1** : conforme au §22 du cahier de charge — **rôles/permissions, corrections manuelles avec audit trail, et rapports (jour/semaine/mois/période) avec export PDF/Excel sont inclus en V1**, pas reportés en V2.

---

## 1. Décisions actées lors du cadrage

| Sujet | Décision |
|---|---|
| Type de caméra fixe | **Webcam USB**, branchée directement au PC local. Intégration via OpenCV, accès direct au device — pas de flux RTSP à gérer. |
| Revue des images de sécurité (§8 cahier de charge) | Le client dispose déjà d'un système NVR/vidéosurveillance séparé. Notre système **n'a pas besoin de stocker ni de rejouer de vidéo** — le management consulte ce système existant indépendamment. Notre seule responsabilité : que les enregistrements de pointage soient suffisamment horodatés pour permettre un recoupement manuel avec cette vidéo externe. |
| Scope V1 du dashboard | **Complet**, conforme au cahier de charge : rôles (Owner/Admin/Guard/Viewer), corrections manuelles + audit trail non destructif, rapports jour/semaine/mois/période, export PDF + Excel, impression. Rien n'est repoussé en V2 sur ces points. |

Cette dernière décision change l'estimation par rapport au draft précédent : le dashboard n'est plus "minimal", et l'estimation totale passe de 12-16 jours à **~18-22 jours ouvrés** (voir §8).

### Points encore ouverts (à trancher en Phase 0, avant le code)

- Solution HTTPS locale pour l'app PWA du garde (certificat auto-signé installé une fois sur le téléphone, ou alternative type mkcert/reverse-proxy) — à tester tôt car bloquant pour l'installabilité PWA.
- Hébergement définitif du dashboard cloud (Render/Railway pressenti) et budget associé.
- Format exact attendu pour les rapports imprimés (logo entreprise, mise en page) — le cahier de charge (§16) impose : nom de l'entreprise, nom/numéro employé, période, tableau arrivée/départ, enregistrements manquants, date de génération, zone de signature. À valider avec une maquette avant la Phase 4.
- Règle exacte de blocage des soumissions dupliquées (§18) : proposition par défaut **60 secondes** entre deux vérifications réussies pour le même employé — à valider avec le client, configurable côté admin.
- Schéma de numérotation du `employee_number` auto-généré (ex. séquentiel, préfixé par année) si le client n'entre pas son propre numéro.

---

## 2. Ce qui change par rapport aux hypothèses initiales

| | Ancienne hypothèse | Architecture confirmée |
|---|---|---|
| Capture faciale | Caméra du téléphone du garde, traitement dans le navigateur (`@vladmandic/human`) | Caméra fixe dédiée, connectée à un PC local qui fait le traitement |
| Où tourne la reconnaissance faciale | Dans le navigateur du téléphone (client-side) | Sur le PC local (server-side) — DeepFace, plus simple et plus précis avec du vrai matériel |
| Rôle de l'app PWA du garde | Capture + traitement + stockage offline complet | Interface de contrôle simple : sélectionner l'employé, choisir arrivée/départ, déclencher la vérification, afficher le résultat |
| Connexion nécessaire pour un pointage | Doit marcher 100% hors ligne sur le téléphone (sync complexe) | App du garde → PC local sur le même réseau WiFi local — **pas besoin d'internet pour cette boucle** |
| Rôle d'internet | Central (sync offline complexe côté téléphone) | Secondaire : uniquement pour pousser les données vers le dashboard cloud, en différé |
| Ajout d'un nouvel employé | Capture guidée avec séquence de liveness automatique dans le navigateur | Le garde supervise physiquement : il dit à l'employé de regarder la caméra fixe, éventuellement à gauche/droite ; plusieurs photos sont prises |
| Anti-usurpation | Système automatique avec séquences aléatoires | Supervision humaine directe par le garde = protection naturelle — liveness automatique devient un bonus V2 |
| Revue vidéo en cas de litige | Non spécifié | NVR existant du client, séparé — pas d'intégration vidéo dans notre système |
| Dashboard management | "Minimal" (vue du jour + historique employé) | Complet : rôles, audit trail, rapports + export, conforme au cahier de charge |

**Bonne nouvelle** : cette architecture élimine les deux parties les plus risquées du projet — la reconnaissance faciale dans le navigateur d'un téléphone Android, et la synchronisation offline complexe avec résolution de conflits côté téléphone. Le PC local devient le "cerveau" du système ; le téléphone redevient une simple télécommande.

---

## 3. Flux fonctionnels

### 3.1 Pointage d'un employé existant (§2 cahier de charge)

1. Le garde ouvre l'app sur son téléphone (connecté au WiFi local)
2. Le garde cherche/sélectionne l'employé par nom ou numéro
3. Le garde choisit "Arrivée" ou "Départ"
4. Le garde appuie sur "Vérifier"
5. L'app envoie une requête au PC local (réseau WiFi local)
6. Le PC local déclenche une capture sur la caméra fixe, extrait le visage, compare à l'empreinte enregistrée de l'employé sélectionné
7. Le PC local enregistre la tentative (`verification_attempts`, succès ou échec) puis, si succès, crée l'événement de pointage (`attendance_events`)
8. Le PC local renvoie le résultat à l'app
9. L'app affiche : icône verte + nom + heure ("Ahmed Mohamed — Arrivée enregistrée avec succès — 08:04"), ou icône rouge + "Réessayer" en cas d'échec

Si la vérification échoue, **rien n'est enregistré comme pointage** — seule la tentative échouée est journalisée (§18).

### 3.2 Ajout d'un nouvel employé (§5, §6 cahier de charge)

1. Le garde (si autorisé) ou l'admin ouvre "Ajouter un employé"
2. Saisie du nom complet (obligatoire) ; champs optionnels : numéro personnalisé, département, poste, téléphone, notes
3. Le garde dit à l'employé de regarder la caméra fixe, éventuellement de tourner légèrement la tête
4. Le PC local capture plusieurs photos, vérifie que le visage est visible et correctement positionné
5. Le PC local calcule et stocke l'empreinte faciale de référence
6. L'app confirme "Employé ajouté avec succès" (processus visé : < 1 minute)

Un administrateur peut ré-enregistrer le visage d'un employé existant si son apparence change ou si la reconnaissance devient difficile (§6).

### 3.3 Correction manuelle (§14 cahier de charge)

1. Un administrateur ouvre la fiche employé ou l'historique et sélectionne un enregistrement (ou un jour sans enregistrement)
2. Il choisit l'action : ajouter arrivée manquante, ajouter départ manquant, corriger une heure, changer arrivée↔départ
3. Il saisit obligatoirement une raison
4. Le système crée une entrée d'audit (`corrections`) avec : qui, quand, valeur précédente, nouvelle valeur, raison — **l'enregistrement original n'est jamais supprimé silencieusement**
5. L'historique employé affiche l'enregistrement corrigé avec une indication "corrigé manuellement", consultable dans l'audit trail

### 3.4 Synchronisation vers le dashboard cloud

- Le PC local garde toutes les données en local (SQLite) — le système fonctionne même sans internet
- Quand une connexion internet est disponible, le PC local envoie par lot les nouveaux événements (`attendance_events`, `verification_attempts`, `corrections`) vers le dashboard cloud
- Le management consulte le dashboard cloud pour voir les pointages, l'historique, générer et imprimer des rapports

---

## 4. Contrainte transversale : simplicité extrême de l'app du garde

Le garde peut avoir une faible familiarité avec les applications numériques :

- Gros boutons, peu de texte, icônes claires
- Pas plus de 2-3 actions par écran
- Retour visuel immédiat et sans ambiguïté (vert/rouge, icône ✓/✗, pas de jargon)
- Le flux principal tient en 3 taps maximum : sélectionner l'employé → arrivée/départ → vérifier
- Pas d'écran de configuration visible pour le garde — ça reste côté admin/PC local

---

## 5. Stack technique

| Composant | Choix | Justification |
|---|---|---|
| Caméra | Webcam USB dédiée, branchée au PC local | Confirmé avec le client — cadrage constant, intégration OpenCV directe |
| Traitement facial | **DeepFace** (Python) sur le PC local | Traitement server-side possible (vrai PC, pas un téléphone) — installation simple |
| Backend local | **FastAPI**, tourne sur le PC local | Gère la caméra, le traitement facial, la base de données, l'API pour l'app du garde |
| Base de données locale | **SQLite** sur le PC local | Source de vérité locale, fonctionne sans internet |
| App du garde | **PWA (React + Vite)**, se connecte au PC local via IP/nom local | Reste installable, n'a plus besoin d'accéder à la caméra du téléphone |
| Backend dashboard cloud | **FastAPI** (même stack que le local, réutilisable), base **PostgreSQL** | Cohérence technique, réutilisation de schémas/logique métier (validations, règles de complétude) |
| Dashboard management | **React**, hébergé dans le cloud (Render/Railway) | Consultable de n'importe où, accessible desktop/tablette/téléphone |
| Génération PDF | **WeasyPrint** (HTML/CSS → PDF) côté backend cloud | Permet de designer les rapports en HTML/CSS, cohérent avec le rendu web, gère bien tableaux + zone de signature |
| Export Excel | **openpyxl** côté backend cloud | Standard, léger, pas de dépendance lourde |
| Sync PC local → cloud | Job périodique simple (push des événements `synced = false`) | Pas de résolution de conflits nécessaire — le PC local est la seule source qui écrit les données de pointage |
| HTTPS app du garde | Certificat local (auto-signé ou mkcert), installé une fois sur le téléphone | Nécessaire pour l'installabilité PWA — à valider en Phase 0 |
| Authentification | JWT, même mécanisme local (PC) et cloud (dashboard), rôles portés dans le token | Réutilisable des deux côtés, évite de dupliquer la logique de permissions |

---

## 6. Modèle de données

### PC local (SQLite — source de vérité pour le pointage)

```
employees
  id, full_name, employee_number (auto ou saisi), department, job_title,
  phone, notes, registration_date, active (bool), face_embedding (vecteur),
  created_at, updated_at

users                       -- comptes garde/admin locaux
  id, username, password_hash, role (admin|guard), active, created_at

verification_attempts       -- TOUTE tentative, réussie ou échouée (§18)
  id, employee_id, guard_id, type_requested (arrival|departure),
  timestamp, result (success|failed), similarity_score, failure_reason,
  attendance_event_id (nullable, rempli si succès), synced (bool)

attendance_events           -- uniquement les pointages confirmés (§2, §12)
  id, employee_id, type (arrival|departure), timestamp, guard_id,
  verification_attempt_id, source (auto|manual), synced (bool),
  created_at

corrections                 -- audit trail des modifications manuelles (§14)
  id, attendance_event_id (nullable si ajout d'un enregistrement manquant),
  employee_id, action (add_arrival|add_departure|correct_time|change_type),
  performed_by (user id), performed_at, previous_value (json),
  new_value (json), reason (text), synced (bool)
```

### Dashboard cloud (PostgreSQL — miroir synchronisé + gestion des rôles)

```
employees            -- même structure, alimentée par sync
attendance_events    -- même structure, alimentée par sync
verification_attempts
corrections
users                -- comptes cloud : owner, admin, guard (lecture seule shift), viewer (§20)
```

`synced` marque si l'événement a déjà été poussé vers le dashboard cloud — pas de logique de résolution de conflits puisque le PC local est la seule source qui écrit les données de pointage. Le dashboard cloud écrit uniquement des `corrections` (elles-mêmes redescendues vers le PC local au prochain sync bidirectionnel léger, ou simplement conservées côté cloud comme source de vérité pour les rapports — **à trancher en Phase 0** : est-ce que les corrections faites depuis le dashboard doivent redescendre vers le PC local, ou le PC local reste-t-il uniquement en lecture pour les rapports historiques ? Recommandation : le PC local n'a pas besoin de connaître les corrections — les rapports et l'affichage définitif se font depuis le cloud, qui a la vue complète.

---

## 7. Contrat d'API

### 7.1 PC local ↔ app du garde (réseau local)

```
POST   /auth/login
GET    /employees?query=&department=              (liste + recherche)
POST   /employees                                  (créer un employé)
PATCH  /employees/{id}                              (champs optionnels, active)
POST   /employees/{id}/face                         (enregistrer/ré-enregistrer le visage, capture multi-photos)
POST   /attendance/verify                           (employee_id + type → capture + comparaison + décision + enregistrement)
GET    /attendance/shift-activity                   (pointages du garde connecté, session en cours — §3 cahier de charge)
GET    /dashboard/overview                          (arrivées/départs du jour, vue locale de secours)
```

### 7.2 Dashboard cloud (management)

```
POST   /auth/login
GET    /employees?query=&department=&active=
POST   /employees
PATCH  /employees/{id}
GET    /employees/{id}/attendance?date_from=&date_to=          (§11 — historique date par date)

GET    /attendance?employee_id=&date_from=&date_to=&type=&completeness=   (§10C — filtres)
POST   /attendance/corrections                                  (§14 — créer une correction, avec raison obligatoire)
GET    /attendance/corrections?attendance_event_id=              (audit trail d'un enregistrement)

GET    /dashboard/overview                                       (§10A)

GET    /reports/daily?date=
GET    /reports/weekly?week_start=
GET    /reports/monthly?month=
GET    /reports/custom?employee_id=&date_from=&date_to=
GET    /reports/{type}/export?format=pdf|xlsx&...                (§15, §16)

GET    /users            (owner uniquement)
POST   /users
PATCH  /users/{id}       (rôle, activation/désactivation — §20)
```

Le contrat exact (schémas de requête/réponse) doit être figé en Phase 0 pour que le stagiaire commence l'app du garde et le dashboard contre une API mockée.

### 7.3 Matrice des permissions (§20 cahier de charge)

| Rôle | Capacités |
|---|---|
| Owner / Management | Tout voir, gérer les employés, tous les rapports, imprimer/exporter, corriger les enregistrements, gérer les utilisateurs |
| Administrator | Ajouter des employés, enregistrer les visages, voir le pointage, corriger les enregistrements, générer des rapports |
| Security guard | Chercher un employé, enregistrer arrivée/départ, vérifier le visage, enregistrer un employé si autorisé, voir son activité de shift |
| Viewer | Voir le pointage, imprimer les rapports, ne peut pas modifier |

Implémentation : rôle porté dans le JWT, vérifié côté backend sur chaque endpoint (jamais uniquement côté UI).

---

## 8. Répartition des rôles dans l'équipe

### Toi (lead) — logique métier et intégrations critiques
- Intégration caméra fixe → PC local (capture déclenchée par l'API)
- Traitement facial : DeepFace, calcul et comparaison des empreintes, calibration du seuil
- Flux d'ajout d'employé (capture multi-photos)
- Backend FastAPI local, base de données locale
- Endpoints de corrections manuelles + logique d'audit trail (non-destructif)
- RBAC backend (rôles/permissions, sur les deux backends)
- Endpoints de génération de rapports (agrégation des données — logique métier de complétude : "manquant", "aucun pointage", etc., cf. §11/§13)
- Job de synchronisation PC local → dashboard cloud
- Sécurité (auth, accès réseau local, HTTPS)
- Déploiement sur site du PC local (installation, démarrage automatique) et du dashboard cloud

### Stagiaire (niveau master, autonome en UI) — une fois les contrats figés
- App PWA du garde : tous les écrans (sélection employé, arrivée/départ, résultat, ajout employé), câblage aux appels API
- Dashboard cloud : écrans overview, liste employés, fiche employé (historique date par date), écrans de correction (formulaire, appelle l'endpoint du lead)
- Écrans et déclenchement des rapports (jour/semaine/mois/période), boutons export PDF/Excel/impression (consomme les endpoints du lead)
- Gestion UI des rôles (affichage/masquage selon permissions, appelle l'endpoint `/users` du lead)
- Données de démonstration
- Tests manuels et documentation

Règle inchangée : toute décision de logique métier (correspondance faciale, règles de complétude, audit, permissions serveur) reste chez toi ; l'affichage et le câblage sur une API définie sont délégables.

---

## 9. Revue des images de sécurité — hors scope technique

Le cahier de charge (§7, §8) prévoit que la caméra dédiée reste une caméra de sécurité normale et que le management puisse "réviser les images enregistrées" en cas de litige. **Confirmé avec le client : ceci passe par le NVR/système de vidéosurveillance existant, indépendant de notre développement.**

Conséquences pour le plan :
- Aucun stockage vidéo, aucun lecteur vidéo, aucune fonctionnalité de rejouabilité à développer dans le dashboard ou sur le PC local
- Notre seule responsabilité : garantir que chaque `attendance_event` et chaque `verification_attempt` porte un horodatage fiable et précis, permettant à un administrateur de retrouver manuellement le bon passage sur le système NVR existant
- Documenter cette séparation dans la documentation livrée au client, pour éviter toute confusion future sur le périmètre du système

---

## 10. Plan de travail, en ordre

### Phase 0 — Cadrage (0,5-1 jour)
1. Figer le contrat d'API complet (§7), y compris rapports, corrections, rôles
2. Trancher les points ouverts du §1 (HTTPS local, hébergement cloud, format des rapports imprimés, fenêtre anti-doublon, schéma de numérotation employé)
3. Décider si les corrections faites depuis le cloud redescendent vers le PC local (§6) ou restent cloud-only
4. Définir les maquettes ultra-simples de l'app du garde (gros boutons, peu d'écrans) et une maquette du rapport imprimé (§16)

### Phase 1 — PC local : fondations + caméra (3-4 jours) — toi
1. Setup FastAPI + base de données locale (SQLite)
2. Intégration de la webcam USB (capture d'image sur demande via OpenCV)
3. Auth basique (login garde/admin, JWT avec rôle)
4. Test unitaire : capture d'une photo, extraction d'empreinte DeepFace

### Phase 2 — Vérification et enregistrement facial (3-4 jours) — toi
1. Endpoint `/attendance/verify` complet (capture → comparaison → décision → `verification_attempts` → `attendance_events` si succès)
2. Flux d'ajout d'employé (capture multi-photos, calcul de l'empreinte de référence)
3. Blocage des soumissions dupliquées (fenêtre configurable, défaut 60s)
4. Calibration du seuil de décision avec de vraies photos (toi + volontaires)

### Phase 2bis — Corrections manuelles et audit trail (1,5-2 jours) — toi
1. Modèle et endpoints `corrections` (ajout, correction, changement de type)
2. Garantie de non-destruction (l'original reste lisible, l'historique de correction est consultable)
3. Tests : ajouter une arrivée manquante, corriger une heure, changer arrivée↔départ, vérifier la traçabilité

### Phase 3 — App PWA du garde (3-4 jours, en parallèle des Phases 1-2) — stagiaire, sous ta revue
1. Écrans : sélection employé, choix arrivée/départ, bouton vérifier, écran résultat
2. Écran ajout employé
3. Écran "activité de mon shift"
4. Connexion au PC local via IP/nom local, contre l'API mockée puis réelle
5. Test d'installabilité PWA sur le téléphone du garde

### Phase 4 — Dashboard cloud, rôles et rapports (5-6 jours) — mixte
1. RBAC backend (rôles/permissions sur les deux backends) — toi (~1 jour)
2. Endpoints de rapports (jour/semaine/mois/période) + agrégation de complétude — toi (~1,5 jour)
3. Génération PDF (WeasyPrint) et export Excel (openpyxl) — toi (~1 jour)
4. Dashboard UI : overview, liste employés, fiche employé (historique date par date §11), écrans de correction, déclenchement rapports/export/impression, gestion des rôles — stagiaire, une fois les endpoints prêts (~2-2,5 jours)
5. Job de synchronisation PC local → cloud (push des événements non-synchronisés) — toi
6. Déploiement du backend + dashboard cloud (Render/Railway) — toi

### Phase 5 — Intégration réseau local et déploiement sur site (1-2 jours) — toi
1. Certificat HTTPS local, installé sur le téléphone du garde
2. Test de bout en bout sur le vrai réseau WiFi du poste de garde, avec la vraie caméra
3. Configuration du démarrage automatique du backend sur le PC local

### Phase 6 — Stabilisation et tests d'acceptation (2-3 jours)
1. Geler les fonctionnalités, corriger uniquement les bugs bloquants
2. Tester avec plusieurs employés réels et conditions de lumière variées
3. Tester les permissions par rôle (un garde ne doit pas accéder aux fonctions admin, etc.)
4. Vérifier chaque critère d'acceptation (§11)
5. Préparer le scénario de démo final

**Estimation totale : ~18 à 22 jours ouvrés (3,5 à 4,5 semaines).** Révisée à la hausse par rapport au draft initial (12-16 jours) pour refléter le scope complet du cahier de charge sur les rôles, l'audit trail et les rapports/export — largement compensée par l'absence d'intégration vidéo (NVR externe) et la simplicité de l'intégration caméra USB (déjà confirmée, plus de branche RTSP à prévoir).

---

## 11. Critères d'acceptation (§21 cahier de charge)

Le système doit répondre de façon fiable à ces quatre questions, pour n'importe quel employé et n'importe quelle période :
1. L'employé est-il venu ?
2. À quelle heure est-il arrivé ?
3. À quelle heure est-il parti ?
4. Était-il physiquement présent au moment de l'enregistrement ?

Et démontrer, en démo finale :
- **Flux garde** : chercher employé → choisir arrivée/départ → vérifier le visage → confirmation en < 5 secondes
- **Flux management** : chercher employé → sélectionner une période → voir/imprimer l'historique complet
- Une tentative avec un mauvais visage est rejetée et journalisée, sans créer de pointage
- Une correction manuelle est traçable (qui, quand, avant/après, raison) sans supprimer l'original
- Un rapport jour/semaine/mois/période s'imprime et s'exporte (PDF + Excel) avec toutes les mentions requises (§16)
- Le système continue à fonctionner localement pendant une coupure internet, puis se resynchronise sans doublon
- Les permissions par rôle sont respectées (un viewer ne peut rien modifier, un garde n'a pas accès à l'admin)

---

## 12. Risques mis à jour

| Risque | Mitigation |
|---|---|
| PC local = point unique de défaillance pour tout le poste de garde | Redémarrage automatique du service backend, procédure de dépannage documentée pour le personnel sur site |
| Certificat HTTPS local mal configuré → app inutilisable | Tester la procédure d'installation du certificat sur le téléphone du garde dès la Phase 0 |
| Réseau WiFi local instable au poste de garde | Tester la portée/qualité du signal entre le PC local et l'emplacement du garde dès la Phase 1 |
| Interface trop complexe pour un garde peu familier avec le numérique | Tester l'app avec un utilisateur réel (pas seulement toi/le stagiaire) avant la Phase 6 |
| Format des rapports imprimés ne correspond pas aux attentes du client | Valider une maquette de rapport (logo, mise en page, zone de signature) avant d'écrire le code de génération PDF en Phase 4 |
| Confusion côté client sur la revue vidéo (croire que le dashboard inclut la vidéo) | Documenter explicitement que la revue vidéo passe par le NVR existant, séparé (§9), dès la livraison du cahier de charge validé |
| Bugs de permissions (un rôle accède à des fonctions non autorisées) | Tests dédiés par rôle en Phase 6, vérification systématique côté backend (jamais uniquement côté UI) |
| Stagiaire bloqué en attendant l'API | Contrat d'API figé en Phase 0, API mockée pour qu'il commence sans attendre |
| Sous-estimation du scope (déjà arrivé une fois avec le dashboard "minimal") | Cette révision recale le plan sur le cahier de charge complet — toute nouvelle fonctionnalité demandée par le client doit être comparée au §22 avant d'être ajoutée au scope V1 |

---

## 13. Ce qui reste inchangé

- Règles métier : une arrivée/un départ par pointage explicite choisi par le garde (le système ne devine jamais), gestion des enregistrements incomplets (§12, §13)
- Rôles Owner/Admin/Guard/Viewer (§20)
- Workflow GitHub (branches, PR, revue) — voir le document précédent, toujours valable
- Le PC local reste la seule source qui écrit les données de pointage brutes ; le cloud ne fait qu'ajouter des corrections/rapports par-dessus
