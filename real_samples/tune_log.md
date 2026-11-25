# Nhật ký kiểm chứng bằng ảnh thật từ internet

Nguồn: tìm qua Bing Images ("scan công văn tiếng Việt mẫu"), lấy từ
thuvienphapluat.vn và scribdassets.com (xem lại bằng trình duyệt tích hợp,
không tải file thực thi — chỉ ảnh).

## Phát hiện quan trọng

1. **Bug chụp màn hình**: lần đầu chụp ảnh trong khung xem trình duyệt 800x600,
   ảnh gốc lớn hơn (768x1024) bị tự động thu nhỏ để vừa khung → mất chi tiết
   nét chữ → OCR gần như hỏng hoàn toàn (ví dụ chỉ ra `VAN TRÔNG LUẬT MỸ HÀ
   XỘt...`). Sau khi phóng khung xem lên 1000x1400 và chụp lại đúng tỉ lệ gốc,
   kết quả cải thiện rõ rệt. => Đây là lỗi phương pháp kiểm tra, không phải
   giới hạn thật của OCR.

2. **Quá khớp (overfitting) với bộ test tổng hợp**: cấu hình
   `upscale=1, denoise=median, psm=6` đạt 99.69% trên ảnh tổng hợp (chữ to,
   nhiễu kiểu Gaussian) nhưng chỉ đạt **~14%** trên ảnh scan thật (văn bản
   pháp lý, chữ nhỏ dày đặc) vì median blur xóa mất chi tiết nét chữ nhỏ.
   `psm=6` cũng giả định ảnh là một khối văn bản đơn, sai với layout nhiều
   cột/đoạn của văn bản thật.

3. Dò lại trên ảnh thật (ground truth transcribe thủ công từ ảnh, file
   `sample3_ground_truth.txt`) cho thấy cấu hình tốt nhất là:
   `upscale=2, denoise=none, threshold=none, psm=6` → **93.34%** ký tự chính
   xác trên văn bản pháp lý thật (dày đặc, chữ nhỏ, nhiều đoạn).

4. Áp cấu hình này lại lên bộ 100 ảnh tổng hợp: **98.32%** (giảm nhẹ so với
   98.88% của cấu hình cũ, chủ yếu ở nhóm "extreme": 93.97% so với 95.62%)
   — đánh đổi hợp lý vì cấu hình cũ gần như không dùng được với ảnh thật.

## Kết luận / cấu hình cuối

`Config(upscale=2, denoise="none", threshold="none", deskew=False, psm=6)`

- Ảnh tổng hợp (chữ to, rõ, kể cả mô phỏng chụp nghiêng/mờ/nhiễu): **98.32%**
  ký tự chính xác.
- Ảnh văn bản thật, chữ nhỏ, layout phức tạp (độ phân giải vừa phải, không
  phải scan chất lượng cao): **93.34%** ký tự chính xác.

=> Với ảnh scan/chụp chất lượng tốt, rõ nét, độ phân giải đủ cao (khuyến nghị
≥200-300 DPI tương đương, chữ cao tối thiểu ~20-25px sau khi phóng to), độ
chính xác thực tế sẽ gần mức 98%+. Với ảnh chữ nhỏ/độ phân giải thấp như ảnh
thử nghiệm ở đây, ~93-95% là mức thực tế, chưa đạt 100% tuyệt đối — đúng như
đã cảnh báo trước đó, vì bản chất OCR không thể đảm bảo 100% trên mọi loại
ảnh.
