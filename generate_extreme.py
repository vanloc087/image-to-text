"""Thêm biến thể 'extreme' (ảnh chụp nghiêng góc, méo phối cảnh, nhiễu nặng, mờ, nén mạnh)
để kiểm tra độ chính xác trong điều kiện khắc nghiệt hơn, giống ảnh chụp điện thoại thực tế."""
import json
import random
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from corpus import SAMPLES
from generate_testset import FONTS, render_clean, add_noise, jpeg_compress

OUT_DIR = Path("testset")
random.seed(7)
np.random.seed(7)


def perspective_warp(img: Image.Image, strength: float = 0.06) -> Image.Image:
    arr = np.array(img)
    h, w = arr.shape[:2]
    src = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
    jitter = lambda: random.uniform(-strength, strength)
    dst = np.float32([
        [jitter() * w, jitter() * h],
        [w + jitter() * w, jitter() * h],
        [jitter() * w, h + jitter() * h],
        [w + jitter() * w, h + jitter() * h],
    ])
    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(arr, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))
    return Image.fromarray(warped)


def degrade_extreme(img: Image.Image) -> Image.Image:
    img = img.rotate(random.uniform(-6, 6), expand=True, fillcolor=(255, 255, 255))
    img = perspective_warp(img, strength=0.05)
    arr = np.array(img)
    arr = cv2.GaussianBlur(arr, (3, 3), 0.9)
    img = Image.fromarray(arr)
    img = add_noise(img, 20)
    w, h = img.size
    gradient = np.tile(np.linspace(-35, 35, w), (h, 1)).astype(np.int16)
    arr = np.array(img).astype(np.int16)
    arr = np.clip(arr + gradient[:, :, None], 0, 255).astype(np.uint8)
    img = Image.fromarray(arr)
    return jpeg_compress(img, 40)


def main():
    gt_path = OUT_DIR / "ground_truth.json"
    ground_truth = json.loads(gt_path.read_text(encoding="utf-8"))

    for i, text in enumerate(SAMPLES):
        font_path = FONTS[i % len(FONTS)]
        base = render_clean(text, font_path)
        img = degrade_extreme(base.copy())
        filename = f"{i:02d}_extreme.jpg"
        img.convert("RGB").save(OUT_DIR / filename, quality=85)
        ground_truth[filename] = text

    gt_path.write_text(json.dumps(ground_truth, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Đã thêm {len(SAMPLES)} ảnh 'extreme'. Tổng cộng: {len(ground_truth)} ảnh trong testset/")


if __name__ == "__main__":
    main()
