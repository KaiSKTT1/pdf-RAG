# 8.2.1 Câu hỏi 1: Thêm hỗ trợ file DOCX

## 1. Mục tiêu

Yêu cầu cần đạt:
- Mở rộng hệ thống để hỗ trợ tải lên và xử lý file DOCX.
- Sử dụng thư viện phù hợp (python-docx hoặc Docx2txtLoader từ LangChain).
- Đảm bảo text extraction chính xác.

## 2. Những gì đã triển khai

### 2.1 Cài đặt thư viện hỗ trợ DOCX

Đã thêm vào file `requirements.txt`:
- docx2txt==0.8
- python-docx==1.1.2

### 2.2 Cập nhật file uploader trên UI
Đã sửa file upload.py để cho phép chọn cả file .docx:
- uploaded_file = st.file_uploader("📂 Chọn file", type=["pdf", "docx"], key=uploader_key)

File liên quan: `ui\components\main_area_parts\upload.py`

### 2.3 Tạo DOCXLoader riêng
Đã tạo file loaders/docx_loader.py chuyên xử lý file DOCX:

Đã dùng Docx2txtLoader từ LangChain để lấy đúng nội dung văn bản:

Lý do chọn Docx2txtLoader:
- Nó dùng thư viện docx2txt bên dưới
- docx2txt được kiểm chứng là đọc text từ DOCX chính xác, kể cả tiếng Việt có dấu
- Giữ được thứ tự đoạn văn, xử lý được bảng đơn giản
File liên quan: `loaders\docx_loader.py`

