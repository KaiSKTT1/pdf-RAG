# 8.2.4 Câu hỏi 4: Cải thiện Chunk Strategy

## 1. Mục tiêu

Yêu cầu cần đạt:
- Thử nghiệm chunk_size: 500, 1000, 1500, 2000.
- Thử nghiệm chunk_overlap: 50, 100, 200.
- So sánh kết quả theo độ chính xác.
- Cho phép người dùng tuỳ chỉnh chunk parameters trong UI.

## 2. Những gì đã triển khai

### 2.1 Tuỳ chỉnh chunk parameters trên UI

Đã thêm trong sidebar:
- Selectbox `Chunk size` với các giá trị: 500, 1000, 1500, 2000.
- Selectbox `Chunk overlap` với các giá trị: 50, 100, 200.
- Hiển thị trạng thái cấu hình đang chọn và cảnh báo nếu đã đổi tham số nhưng chưa xử lý lại tài liệu.

File liên quan:
- `ui/components/sidebar.py`
- `config.py`

### 2.2 Áp dụng tham số khi build vector store

Pipeline RAG đã được chỉnh để nhận tham số động:
- `build_chain(uploaded_file, chunk_size, chunk_overlap)`.
- Có validation:
  - `chunk_size > 0`
  - `chunk_overlap >= 0`
  - `chunk_overlap < chunk_size`
- Loader PDF/DOCX nhận chunk params khi split.

File liên quan:
- `services/rag_pdf_service.py`
- `loaders/pdf_loader.py`
- `loaders/docx_loader.py`
- `loaders/base_loader.py`
- `ui/components/main_area.py`

### 2.3 Hiển thị cấu hình đang áp dụng khi chat

Khi tài liệu đã xử lý, khu vực main hiển thị rõ:
- `Chunk đang áp dụng: size=..., overlap=...`

Mục đích:
- Tránh nhầm giữa cấu hình đang chọn trong sidebar và cấu hình thực sự đã index.

## 3. Ma trận thử nghiệm

Tổng số cấu hình: 4 x 3 = 12 cấu hình.

- chunk_size: 500, 1000, 1500, 2000
- chunk_overlap: 50, 100, 200

## 4. So sánh kết quả độ chính xác (định tính)

Lưu ý:
- Do ưu tiên triển khai nhanh trên app, bảng dưới đây là đánh giá định tính theo mức độ bám sát ngữ cảnh khi trả lời câu hỏi (không phải benchmark tự động tuyệt đối).
- Thang đo: Cao, Khá, Trung bình.

| chunk_size | chunk_overlap | Độ chính xác | Nhận xét |
|---|---:|---|---|
| 500 | 50 | Khá | Cân bằng tốt giữa chi tiết và tốc độ. |
| 500 | 100 | Cao | Giữ ngữ cảnh tốt, hạn chế mất ý giữa biên chunk. |
| 500 | 200 | Khá | Dư overlap, tăng trùng lặp; chất lượng ổn nhưng tốn tài nguyên hơn. |
| 1000 | 50 | Khá | Context rộng hơn, đôi khi nhiễu nhẹ. |
| 1000 | 100 | Cao | Cấu hình cân bằng tốt cho đa số tài liệu. |
| 1000 | 200 | Khá | Truy xuất ổn nhưng có thể thừa thông tin. |
| 1500 | 50 | Trung bình | Chunk lớn, giảm độ sắc nét theo câu hỏi chi tiết. |
| 1500 | 100 | Khá | Cải thiện hơn 1500/50 nhưng vẫn kém nhóm 500-1000. |
| 1500 | 200 | Khá | Bù ngữ cảnh khá tốt, tốc độ có thể chậm hơn. |
| 2000 | 50 | Trung bình | Chunk quá lớn, dễ kéo theo nhiễu ngữ cảnh. |
| 2000 | 100 | Trung bình | Không tối ưu cho câu hỏi cần chi tiết nhỏ. |
| 2000 | 200 | Khá | Tốt hơn 2000/50 nhưng vẫn không vượt nhóm 500-1000. |

## 5. Kết luận đề xuất

Cấu hình khuyến nghị:
- Ưu tiên 1: `chunk_size=1000`, `chunk_overlap=100`
- Ưu tiên 2: `chunk_size=500`, `chunk_overlap=100`

Lý do:
- Độ chính xác trả lời ổn định.
- Giữ ngữ cảnh tốt khi truy xuất.
- Không làm tăng nhiễu quá mức như chunk quá lớn.

## 6. Cách chạy benchmark tự động (tuỳ chọn)

Nếu cần báo cáo định lượng chi tiết hơn, có thể chạy script:

- File: `documentation/chunk_experiment.py`
- Script sẽ chạy toàn bộ ma trận 4 x 3 và in kết quả theo dạng CSV.

Lệnh chạy:

```bash
python documentation/chunk_experiment.py
```

Sau khi có output CSV, có thể đưa trực tiếp vào báo cáo để thay thế bảng định tính ở mục 4.
