"""Sinh bộ ảnh test đa dạng (nhiều font, mô phỏng ảnh scan thật) kèm ground-truth
để đo độ chính xác OCR một cách khách quan, lặp lại được."""
import io
import json
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from corpus import SAMPLES

FONTS = [
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/HelveticaNeue.ttc",
]

OUT_DIR = Path("testset")
random.seed(42)
np.random.seed(42)


def render_clean(text: str, font_path: str, font_size: int = 40) -> Image.Image:
    font = ImageFont.truetype(font_path, font_size)
    # đo kích thước cần thiết
    dummy = Image.new("L", (10, 10))
    d = ImageDraw.Draw(dummy)
    bbox = d.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0] + 80
    h = bbox[3] - bbox[1] + 80
    img = Image.new("L", (w, h), 255)
    d = ImageDraw.Draw(img)
    d.text((40, 40), text, font=font, fill=0)
    return img.convert("RGB")


def add_noise(img: Image.Image, amount: float) -> Image.Image:
    arr = np.array(img).astype(np.int16)
    noise = np.random.normal(0, amount, arr.shape)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def jpeg_compress(img: Image.Image, quality: int) -> Image.Image:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def degrade_light(img: Image.Image) -> Image.Image:
    img = img.rotate(random.uniform(-1.5, 1.5), expand=True, fillcolor=(255, 255, 255))
    img = img.filter(ImageFilter.GaussianBlur(0.4))
    img = add_noise(img, 5)
    return jpeg_compress(img, 85)


def degrade_heavy(img: Image.Image) -> Image.Image:
    img = img.rotate(random.uniform(-4, 4), expand=True, fillcolor=(255, 255, 255))
    img = img.filter(ImageFilter.GaussianBlur(1.1))
    img = add_noise(img, 14)
    # ánh sáng không đều: thêm gradient sáng/tối nhẹ
    w, h = img.size
    gradient = np.tile(np.linspace(-20, 20, w), (h, 1)).astype(np.int16)
    arr = np.array(img).astype(np.int16)
    arr = np.clip(arr + gradient[:, :, None], 0, 255).astype(np.uint8)
    img = Image.fromarray(arr)
    return jpeg_compress(img, 55)


def degrade_lowres(img: Image.Image) -> Image.Image:
    w, h = img.size
    small = img.resize((max(1, w // 3), max(1, h // 3)), Image.BILINEAR)
    back = small.resize((w, h), Image.BILINEAR)
    return jpeg_compress(back, 70)


VARIANTS = {
    "clean": lambda img: img,
    "light": degrade_light,
    "heavy": degrade_heavy,
    "lowres": degrade_lowres,
}


def main():
    OUT_DIR.mkdir(exist_ok=True)
    ground_truth = {}
    for i, text in enumerate(SAMPLES):
        font_path = FONTS[i % len(FONTS)]
        base = render_clean(text, font_path)
        for variant_name, fn in VARIANTS.items():
            img = fn(base.copy())
            filename = f"{i:02d}_{variant_name}.jpg"
            img.convert("RGB").save(OUT_DIR / filename, quality=90)
            ground_truth[filename] = text

    with open(OUT_DIR / "ground_truth.json", "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, ensure_ascii=False, indent=2)

    print(f"Đã sinh {len(ground_truth)} ảnh test vào {OUT_DIR}/")


if __name__ == "__main__":
    main()
