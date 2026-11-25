#!/usr/bin/env python3
"""Scan images and save the recognized text into a Word (.docx) file.

Usage:
    python ocr_to_word.py anh1.jpg anh2.png -o ketqua.docx
    python ocr_to_word.py ./thu_muc_anh -o ketqua.docx
"""
import argparse
import re
import sys
from dataclasses import replace
from pathlib import Path

from docx import Document
from PIL import Image, ImageOps

from pipeline import Config, ocr as ocr_with_config

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}

# Cấu hình tìm được qua vòng lặp tinh chỉnh tự động, kiểm chứng trên CẢ ảnh tổng hợp
# (testset/, 100 ảnh: 98.32% chính xác ký tự) LẪN ảnh văn bản thật lấy từ internet
# (real_samples/, 93.34% chính xác ký tự trên văn bản pháp lý dày đặc chữ nhỏ).
# Lưu ý: cấu hình "median denoise" từng thắng trên ảnh tổng hợp lại phá nét chữ nhỏ
# trên ảnh thật (tụt xuống ~14%) nên đã loại bỏ — xem real_samples/tune_log.md.
BEST_CONFIG = Config(upscale=2, denoise="none", threshold="none", deskew=False, psm=6)


def natural_key(path: Path):
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", path.name)]


def collect_images(inputs: list[str]) -> list[Path]:
    images: list[Path] = []
    for item in inputs:
        path = Path(item)
        if path.is_dir():
            images.extend(p for p in path.iterdir() if p.suffix.lower() in IMAGE_EXTS)
        elif path.is_file():
            images.append(path)
        else:
            print(f"Bỏ qua (không tìm thấy): {path}", file=sys.stderr)
    return sorted(images, key=natural_key)


def ocr_image(path: Path, lang: str) -> str:
    image = Image.open(path)
    image = ImageOps.exif_transpose(image)
    config = replace(BEST_CONFIG, lang=lang)
    return ocr_with_config(image, config)


def build_docx(images: list[Path], lang: str, output: Path, with_headers: bool) -> None:
    doc = Document()
    for i, path in enumerate(images):
        print(f"Đang nhận diện ({i + 1}/{len(images)}): {path.name}")
        text = ocr_image(path, lang)

        if with_headers:
            doc.add_heading(path.name, level=2)

        if text:
            for line in text.splitlines():
                doc.add_paragraph(line)
        else:
            doc.add_paragraph("[Không nhận diện được văn bản]")

        if i < len(images) - 1:
            doc.add_page_break()

    doc.save(output)


def main() -> None:
    parser = argparse.ArgumentParser(description="OCR ảnh sang file Word (.docx)")
    parser.add_argument("inputs", nargs="+", help="File ảnh hoặc thư mục chứa ảnh")
    parser.add_argument("-o", "--output", default="output.docx", help="Đường dẫn file .docx đầu ra")
    parser.add_argument("-l", "--lang", default="vie", help="Ngôn ngữ OCR (vd: vie, eng, vie+eng)")
    parser.add_argument("--no-headers", action="store_true", help="Không chèn tên file ảnh làm tiêu đề")
    args = parser.parse_args()

    images = collect_images(args.inputs)
    if not images:
        print("Không tìm thấy ảnh nào để xử lý.", file=sys.stderr)
        sys.exit(1)

    output = Path(args.output)
    build_docx(images, args.lang, output, with_headers=not args.no_headers)
    print(f"Hoàn tất. Đã lưu: {output.resolve()}")


if __name__ == "__main__":
    main()
