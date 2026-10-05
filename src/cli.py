import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.ocr.rapid_engine import OCREngine
from src.parsing.parser import load_config, parse


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python src/cli.py <image> [--raw] [--config chemin.json]")
    lines = OCREngine().read(sys.argv[1])
    if "--raw" in sys.argv:
        result = lines
    else:
        config = load_config(sys.argv[sys.argv.index("--config") + 1]) if "--config" in sys.argv else None
        result = parse(lines, config)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
