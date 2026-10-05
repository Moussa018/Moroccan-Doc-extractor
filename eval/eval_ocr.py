import os
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

import json 
import sys
from collections import defaultdict
from pathlib import Path

from paddleocr import paddleOCR 


DATA = Path("/data/synthetic/lisence")

MARGIN = 10

def levenshtein(a,b):
    if a == b : 
        return 0
    prev = list(range(len(b) + 1 ))
    for i , ca in enumerate(a,1):
        cur = [i]
        for j , cb in enumerate(b,1):
            cur.append(min(prev[j]+1 , cur[j-1] + 1 , prev[j-1] + (ca!=cb)))
        prev = curr
    return prev[-1]

def norm(s):
    return " ".join(s.split())

 """Retourne [(texte, [x1,y1,x2,y2]), ...] pour une image."""
def get_lines(res):
    text = res["rec_texts"]
    boxes = res.get("rec_boxes")
    if boxes is None or len(boxes) == 0 :
        boxes = []
        for poly in res["rec_polys"]:
            xs = [p[0] for p in poly]
            ys = [p[1] for p in poly]
            boxes.append([min(xs), min(ys), max(xs), max(ys)])
        return [(t, [float(v) for v in b]) for t , b in zip(texts, boxes)]

def read_fields(lines , gt_boxes):
    out = {}

    for key , {x1,y1,x2,y2} in gt_boxes.items():
        hits = []
        for text , b in lines :
            cx, cy = (b[0]+b[2])/2 , (b[1]+b[3])/2
            if x1 - MARGIN <= cx <=x2 + MARGIN and y1-MARGIN <= y2 <= y1 + MARGIN:
                hits.append((b[0], text))
        out[key] = norm(" ".join(t for _ , t in sorted(hits)))
    return out 
    
def main(n=20, lang="fr"):
    ocr = PaddleOCR(
        lang=lang,
        enable_mkldnn=False,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
    )

    images = sorted((DATA / "images").glob("*.png"))[:n]
    exact = defaultdict(int)
    edits = defaultdict(int)
    chars = defaultdict(int)
    total = defaultdict(int)
    errors = []

    for img in images:
        label = json.loads((DATA / "labels" / f"{img.stem}.json").read_text(encoding="utf-8"))
        results = list(ocr.predict(str(img)))
        lines = get_lines(results[0])
        pred = read_fields(lines, label["boxes"])

        for key, gt in label["fields"].items():
            p = pred.get(key, "")
            total[key] += 1
            chars[key] += len(gt)
            edits[key] += levenshtein(gt, p)
            if norm(gt) == p:
                exact[key] += 1
            else:
                errors.append({"image": img.name, "field": key, "expected": gt, "got": p})
        print(f"{img.name} traité")

    print(f"\n{'champ':<14}{'exact':>8}{'CER':>8}")
    all_exact = all_total = all_edits = all_chars = 0
    for key in total:
        print(f"{key:<14}{100 * exact[key] / total[key]:>7.1f}%{100 * edits[key] / chars[key]:>7.1f}%")
        all_exact += exact[key]
        all_total += total[key]
        all_edits += edits[key]
        all_chars += chars[key]
    print(f"{'GLOBAL':<14}{100 * all_exact / all_total:>7.1f}%{100 * all_edits / all_chars:>7.1f}%")

    Path("output").mkdir(exist_ok=True)
    Path("output/eval_errors.json").write_text(
        json.dumps(errors, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{len(errors)} erreurs sauvegardées dans output/eval_errors.json")
    for e in errors[:10]:
        print(f'  {e["image"]} {e["field"]}: attendu "{e["expected"]}" / lu "{e["got"]}"')


if __name__ == "__main__":
    main(n=int(sys.argv[1]) if len(sys.argv) > 1 else 20)