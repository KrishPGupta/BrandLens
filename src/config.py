from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_config(path=None):
    p = Path(path) if path else ROOT / "config" / "config.yaml"
    with open(p) as f:
        return yaml.safe_load(f)


def resolve(cfg, key):
    """Absolute path for a key under cfg['paths'], created if missing."""
    p = ROOT / cfg["paths"][key]
    if p.suffix == "":
        p.mkdir(parents=True, exist_ok=True)
    else:
        p.parent.mkdir(parents=True, exist_ok=True)
    return p
