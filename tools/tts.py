# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "kokoro==0.9.4",
#   "soundfile",
#   "numpy",
#   "torch==2.14.1",
# ]
#
# [tool.uv.sources]
# torch = { index = "pytorch-cpu" }
#
# [[tool.uv.index]]
# name = "pytorch-cpu"
# url = "https://download.pytorch.org/whl/cpu"
# explicit = true
# ///
"""Narration audio from a demo's SCRIPT.md, one mp3 per section (Kokoro, CPU).

Usage: uv run tools/tts.py <demo_id> [--voice af_heart] [--force] [--budget 285]

SCRIPT.md format: sections start with '## <name>' (intro, step1..stepN, end);
text before the first heading is ignored; paragraphs are separated by blank
lines. Writes demos/<id>/audio/<section>.mp3 and audio/manifest.json.
Only sections whose hash (voice + normalized text) changed are regenerated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SAMPLE_RATE = 24000
PAUSE_S = 0.4
DEFAULT_VOICE = "af_heart"
DEFAULT_BUDGET = 285.0


def parse_script(text: str) -> dict[str, list[str]]:
    """Return {section: [paragraph, ...]} in file order."""
    sections: dict[str, list[str]] = {}
    current: str | None = None
    buf: list[str] = []

    def flush() -> None:
        if current is None:
            return
        paras, cur = [], []
        for line in buf + [""]:
            if line.strip():
                cur.append(line.strip())
            elif cur:
                paras.append(" ".join(cur))
                cur = []
        sections[current] = paras

    for line in text.splitlines():
        m = re.match(r"##\s+(\S.*?)\s*$", line)
        if m and not line.startswith("###"):
            flush()
            current, buf = m.group(1), []
        elif current is not None:
            buf.append(line)
    flush()
    return sections


def section_hash(voice: str, paragraphs: list[str]) -> str:
    norm = "\n\n".join(" ".join(p.split()) for p in paragraphs)
    return hashlib.sha256(f"{voice}\n{norm}".encode("utf-8")).hexdigest()


class KokoroBackend:
    """Real synthesizer; heavy imports happen here only."""

    def __init__(self, voice: str):
        from kokoro import KPipeline  # noqa: PLC0415

        self.voice = voice
        self.pipeline = KPipeline(lang_code=voice[0], device="cpu")

    def synth(self, text: str):
        import numpy as np  # noqa: PLC0415

        chunks = [r.audio.cpu().numpy() for r in self.pipeline(text, voice=self.voice, speed=1.0)]
        return np.concatenate(chunks) if chunks else np.zeros(0, dtype="float32")

    def write(self, path: Path, parts: list, pause_samples: int) -> None:
        import numpy as np  # noqa: PLC0415
        import soundfile as sf  # noqa: PLC0415

        silence = np.zeros(pause_samples, dtype="float32")
        seq = []
        for i, p in enumerate(parts):
            if i:
                seq.append(silence)
            seq.append(p)
        sf.write(str(path), np.concatenate(seq), SAMPLE_RATE, format="MP3")


def run(demo_dir: Path, voice: str, force: bool, budget: float, backend_factory=None) -> int:
    script = demo_dir / "SCRIPT.md"
    sections = parse_script(script.read_text(encoding="utf-8"))
    audio_dir = demo_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = audio_dir / "manifest.json"
    old: dict = {}
    if manifest_path.exists():
        old = json.loads(manifest_path.read_text(encoding="utf-8")).get("sections", {})

    for name in set(old) - set(sections):
        (audio_dir / f"{name}.mp3").unlink(missing_ok=True)

    backend = None
    pause = int(PAUSE_S * SAMPLE_RATE)
    entries: dict[str, dict] = {}
    rows = []
    for name, paras in sections.items():
        h = section_hash(voice, paras)
        mp3 = audio_dir / f"{name}.mp3"
        prev = old.get(name)
        if not force and prev and prev.get("hash") == h and mp3.exists():
            entries[name] = prev
            rows.append((name, prev["duration"], "no"))
            continue
        if backend is None:
            backend = (backend_factory or KokoroBackend)(voice)
        parts = [backend.synth(p) for p in paras]
        offsets, t = [], 0.0
        for i, part in enumerate(parts):
            if i:
                t += PAUSE_S
            offsets.append(round(t, 3))
            t += len(part) / SAMPLE_RATE
        backend.write(mp3, parts, pause)
        entries[name] = {"hash": h, "duration": round(t, 3), "offsets": offsets}
        rows.append((name, entries[name]["duration"], "yes"))

    manifest = {"voice": voice, "sections": entries}
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    total = sum(r[1] for r in rows)
    w = max([len(r[0]) for r in rows] + [7])
    print(f"{'section':<{w}}  {'duration':>9}  regenerated")
    for name, dur, regen in rows:
        print(f"{name:<{w}}  {dur:>8.1f}s  {regen}")
    print(f"{'TOTAL':<{w}}  {total:>8.1f}s  (budget {budget:.0f}s)")
    if total > budget:
        print(f"ERROR: total {total:.1f}s exceeds budget {budget:.0f}s", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate narration mp3 per SCRIPT.md section (Kokoro).")
    ap.add_argument("demo_id")
    ap.add_argument("--voice", default=DEFAULT_VOICE)
    ap.add_argument("--force", action="store_true", help="regenerate all sections")
    ap.add_argument("--budget", type=float, default=DEFAULT_BUDGET, help="max total seconds (default 285)")
    ap.add_argument("--demos-dir", type=Path, default=Path(__file__).resolve().parent.parent / "demos")
    a = ap.parse_args(argv)
    demo_dir = a.demos_dir / a.demo_id
    if not (demo_dir / "SCRIPT.md").exists():
        print(f"ERROR: {demo_dir / 'SCRIPT.md'} not found", file=sys.stderr)
        return 2
    return run(demo_dir, a.voice, a.force, a.budget)


if __name__ == "__main__":
    raise SystemExit(main())
