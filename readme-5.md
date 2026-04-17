# 5. GIAO DIỆN NGƯỜI DÙNG
## 5.1 Thiết kế UI/UX
### 5.1.1 Bố cục tổng thể
Giao diện được chia làm hai phần chính:
- Sidebar (Thanh bên trái): Chứa các thành phần cấu hình và lịch sử chat.
- Main area (Khu vực chính): Chứa vùng upload file và khu vực đặt câu hỏi.

### 5.1.2 Thành phần trên Sidebar
Phần upload file:
- Khu vực drag and drop để tải file lên.
- Hỗ trợ định dạng PDF và DOCX.
- Giới hạn kích thước file 200MB.
- Hiển thị thông báo khi upload thành công hoặc thất bại.
Phần Chunk Strategy:
- Selectbox chọn Chunk size với các giá trị 500, 1000, 1500, 2000.
- Selectbox chọn Chunk overlap với các giá trị 50, 100, 200.
- Hiển thị cảnh báo khi thay đổi tham số nhưng chưa xử lý lại tài liệu.
Phần Lịch sử chat:
- Hiển thị danh sách các câu hỏi đã hỏi dạng selectbox.
- Tự động cắt ngắn câu hỏi dài (trên 60 ký tự).
- Khi chọn câu hỏi, hiển thị lại câu hỏi và câu trả lời tương ứng.
- Hiển thị thông báo "Chưa có câu hỏi nào" nếu lịch sử trống.

### 5.1.3 Thành phần trên Main Area
Vùng upload file:
- Khu vực drag and drop để tải file.
- Hiển thị giới hạn dung lượng (200MB) và định dạng hỗ trợ (PDF, DOCX).
- Hiển thị thông báo sau khi xử lý tài liệu thành công.
Khu vực đặt câu hỏi:
- Ô nhập câu hỏi dạng chat input.
- Hiển thị lịch sử hỏi đáp dạng tin nhắn (user và assistant).
- Spinner hiển thị trong lúc AI đang xử lý.

## 5.2 User Flow
Người dùng tương tác với ứng dụng theo các bước sau:
- Landing: Người dùng thấy giao diện chính với vùng upload file và sidebar cấu hình.
- Upload: Người dùng kéo thả hoặc chọn file PDF/DOCX để tải lên.
- Processing: Hệ thống xử lý tài liệu (đọc file, chia chunk, tạo embeddings, lưu vector store). Hiển thị thông báo tiến trình.
- Configure (tùy chọn): Người dùng có thể điều chỉnh chunk size và chunk overlap trong sidebar.
- Query: Người dùng nhập câu hỏi vào ô chat.
- Response: Hệ thống tìm kiếm và sinh câu trả lời, hiển thị trong khung chat.
- Iterate: Người dùng có thể đặt thêm nhiều câu hỏi, lịch sử tự động lưu lại.
- Review: Người dùng có thể xem lại lịch sử chat trong sidebar.
- Clear (tùy chọn): Người dùng có thể xóa lịch sử hoặc xóa tài liệu đã upload.

## 5.3 Thành phần tương tác
### 5.3.1 File Upload
- Hỗ trợ định dạng: PDF, DOCX.
- Giới hạn dung lượng: 200MB.
- Giao diện drag and drop hoặc nhấn chọn file.
- Hiển thị thông báo thành công hoặc lỗi (sai định dạng, quá dung lượng).

### 5.3.2 Question Answering
- Ô nhập câu hỏi dạng chat input.
- Xử lý theo thời gian thực khi nhấn Enter.
- Hiển thị spinner "Đang xử lý..." trong lúc AI suy nghĩ.
- Hiển thị câu trả lời dạng chat message, phân biệt user và assistant.
### 5.3.5 Error Handling
- Hiển thị thông báo lỗi khi file không đúng định dạng.
- Hiển thị thông báo lỗi khi kết nối API thất bại.
- Hiển thị thông báo lỗi khi không tìm thấy câu trả lời.
- Dialog xác nhận trước khi xóa dữ liệu.