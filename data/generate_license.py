import json 
import random
import sys 
from datetime import date , timedelta
from pathlib import Path
from playwright.sync_api import sync_playwright


SURNAMES = ["Alaoui", "Bennani", "Idrissi", "Tazi", "Berrada", "Chraibi", "Fassi",
            "Lahlou", "Benjelloun", "Amrani", "Saidi", "Mansouri", "Ouazzani", "Haddad"]
GIVEN = ["Youssef", "Mohamed", "Karim", "Amine", "Hamza", "Omar", "Sara",
         "Salma", "Imane", "Fatima", "Zineb", "Yassine", "Nadia", "Rachid"]
CITIES = ["Casablanca", "Rabat", "Fes", "Marrakech", "Tanger", "Agadir",
          "Meknes", "Oujda", "Kenitra", "Tetouan", "Safi", "El Jadida"]
CATEGORIES = ["A", "A1", "B", "C", "D", "B, C", "A, B"]
FONTS = ["sans-serif", "serif", "monospace"]
BACKGROUNDS = [("#e8f1f8", "#f6efe4"), ("#eef5e8", "#f8f3df"), ("#f1e9f5", "#e6eef8")]

FIELDS = [
    ("surname", "Nom / Surname", 260, 80),
    ("given_name", "Prénom / Given name", 260, 145),
    ("dob", "Date de naissance", 260, 210),
    ("pob", "Lieu de naissance", 520, 210),
    ("issue_date", "Délivré le", 260, 275),
    ("expiry_date", "Expire le", 520, 275),
    ("license_no", "N° du permis", 260, 340),
    ("categories", "Catégories", 520, 340),
]

SCALE = 2


def fmt(d):
    return d.strftime("%d/%m/%Y")

def rand_date(start , end):
    return start + timedelta(days=random.randint(0,(end-start).days))

def make_record():
    dob = rand_date(date(1980,1,1) , date(2004,12,31))
    issue = rand_date(dob+ timedelta(days=18*366), date(2025, 12, 31))
    expiry = issue + timedelta(days=3652)
    return {
        "surname" : random.choice(SURNAMES).upper(),
        "given_name": random.choice(GIVEN),
         "dob": fmt(dob),
        "pob": random.choice(CITIES),
        "issue_date": fmt(issue),
        "expiry_date": fmt(expiry),
        "license_no": f"SP-{random.randint(0, 99999999):08d}",  # format fictif
        "categories": random.choice(CATEGORIES),   
    }

def build_html(rec):
    c1, c2 = random.choice(BACKGROUNDS)
    font = random.choice(FONTS)
    blocks = ""
    for key, label, x, y in FIELDS:
        blocks += (
            f'<div class="f" style="left:{x}px;top:{y}px">'
            f'<span class="l">{label}</span>'
            f'<span class="v" data-field="{key}">{rec[key]}</span></div>'
        )
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
body{{margin:0;background:#fff}}
#card{{position:relative;width:856px;height:540px;overflow:hidden;border-radius:24px;
background:linear-gradient(135deg,{c1},{c2});font-family:{font};color:#111}}
.t{{position:absolute;top:24px;left:30px;font-size:22px;font-weight:bold;letter-spacing:1px}}
.photo{{position:absolute;top:80px;left:30px;width:200px;height:250px;background:#cfd6dc;
display:flex;align-items:center;justify-content:center;color:#667;font-size:20px}}
.f{{position:absolute}}
.l{{display:block;font-size:12px;color:#556;margin-bottom:4px}}
.v{{display:inline-block;font-size:22px;font-weight:bold}}
.wm{{position:absolute;top:210px;left:90px;font-size:120px;font-weight:bold;
color:rgba(200,0,0,.16);transform:rotate(-20deg);letter-spacing:6px}}
</style></head><body><div id="card">
<div class="t">PERMIS DE CONDUIRE - SPECIMEN</div>
<div class="photo">PHOTO</div>{blocks}<div class="wm">SPECIMEN</div>
</div></body></html>"""


def main(n=20, seed=0, out="data/synthetic/license"):
    random.seed(seed)
    out = Path(out)
    (out / "images").mkdir(parents=True, exist_ok=True)
    (out / "labels").mkdir(parents=True, exist_ok=True)

    boxes_js = """() => Object.fromEntries(
        [...document.querySelectorAll('[data-field]')].map(e => {
            const r = e.getBoundingClientRect();
            return [e.dataset.field, [r.left, r.top, r.right, r.bottom]];
        }))"""

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 856, "height": 540},
                                device_scale_factor=SCALE)
        for i in range(n):
            rec = make_record()
            page.set_content(build_html(rec))
            boxes = page.evaluate(boxes_js)
            name = f"{i:06d}"
            page.locator("#card").screenshot(path=str(out / "images" / f"{name}.png"))
            label = {
                "fields": rec,
                "boxes": {k: [round(v * SCALE) for v in b] for k, b in boxes.items()},
            }
            (out / "labels" / f"{name}.json").write_text(
                json.dumps(label, ensure_ascii=False, indent=2), encoding="utf-8")
        browser.close()
    print(f"{n} images générées dans {out}")



if __name__ == "__main__":
    main(n=int(sys.argv[1]) if len(sys.argv) > 1 else 20)