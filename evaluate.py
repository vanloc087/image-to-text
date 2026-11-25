"""Đo độ chính xác OCR (theo ký tự và theo từ) trên bộ testset/ground_truth.json."""
import json
import re
from pathlib import Path

import Levenshtein
from PIL import Image

from pipeline import Config, ocr

TESTSET_DIR = Path("testset")


def normalize(text: str) -> str:
    text = text.replace("\n", " ")
    return re.sub(r"\s+", " ", text).strip()


def char_accuracy(gt: str, pred: str) -> float:
    gt, pred = normalize(gt), normalize(pred)
    if not gt:
        return 1.0 if not pred else 0.0
    dist = Levenshtein.distance(gt, pred)
    return max(0.0, 1 - dist / len(gt))


def word_accuracy(gt: str, pred: str) -> float:
    gt_words, pred_words = normalize(gt).split(), normalize(pred).split()
    if not gt_words:
        return 1.0 if not pred_words else 0.0
    dist = Levenshtein.distance(gt_words, pred_words)
    return max(0.0, 1 - dist / len(gt_words))


def load_ground_truth() -> dict:
    with open(TESTSET_DIR / "ground_truth.json", encoding="utf-8") as f:
        return json.load(f)


def evaluate(config: Config, filenames=None, verbose: bool = False):
    gt_map = load_ground_truth()
    if filenames is None:
        filenames = list(gt_map.keys())

    char_accs, word_accs = [], []
    per_variant = {}
    for filename in filenames:
        gt = gt_map[filename]
        img = Image.open(TESTSET_DIR / filename)
        pred = ocr(img, config)
        ca = char_accuracy(gt, pred)
        wa = word_accuracy(gt, pred)
        char_accs.append(ca)
        word_accs.append(wa)

        variant = filename.split("_", 1)[1].rsplit(".", 1)[0]
        per_variant.setdefault(variant, []).append(ca)

        if verbose:
            print(f"[{filename}] char_acc={ca:.2%} word_acc={wa:.2%}")
            print(f"  GT : {gt}")
            print(f"  OCR: {pred}")

    result = {
        "char_accuracy": sum(char_accs) / len(char_accs),
        "word_accuracy": sum(word_accs) / len(word_accs),
        "per_variant": {k: sum(v) / len(v) for k, v in per_variant.items()},
        "n": len(filenames),
    }
    return result


if __name__ == "__main__":
    cfg = Config()
    res = evaluate(cfg, verbose=False)
    print("Config:", cfg.as_dict())
    print(f"Char accuracy: {res['char_accuracy']:.2%}")
    print(f"Word accuracy: {res['word_accuracy']:.2%}")
    print("Theo biến thể:", {k: f"{v:.2%}" for k, v in res["per_variant"].items()})
