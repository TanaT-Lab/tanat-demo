# TanaT Demo

Interactive demonstrations of the TanaT framework for temporal sequence analysis.

**Live demo:** https://tanat.gitlabpages.inria.fr/core/tanat-demo/

**TanaT repository:** https://gitlab.inria.fr/tanat/core/tanat

## Overview

This is a modular demo framework that showcases TanaT capabilities through interactive, narrated demonstrations. Each demo is self-contained with its own configuration, audio files, and generated outputs.

### Current Demos

| Demo | Description |
|------|-------------|
| **mimic-clustering** | Hospital readmission pattern analysis using MIMIC-IV data |

## Quick Start

```bash
# Run the demo locally
python run.py

# Options
python run.py --port 9000      # Custom port
python run.py --regenerate     # Force regenerate all outputs
python run.py --no-browser     # Don't open browser
```

## Architecture

```
tanat-demo/
├── index.html              # Landing page (demo selection)
├── player.html             # Universal demo player
├── run.py                  # Local launcher
├── generate_all.py         # Master output generator
│
├── core/                   # Shared components
│   ├── styles.css          # Dark terminal theme
│   ├── player.js           # Player logic (typewriter, navigation)
│   └── landing.js          # Landing page controller
│
├── assets/                 # Shared assets
│   └── logo.png
│
├── data/                   # Shared data files
│   └── mimic_admissions_pool.csv
│
└── demos/                  # Individual demos
    └── mimic-clustering/
        ├── config.js       # Demo configuration
        ├── generate.py     # Output generator script
        ├── audio/          # Narration audio files
        └── outputs/        # Generated figures (gitignored)
```

## Adding a New Demo

### 1. Create the demo folder

```bash
mkdir -p demos/my-demo/{audio,outputs}
```

### 2. Create `demos/my-demo/config.js`

```javascript
const DEMO_CONFIG = {
    id: 'my-demo',
    title: 'My Demo Title',
    subtitle: 'Subtitle',
    description: 'Short description',
    
    intro: {
        audio: 'audio/intro.mp3',
        phases: [
            { type: 'text', content: 'Welcome to this demo...' }
        ]
    },
    
    stations: [
        {
            id: 1,
            name: 'Load',
            description: 'Load data',
            audio: 'audio/step1.mp3',
            blocks: [
                {
                    id: '1a',
                    code: `import pandas as pd\ndf = pd.read_csv("data.csv")`,
                    output: 'Loaded 100 records'
                }
            ]
        }
        // More stations...
    ],
    
    outro: { audio: 'audio/end.mp3' }
};
```

### 3. Create `demos/my-demo/generate.py`

```python
#!/usr/bin/env python3
"""My Demo - Output Generator"""

import os
DEMO_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUTS_DIR = os.path.join(DEMO_DIR, "outputs")

def generate():
    """Generate outputs. Returns True on success."""
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    
    # Generate your figures here...
    # Save them as OUTPUTS_DIR/block_id.png
    
    print(f"  [my-demo] ✓ Generated outputs")
    return True

if __name__ == "__main__":
    import sys
    sys.exit(0 if generate() else 1)
```

### 4. Register in `core/landing.js`

```javascript
const DEMOS_REGISTRY = [
    // Existing demos...
    {
        id: 'my-demo',
        title: 'My Demo Title',
        subtitle: 'Subtitle',
        description: 'Short description',
        icon: '📊',
        tags: ['tag1', 'tag2'],
        duration: '~5 min',
        path: 'demos/my-demo'
    }
];
```

### 5. Add audio files

Record narration and save to `demos/my-demo/audio/`:
- `intro.mp3` - Introduction
- `step1.mp3` → `stepN.mp3` - One per station
- `end.mp3` - Conclusion

### 6. Test locally

```bash
python run.py --regenerate
```

## CI/CD Pipeline

The GitLab CI pipeline automatically:

1. **Build stage**: Runs `generate_all.py` to create outputs for all demos
2. **Deploy stage**: Publishes to GitLab Pages

Outputs are regenerated on every push to `main`.

## Development

### Generate outputs manually

```bash
# All demos
python generate_all.py

# Specific demo
python generate_all.py mimic-clustering

# List available demos
python generate_all.py --list
```

### Local development server

```bash
python -m http.server 8080
# Open http://localhost:8080/index.html
```

## Requirements

- Python 3.10+
- TanaT framework (`pip install tanat`)
- matplotlib, pandas

## License

See the main [TanaT repository](https://gitlab.inria.fr/tanat/core/tanat) for license information.
