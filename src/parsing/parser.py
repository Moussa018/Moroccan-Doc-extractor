import json
import re
import unicodedata
from pathlib import Path

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent.parent / "configs" / "license.json"


def load_config(path=DEFAULT_CONFIG):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _norm(s):
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def _find_label(lines, keywords):
    for line in lines:
        t = _norm(line["text"])
        if any(_norm(k) in t for k in keywords):
            return line
    return None


def _extract(spec, text):
    text = " ".join(text.split())
    if spec.get("fix_digits"):
        text = text.replace("O", "0").replace("o", "0")
    pattern = spec.get("pattern")
    if pattern:
        m = re.search(pattern, text)
        if not m:
            return text
        text = m.group(1) if m.groups() else m.group(0)
        if "format" in spec:
            text = spec["format"].format(text)
    return text


def parse(lines, config=None):
    config = config or load_config()
    fields = config["fields"]
    x_tol = config.get("x_tol", 2)
    max_gap = config.get("max_gap", 3)

    labels = {f: _find_label(lines, s["labels"]) for f, s in fields.items()}
    label_ids = {id(l) for l in labels.values() if l}
    values = [l for l in lines if id(l) not in label_ids]

    out = {}
    for field, spec in fields.items():
        out[field] = ""
        lab = labels[field]
        if lab is not None:
            x1, y1, _, y2 = lab["box"]
            h = y2 - y1
            # valeur = ligne la plus proche sous le libelle, alignee a gauche sur lui
            cands = [v for v in values
                     if abs(v["box"][0] - x1) <= x_tol * h and 0 <= v["box"][1] - y2 <= max_gap * h]
            if cands:
                best = min(cands, key=lambda v: v["box"][1])
                out[field] = _extract(spec, best["text"])
        if not out[field] and spec.get("search_all") and spec.get("pattern"):
            for l in lines:  # repli : champ au format reconnaissable
                if re.search(spec["pattern"], l["text"]):
                    out[field] = _extract(spec, l["text"])
                    break
    return out
