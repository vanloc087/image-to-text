# OCR ảnh sang Word (Tiếng Việt)

Script dòng lệnh (CLI) dùng Tesseract OCR để quét ảnh (ảnh chụp/scan tài liệu
tiếng Việt) và lưu kết quả nhận diện vào file Word (.docx). Chạy hoàn toàn
offline, miễn phí.

## Cài đặt

1. Cài Tesseract (qua Homebrew) kèm gói ngôn ngữ tiếng Việt:

   ```bash
   brew install tesseract
   ```

2. Tạo virtualenv và cài thư viện Python:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## Cách dùng

```bash
source venv/bin/activate

# OCR nhiều file ảnh, gộp vào 1 file Word
python3 ocr_to_word.py anh1.jpg anh2.png -o ketqua.docx

# OCR cả một thư mục ảnh (sắp xếp theo tên)
python3 ocr_to_word.py ./thu_muc_anh -o ketqua.docx
```

### Tuỳ chọn

| Tham số | Ý nghĩa |
|---|---|
| `inputs` | 1 hoặc nhiều file ảnh, hoặc 1 thư mục chứa ảnh |
| `-o`, `--output` | Đường dẫn file Word xuất ra (mặc định `output.docx`) |
| `-l`, `--lang` | Ngôn ngữ OCR (mặc định `vie`; có thể dùng `eng` hoặc `vie+eng`) |
| `--no-headers` | Không chèn tên file ảnh làm tiêu đề trong file Word |

## Cấu trúc dự án

- `ocr_to_word.py` — script chính (CLI).
- `pipeline.py` — tiền xử lý ảnh (resize, khử nhiễu, threshold, deskew) và gọi Tesseract.
- `corpus.py`, `generate_testset.py`, `generate_extreme.py` — sinh bộ ảnh tổng hợp có ground truth để đo độ chính xác.
- `evaluate.py` — tính độ chính xác ký tự/từ (so với ground truth).
- `tune.py` — dò tham số tự động (coordinate ascent) để tối ưu độ chính xác.
- `testset/` — 100 ảnh tổng hợp kèm `ground_truth.json`.
- `real_samples/tune_log.md` — nhật ký kiểm chứng bằng ảnh thật, bài học về overfitting và độ phân giải ảnh.

## Độ chính xác

Cấu hình hiện tại (`upscale=2, denoise=none, threshold=none, psm=6`) đạt:

- **~98.3%** độ chính xác ký tự trên bộ ảnh tổng hợp (`testset/`).
- **~93.3%** độ chính xác ký tự trên ảnh văn bản pháp lý thật, chữ nhỏ dày đặc.

Độ chính xác thực tế phụ thuộc nhiều vào độ phân giải/độ rõ nét của ảnh đầu
vào (khuyến nghị tương đương ≥200–300 DPI). OCR không đảm bảo 100% chính xác
trên mọi loại ảnh.
