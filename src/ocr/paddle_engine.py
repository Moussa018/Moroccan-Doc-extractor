import os
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"  # skip slow connectivity check

from paddleocr import PaddleOCR
import sys

def run(path, lang="fr"):
    ocr = PaddleOCR(
        lang=lang,
        enable_mkldnn=False,              # fixes the oneDNN NotImplementedError on CPU
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
    )
    results = ocr.predict(path)
    for res in results:
        for text, score in zip(res["rec_texts"], res["rec_scores"]):
            print(f"{score:.2f}  {text}")
        res.save_to_img("output/")
if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "fr")