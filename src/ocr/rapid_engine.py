import sys
from rapidocr_onnxruntime import RapidOCR


class OCREngine:
    def __init__(self):
        self.ocr = RapidOCR()

    def read(self, path, verbose=False):
        """Retourne [{text, score, box=[x1,y1,x2,y2]}], tries de haut en bas puis de gauche a droite."""
        result, _ = self.ocr(path)
        lines = []
        for poly, text, score in result or []:
            xs = [p[0] for p in poly]
            ys = [p[1] for p in poly]
            lines.append({
                "text": text,
                "score": float(score),
                "box": [float(min(xs)), float(min(ys)), float(max(xs)), float(max(ys))],
            })
        lines.sort(key=lambda l: (l["box"][1], l["box"][0]))
        if verbose:
            for l in lines:
                print(f'{l["score"]:.2f}  {l["text"]}')
        return lines


if __name__ == "__main__":
    OCREngine().read(sys.argv[1], verbose=True)
