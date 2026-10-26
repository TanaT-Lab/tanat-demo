# TanaT Demo — Feuille de route Refonte + Migration

> État actuel : le repo repose sur une **ancienne API TanaT** (la démo casse dès l'import)
> et a besoin d'une refonte structurelle pour devenir un showcase **scalable** (1 démo
> aujourd'hui, potentiellement beaucoup plus) et **portable** (migration GitLab → GitHub
> `TanaT-Lab`).

**Objectifs :**
1. Rendre la démo **fonctionnelle avec TanaT actuel** (0.10.4, publié sur PyPI).
2. **Simplifier / clarifier** le code tout en gardant l'essence du projet.
3. Garder l'UX/le front tel qu'il est (jugé bon) — refonte **structurelle**, pas de redesign.
4. **Cible : conférence** → la démo doit durer **moins de 5 min**.
5. Préparer la **migration vers GitHub** (`github.com/TanaT-Lab`).

Specs : `TanaT-Lab/specs` → `subrepos/tanat-demo/`.

---

## Décisions actées (2026-10-26)

| Sujet | Décision |
|---|---|
| Base du contenu | S'aligner sur les tutos MIMIC de TanaT (`TanaT/doc/source/user-guide/tutorials/mimic/analyse_and_cluster.py`), **sans ajouter d'étape**. |
| Code de la démo | **Écrit une seule fois** : un `pipeline.py` par démo, découpé en blocs `# %% <id>`. Il produit `outputs.json` (code + sortie + figure par bloc), seule source lue par le player. |
| Données | **CSV versionné** dans `data/`, lu par `pd.read_csv` dans la démo (pas de réseau en conf). `data/build_csv.py` le reconstruit depuis `tanat.dataset.access('mimic4')` (lancé à la main, pas en CI). |
| Version TanaT | Épinglée : `tanat==0.10.4` (PyPI). |
| Audio | **Généré par script** depuis `SCRIPT.md` découpé en sections. Moteur local CPU (**Kokoro-82M**, Apache-2.0) sous réserve d'un POC d'écoute. mp3 versionnés, régénérés seulement si le texte change. |
| Durée | Budget audio **≈ 4 min 20** (actuel : **5 min 38**). Garde-fou : échec si total > 4 min 45. |

---

## 1. `pipeline.py` + migration API TanaT 0.10.4 (bloquant)

Réécrire `demos/mimic-clustering/generate.py` en `pipeline.py` directement avec la nouvelle API.
Le code n'existe plus dans `config.js`.

```python
# %% 3a
criterion = EntityCriterion(query=pl.col("admission_type").str.contains("EMER"))
emergency_pool = pool.subset(pool.which(criterion))
print(emergency_pool)
```

`generate.py` (générique, partagé) exécute les blocs à la suite dans un namespace commun,
capture `stdout`, sauve les figures, écrit `outputs.json` :

```json
{ "3a": { "code": "...", "output": "...", "figure": null } }
```

Tableau de migration (vérifié contre le code de TanaT 0.10.4) :

| Ancien (démo) | TanaT 0.10.4 | Remarque |
|---|---|---|
| `QueryCriterion(query="str pandas")` | `EntityCriterion(query=pl.Expr)` | Requête en **Polars** |
| `pool.filter(criterion, level="sequence")` | `pool.subset(pool.which(criterion))` | ⚠️ **Pas** `filter_entities` : il élague les admissions, alors que la démo garde les patients entiers |
| `pool.zero_from_query(query=...)` | `pool.set_t0(query=pl.Expr, anchor="start")` | |
| `pool.t_zero` | `pool.t0_data()` | |
| `pool.static_data["cluster"]` | `pool.static_data()["cluster"]` | `static_data` est devenu une méthode |
| `HammingEntityMetricSettings(default_value=0.0)` | `HammingSettings(entity_feature=, cost=, mismatch_cost=)` | `default_value` n'existe plus ; Hamming compare **une seule** feature → choisir laquelle |
| `EditSequenceMetricSettings(entity_metric=obj)` | `EditSettings(entity_metric=, indel_cost=, normalize=)` | Accepte `"hamming"` |
| `HierarchicalClustererSettings(...)` | `HierarchicalSettings(metric=, n_clusters=, cluster_column=)` | |
| `SequenceVisualizer.histogram(...)` | `SequenceVisualizer.barplot(...)` | |
| `timeline(relative_time=, granularity=, stacking_mode=)` | `timeline(time_mode="relative", display_unit=)` | `TimeMode` est un `Literal`, pas une enum |
| `draw(pool, entity_features=[...])` | `draw(pool, entity_feature=...)` | Singulier |
| `.xlabel(...)` | `.x_axis(label=...)` | |
| `.facet(by="cluster", ...)` | `.facet(by="cluster", is_static=True, ...)` | `cluster` est statique → à confirmer à l'exécution |

**Validation :** `python generate_all.py` passe en local (uv + TanaT 0.10.4).

## 2. Player branché sur `outputs.json`

- Le player lit `demos/<id>/outputs/outputs.json` (code + sorties + figures).
- `config.js` ne garde que la **mise en scène** : métadonnées, intro, audio, ordre des
  stations et des blocs (par id).
- Fini les sorties codées en dur ("100 patients", "Cluster 0: 2 patients"…).
- `resources.colorPalette` (jamais affiché) : intégrer `ADMISSION_COLORS` comme vrai bloc
  du pipeline, puisque les snippets l'utilisent.

## 3. Narration & audio

**Budget** (durées mesurées sur les mp3 actuels) :

| Section | Actuel | Cible |
|---|---|---|
| intro | 97 s | 65 s |
| step1 Load | 49 s | 35 s |
| step2 Visualize | 28 s | 25 s |
| step3 Filter | 31 s | 27 s |
| step4 Align | 36 s | 30 s |
| step5 Cluster | 40 s | 35 s |
| step6 Analyze | 27 s | 25 s |
| end | 30 s | 20 s |
| **Total** | **5 min 38** | **≈ 4 min 20** |

- Réécrire `SCRIPT.md` : ~150 mots en moins, alignement sur la nouvelle API ("pandas-like
  query syntax" devient faux), chiffres issus de `outputs.json`.
- Structurer `SCRIPT.md` en sections (`## intro`, `## step1`, …, `## end`).
- Script `tools/tts.py` : une section → un mp3, cache par hash du texte, affiche la durée
  par section, échoue si total > 4 min 45.
- **Timings des notes d'intro calculés automatiquement** (marqueurs de notes dans le script,
  synthèse morceau par morceau) au lieu des `time:` réglés à la main dans `config.js`.
- POC Kokoro : générer l'intro avec 2–3 voix, comparer à l'oreille avant de s'engager.
  Alternatives : Piper (plus robotique), Google Cloud / Azure (quota gratuit, compte requis).
  À éviter : edge-tts (non officiel, fragile), XTTS (licence non commerciale).

## 4. Nettoyage du code mort & bugs

Code mort :
- `player.js` : `startDemo`, `showPlayOverlay` (`#play-overlay` n'existe pas),
  `typewriterHTML` + `INTRO_SPEED` / `PAUSE_AFTER_PERIOD`, `resetDemo`, `resetDemoState`
  (référence `intro-text`, `intro-final`, `full-script`, supprimés).
- Écran *welcome* : jamais affiché, `#start-demo-btn` relié à rien.
- `styles.css` : `.play-overlay*`.
- `displayNote` : ~15 types de notes gérés, ~8 utilisés → réduire l'API.
- `README.md` : `index-new.html` (inexistant), commandes obsolètes.
- `.gitignore` : `outputs/figures/` ("Legacy").

Bugs probables (à confirmer au navigateur) :
- "Ready to start" laisse `currentStation = -1` → à la fin de l'audio d'intro,
  `onAudioEnded` ne fait rien (pas d'enchaînement automatique vers l'étape 1).
- "Prev" depuis l'étape 1 relance l'intro mais laisse `currentStation = 1` → à la fin de
  l'audio, `goToStation(2)` alors qu'on est sur l'intro.

## 5. Landing pilotée par un manifeste

- Fin de la duplication `config.js` / `landing.js` (les titres ont déjà divergé).
- Un site statique ne peut pas lister un dossier → `generate_all.py` écrit
  `demos/index.json` au build ; la landing le lit.
- Ajouter une démo = créer le dossier, c'est tout.

## 6. Refonte front (structurelle)

Découper `core/player.js` (1309 lignes) en modules ES, sans build :

```
core/player/
├── main.js          # point d'entrée, orchestration du déroulé
├── state.js         # machine à états explicite (transition→intro→demo→full-script)
├── render.js        # génération DOM (pipeline, stations, notes)
├── audio.js         # lecture audio + autoplay policy
├── typewriter.js    # effets d'écriture
└── navigation.js    # prev/next/pause/reveal + drag&drop
```

- **Comportement/UX inchangé.** La machine à états remplace `currentLayout`,
  `currentStation`, `isTyping`, `isPaused`, `isZoomedOut`… (corrige les bugs du §4).
- Optionnel, faible priorité : découper `core/styles.css` (2366 lignes) en
  `base / landing / player / screens / responsive`.

## 7. Migration GitHub (TanaT-Lab)

De `gitlab.inria.fr/tanat/comms/tanat-demo` vers `github.com/TanaT-Lab/tanat-demo`.
Indépendante du reste → **à faire tôt** pour que les PRs de la refonte vivent sur le
dépôt définitif.

- [ ] Créer `tanat-demo` sur l'org **TanaT-Lab** et pousser l'historique.
- [ ] Remplacer `.gitlab-ci.yml` + GitLab Pages par `.github/workflows/pages.yml` + GitHub Pages.
- [ ] CI : `tanat==0.10.4` épinglé (`pyproject.toml` ou `requirements.txt`), lancé aussi
      sur les PRs (la démo a cassé en silence avec `pip install tanat` non épinglé).
- [ ] Liens (README, `index.html`, `player.html`) : GitLab → GitHub, doc TanaT,
      `https://tanat-lab.github.io/tanat-demo/`.
- [ ] Données : documenter la provenance et la licence du CSV (MIMIC-IV Clinical Database
      Demo, ODbL, à confirmer) avant publication publique.

---

## Ordre d'exécution

1. **`pipeline.py` migré + CSV + version épinglée** (§1) — rend le projet fonctionnel.
   En parallèle : **POC TTS** (§3), **nettoyage** (§4), **création du dépôt GitHub** (§7).
2. **Player sur `outputs.json`** (§2).
3. **Réécriture de `SCRIPT.md` + génération audio** (§3) — après §1, les chiffres cités en dépendent.
4. **Manifeste landing** (§5).
5. **Refonte front** (§6).
6. **GitHub Actions + Pages + liens** (§7) ; validation finale `python run.py`.

## Questions ouvertes

- Texte de la narration de l'étape 1 (49 s d'audio) : absent de `SCRIPT.md`.
- Feature comparée par Hamming : `admission_type` seule, ou autre choix ?
- Choix de la voix (après POC).
