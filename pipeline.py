"""Tiền xử lý ảnh + chạy OCR với cấu hình tham số hóa được (để dò/tối ưu)."""
from dataclasses import dataclass, asdict

import cv2
import numpy as np
import pytesseract
from PIL import Image


@dataclass(frozen=True)
class Config:
    upscale: int = 2          # hệ số phóng to ảnh trước khi OCR
    denoise: str = "none"     # none | median | nlmeans
    threshold: str = "none"   # none | otsu | adaptive
    deskew: bool = False
    psm: int = 6
    lang: str = "vie"

    def as_dict(self):
        return asdict(self)


def _deskew(gray: np.ndarray) -> np.ndarray:
    inv = cv2.bitwise_not(gray)
    _, bw = cv2.threshold(inv, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    coords = cv2.findNonZero(bw)
    if coords is None or len(coords) < 20:
        return gray
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    if abs(angle) < 0.1 or abs(angle) > 20:
        return gray  # tránh xoay nhầm khi không có skew rõ ràng
    h, w = gray.shape
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def preprocess(image: Image.Image, config: Config) -> Image.Image:
    arr = np.array(image.convert("L"))

    if config.upscale > 1:
        arr = cv2.resize(arr, None, fx=config.upscale, fy=config.upscale, interpolation=cv2.INTER_CUBIC)

    if config.deskew:
        arr = _deskew(arr)

    if config.denoise == "median":
        arr = cv2.medianBlur(arr, 3)
    elif config.denoise == "nlmeans":
        arr = cv2.fastNlMeansDenoising(arr, h=10)

    if config.threshold == "otsu":
        _, arr = cv2.threshold(arr, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    elif config.threshold == "adaptive":
        arr = cv2.adaptiveThreshold(
            arr, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 15
        )

    return Image.fromarray(arr)


def ocr(image: Image.Image, config: Config) -> str:
    processed = preprocess(image, config)
    tess_config = f"--oem 1 --psm {config.psm}"
    return pytesseract.image_to_string(processed, lang=config.lang, config=tess_config).strip()
