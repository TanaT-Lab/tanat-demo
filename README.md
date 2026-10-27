# TanaT Demo

Interactive demonstrations of the TanaT framework for temporal sequence analysis.

**Live demo:** https://tanat-lab.github.io/tanat-demo/

**TanaT repository:** https://github.com/TanaT-Lab/TanaT

> The history of this repository before 2026-10-26 is archived at
> https://gitlab.inria.fr/tanat/comms/tanat-demo.

## Overview

A modular demo framework: a player types real TanaT code step by step, shows its
outputs and figures, synchronized with an audio narration. Each demo is
self-contained. The code shown is **written once**, in a `pipeline.py` that is
really executed: what the audience sees is what ran.

| Demo | Description |
|------|-------------|
| **mimic-clustering** | Hospital readmission pattern analysis using MIMIC-IV data |

## Quick Start

```bash
pip install -r requirements.txt   # pins tanat==0.10.4
python run.py                     # generate outputs if needed, serve, open browser

python run.py --port 9000         # custom port
python run.py --regenerate        # force regenerate all outputs
python run.py --no-browser        # don't open browser
```

## Architecture

```
tanat-demo/
├── index.html              # Landing page (cards read from demos/index.json)
├── player.html             # Universal demo player
├── run.py                  # Local launcher
├── generate_all.py         # Runs demos/*/pipeline.py, writes outputs + demos/index.json
│
├── core/                   # Shared front (no build step)
│   ├── styles.css          # Dark terminal theme
│   ├── player.js           # Player logic (typewriter, navigation, audio)
│   └── landing.js          # Landing page controller
│
├── tools/tts.py            # SCRIPT.md sections -> audio/*.mp3 (Kokoro, CPU)
├── tests/                  # pytest (+ Playwright headless for the front)
├── assets/                 # Shared assets (logo)
├── data/                   # Shared data (mimic_admissions_pool.csv)
│
└── demos/                  # Individual demos
    ├── index.json          # Generated manifest (gitignored)
    └── mimic-clustering/
        ├── pipeline.py     # The code shown, in `# %% <id>` blocks
        ├── demo.json       # Card metadata (landing page, player header)
        ├── config.js       # Staging: intro notes, stations, audio, shown block ids
        ├── SCRIPT.md       # Narration, one `## <section>` per audio file
        ├── audio/          # Narration mp3
        └── outputs/        # Generated (gitignored): outputs.json + figures
```

## Adding a New Demo

1. **Create** `demos/my-demo/`.
2. **`pipeline.py`**: everything before the first `# %%` marker is a hidden
   preamble (imports, plot theme). Each `# %% <id>` block is run in a shared
   namespace; its code, printed output and at most one figure go to
   `outputs/outputs.json` (figure saved as `outputs/<id>.png`).

   ```python
   # %% 1a
   import pandas as pd
   df = pd.read_csv("data/my_data.csv")
   print(f"Loaded {len(df)} records")
   ```

3. **`demo.json`**: `id`, `title`, `subtitle`, `description`, `icon`, `tags`.
4. **`config.js`**: staging only. List the stations and which block ids each one
   shows (`blocks: ['1a', '1b']`); a block that is not listed runs but stays
   hidden. See `demos/mimic-clustering/config.js`.
5. **Narration**: write `SCRIPT.md` (`## intro`, `## step1` ... `## end`), then
   `uv run tools/tts.py my-demo` (cached by text hash, fails above the time budget).
6. **Check**: `python generate_all.py my-demo`, then `python run.py`.

The landing page picks the demo up from `demos/index.json`: nothing else to register.

## Development

```bash
python generate_all.py                  # all demos
python generate_all.py mimic-clustering # one demo
python generate_all.py --list           # list demos

pytest tests/                           # front tests need: pip install playwright && playwright install chromium
```

CI runs on every PR and push to `main` (`.github/workflows/pages.yml`): it
regenerates the demo outputs with the pinned TanaT and runs the tests. On `main`
it publishes the site to GitHub Pages — enable it in
**Settings > Pages > Source: GitHub Actions**. Build the site locally with
`python tools/build_site.py _site`.

## Requirements

- Python 3.10+
- `tanat==0.10.4` (see `requirements.txt`)

## License

See the main [TanaT repository](https://github.com/TanaT-Lab/TanaT) for license information.
