# 8.2.3 Câu hỏi 3: Thêm nút xóa lịch sử
## 1. Mục tiêu

Yêu cầu cần đạt:
- Thêm button "Clear History" để xóa toàn bộ lịch sử chat.
- Thêm button "Clear Vector Store" để xóa tài liệu đã upload.
- Có confirmation dialog trước khi xóa.

## 2. Những gì đã triển khai
### 2.1 Thêm nút xóa lịch sử chat trong sidebar
Đã thêm button "Clear History" ở khu vực sidebar. Khi người dùng nhấn vào, toàn bộ danh sách câu hỏi và câu trả lời trong session sẽ bị xóa sạch, giao diện chat trở về trạng thái ban đầu.

File liên quan:
- `ui/components/sidebar.py`

### 2.2 Thêm nút xóa vector store
Đã thêm button "Clear Vector Store" để xóa vector database (FAISS index) đang lưu trữ. Sau khi xóa, người dùng cần upload lại tài liệu nếu muốn tiếp tục hỏi.

File liên quan:
- `ui/components/sidebar.py`
- `services/rag_pdf_service.py`

### 2.3 Thêm confirmation dialog
Đã tích hợp cơ chế xác nhận trước khi xóa. Khi người dùng nhấn nút xóa, một hộp thoại hiện ra hỏi lại "Bạn có chắc chắn muốn xóa?" với hai lựa chọn "Xóa" và "Hủy". Điều này tránh việc xóa nhầm dữ liệu.

File liên quan:
- `ui/components/sidebar.py`

<!-- ### 2.4 Xóa đồng bộ nhiều thành phần (())
Khi người dùng xóa lịch sử, hệ thống đồng thời xóa:
- Danh sách chat_history (các câu hỏi và câu trả lời).
- Biến vector_store (dữ liệu vector của tài liệu đã upload).
- Biến selected_history_idx (trạng thái đang chọn trong lịch sử).
Điều này đảm bảo ứng dụng trở về trạng thái sạch sẽ như lúc mới khởi động.

File liên quan:
- `ui/components/sidebar.py`
- `ui/components/session_state.py` -->

### 2.5 Thông báo sau khi xóa
Sau khi xóa thành công, hệ thống hiển thị thông báo "Đã xóa lịch sử" hoặc "Đã xóa tài liệu" để người dùng biết thao tác đã hoàn tất.

File liên quan:
- `ui/components/sidebar.py`

## 3. Ma trận thử nghiệm
Tình huống	|Hành vi kỳ vọng|  Kết quả
Nhấn "Xóa lịch sử chat"|	Hiện dialog xác nhận	|✅ Đạt
Chọn "Hủy"	|Đóng dialog, không xóa gì|	✅ Đạt
Chọn "Xóa"	|Xóa hết câu hỏi và câu trả lời|	✅ Đạt
Xóa khi chưa có lịch sử	|Thông báo không có gì để xóa|	✅ Đạt
Nhấn "Xóa tài liệu đã upload"|	Xóa vector store, cần upload lại	|✅ Đạt
Xóa tài liệu rồi hỏi tiếp	|Báo lỗi yêu cầu upload lại|	✅ Đạt
Xóa cả hai	|Ứng dụng về trạng thái ban đầu	|✅ Đạt

## 4. Kết luận
Tính năng xóa lịch sử đã hoàn thành với các kết quả:
- Người dùng có thể xóa toàn bộ lịch sử chat chỉ bằng một nút bấm.
- Có thể xóa riêng tài liệu đã upload mà không ảnh hưởng đến lịch sử.
- Dialog xác nhận giúp tránh thao tác xóa nhầm.
- Thông báo rõ ràng sau mỗi hành động xóa.

## 5. Cách kiểm tra
Chạy ứng dụng, upload tài liệu, hỏi vài câu. Sau đó:

Nhấn nút "Clear History" → Chọn "Xóa" → Kiểm tra sidebar thấy lịch sử trống.

Nhấn nút "Clear Vector Store" → Thử đặt câu hỏi → Hệ thống báo cần upload lại.

Thử nhấn xóa rồi chọn "Hủy" → Dữ liệu vẫn còn nguyên.

