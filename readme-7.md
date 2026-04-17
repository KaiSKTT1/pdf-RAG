# 7. HƯỚNG DẪN SỬ DỤNG
## 7.1 Hướng dẫn cho người dùng cuối
### 7.1.1 Khởi động ứng dụng
- Mở terminal hoặc command prompt.
- Di chuyển đến thư mục project bằng lệnh cd đường_dẫn_đến_project.
- Kích hoạt môi trường ảo:
        Trên Mac/Linux: source venv/bin/activate
        Trên Windows: venv\Scripts\activate
- Chạy Streamlit: streamlit run main.py
- Truy cập http://localhost:8501 trong trình duyệt.

### 7.1.2 Upload tài liệu
- Nhấn vào nút "Browse files" hoặc kéo thả file vào vùng upload.
- Chọn file PDF hoặc DOCX từ máy tính.
- Chờ hệ thống xử lý, hiện thông báo "Đã xử lý thành công".
- Xem tiến trình xử lý qua các thông báo: "Đang đọc file...", "Đang chia nhỏ văn bản...", "Đang tạo embeddings...".

### 7.1.3 Đặt câu hỏi
- Sau khi tài liệu được xử lý, nhập câu hỏi vào ô chat.
- Nhấn Enter hoặc nhấn bên ngoài ô nhập.
- Chờ spinner "Đang xử lý..." hiển thị trong quá trình AI suy nghĩ.
- Xem câu trả lời hiển thị trong khung chat.

### 7.1.4 Tips sử dụng
Để câu trả lời chính xác hơn:
- Đặt câu hỏi cụ thể, rõ ràng
- Sử dụng từ khóa có trong document
- Tránh câu hỏi quá chung chung
- Chia câu hỏi phức tạp thành nhiều câu nhỏ

Xử lý lỗi:
- Nếu upload fail: Check file format (phải là PDF)
- Nếu processing lâu: Check file size (nên < 50MB)
- Nếu không có response: Kiểm tra Ollama đang chạy
- Nếu lỗi khác: Xem error message và retry

## 7.2 Hướng dẫn cho developers (Dành cho Gemini API)
### 7.2.1 Cấu hình API key
- Tạo file .env trong thư mục gốc của project: - `GEMINI_KEY=your_api_key_here`    
- Thay your_api_key_here bằng API key lấy từ Google AI Studio (https://aistudio.google.com/apikey).
### 7.2.2 Customize embedding model
- Mở file config.py và sửa dòng EMBEDDING_MODEL:
        `EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"`
- Có thể thay bằng các model khác như:
    - "sentence-transformers/all-MiniLM-L6-v2" (nhẹ hơn, tiếng Anh)
    - "intfloat/multilingual-e5-small" (đa ngôn ngữ, hiệu suất tốt)
### 7.2.3 Adjust chunk parameters
Mở file config.py và sửa các giá trị:
- CHUNK_SIZE = 1000  # Kích thước mỗi chunk (ký tự)
- CHUNK_OVERLAP = 100  # Độ trùng lặp giữa các chunk (ký tự)
Hoặc người dùng có thể điều chỉnh trực tiếp trên UI qua selectbox.
### 7.2.4 Thay đổi model Gemini
- Mở file config.py và sửa dòng GEMINI_MODEL: 
        `GEMINI_MODEL = "gemini-2.5-flash"  # Mặc định `
- Các tùy chọn model Gemini:
    - "gemini-2.5-flash" (nhanh, nhẹ, khuyến nghị)
    - "gemini-1.5-pro" (mạnh hơn, chậm hơn)
    - "gemini-2.0-flash" (phiên bản mới)

### 7.2.5 Modify retrieval parameters
Mở file config.py và sửa các giá trị:
- `TOP_K = 10`  # Số chunk trả về cho bước sinh phản hồi
- `FETCH_K = 30`  # Số chunk ứng viên trước khi xếp hạng
- `SEARCH_TYPE = "similarity"`  # Hoặc "mmr" để đa dạng kết quả```
### 7.2.6 Cài đặt thư viện
Các thư viện cần cài đặt cho Gemini API:
- `pip install google-generativeai langchain-google-genai python-dotenv`

### 7.2.7 Add logging
Để thêm logging cho việc debug, thêm vào đầu file main.py hoặc app.py:

- import logging
- logging.basicConfig(level=logging.INFO)
- logger = logging.getLogger(__name__)

<!-- # Thêm trong các bước xử lý
logger.info(f"Đã xử lý {len(chunks)} chunks")
logger.info(f"Câu hỏi: {question}")
logger.info(f"Đang gọi Gemini API...")
logger.info(f"Đã nhận phản hồi từ Gemini")
7.2.8 Kiểm tra kết nối Gemini API
Chạy lệnh sau để kiểm tra API key hoạt động:

bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Key found:', bool(os.getenv('GEMINI_KEY')))"
Kết quả mong đợi: Key found: True

7.2.9 Xử lý lỗi khi gọi API
Trong code đã tích hợp sẵn xử lý lỗi cho các trường hợp:

DefaultCredentialsError: Không tìm thấy API key

API key not valid: Key sai hoặc hết hạn

Rate limit exceeded: Gửi quá nhiều request (60 requests/phút)

Quota exceeded: Hết quota miễn phí

File liên quan:

services/rag_pdf_service.py

rag/chain.py -->