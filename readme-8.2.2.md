# 8.2.2 Câu hỏi 2: Lưu trữ lịch sử hội thoại
## 1. Mục tiêu

Yêu cầu cần đạt:
- Lưu trữ các câu hỏi và câu trả lời trong session.
- Hiển thị lịch sử chat trong sidebar.
-Cho phép người dùng xem lại các câu hỏi đã hỏi.

## 2. Những gì đã triển khai

### 2.1 Lưu trữ lịch sử trong session state

Đã tạo cấu trúc chat_history trong st.session_state để lưu trữ toàn bộ câu hỏi và câu trả lời. Mỗi khi người dùng đặt câu hỏi và nhận phản hồi, hệ thống tự động thêm một bản ghi mới vào danh sách lịch sử.

File liên quan:
- `ui/components/session_state.py`
- `ui/streamlit_app.py`

### 2.2 Component hiển thị lịch sử chat

Đã tạo component chat_history.py chuyên trách hiển thị lịch sử ở sidebar.

 Component này có nhiệm vụ:
- Đọc danh sách lịch sử từ session state.
- Hiển thị thông báo nếu chưa có câu hỏi nào.
- Xây dựng danh sách câu hỏi dạng selectbox để người dùng chọn.
- Tự động cắt ngắn câu hỏi dài (trên 60 ký tự) để giao diện gọn gàng.
- Khi người dùng chọn một câu hỏi, hiển thị lại nội dung câu hỏi và câu trả lời tương ứng.

File liên quan:
- `ui/components/chat_history.py`

### 2.3 Tích hợp vào sidebar
Đã gọi component render_chat_history() trong sidebar để lịch sử chat luôn hiển thị bên cạnh giao diện chính.

File liên quan:
- `ui/components/sidebar.py`

## 3. Ma trận thử nghiệm
Lưu ý:
- Do ưu tiên triển khai nhanh trên app, bảng dưới đây là đánh giá định tính theo mức độ bám sát ngữ cảnh khi trả lời câu hỏi (không phải benchmark tự động tuyệt đối).
- Thang đo: Cao, Khá, Trung bình.

| tình huống | hành vi kì vọng| kết quả |
|---|---:|---|
| Chưa có câu hỏi nào | Hiển thị thông báo "Chưa có câu hỏi nào" | ✅ Đạt |
| Hỏi 1 câu| Danh sách hiển thị 1 câu hỏi | ✅ Đạt |
| Hỏi nhiều câu| Danh sách hiển thị đầy đủ, đánh số thứ tự | ✅ Đạt |
| Câu hỏi quá dài | Tự động cắt ngắn, thêm dấu "..." | ✅ Đạt|
| Chọn câu hỏi trong danh sách | Hiển thị lại câu hỏi và câu trả lời |  ✅ Đạt |
| Xem câu trả lời | Mở rộng được để đọc toàn bộ nội dung| ✅ Đạt |

## 4. Kết luận
Tính năng lưu trữ lịch sử hội thoại đã hoàn thành với các kết quả:
- Toàn bộ câu hỏi và câu trả lời được lưu trong session.
- Lịch sử hiển thị trực quan ở sidebar dưới dạng selectbox.
- Người dùng có thể dễ dàng xem lại bất kỳ câu hỏi nào đã hỏi.
- Giao diện gọn gàng nhờ tự động cắt câu hỏi dài.

## 5. Cách kiểm tra
Chạy ứng dụng, upload tài liệu, sau đó hỏi liên tiếp nhiều câu. Quan sát sidebar thấy danh sách câu hỏi hiện ra. Lần lượt chọn từng câu để kiểm tra xem câu trả lời có hiển thị đúng không.

