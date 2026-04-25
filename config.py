"""Khai báo cấu hình tập trung cho ứng dụng PDF RAG.

Toàn bộ tham số runtime được gom tại đây để có thể tinh chỉnh hành vi
ứng dụng mà không cần sửa trực tiếp các module nghiệp vụ.
"""

import os

# ===== LLM / Sinh phản hồi =====
OLLAMA_MODEL = "qwen2.5"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_TEMPERATURE = 0.7
LLM_TOP_P = 0.9
LLM_REPEAT_PENALTY = 1.1
LLM_NUM_PREDICT = 120
LLM_MODEL = OLLAMA_MODEL

# Ưu tiên tốc độ phản hồi cho pha hỏi đáp.
MAX_CONTEXT_CHARS = 3200
TARGET_RESPONSE_SECONDS = 5.0

# ===== Embedding =====
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
EMBEDDING_DEVICE = "cpu"        # Đổi thành "cuda" khi máy có GPU.
EMBEDDING_NORMALIZE = True

# ===== Chia văn bản =====
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNK_SIZE_OPTIONS = [500, 1000, 1500, 2000]
CHUNK_OVERLAP_OPTIONS = [50, 100, 200]

# ===== Retriever =====
SEARCH_TYPE = "similarity"      # Có thể đổi sang "mmr" để đa dạng kết quả.
TOP_K = 3                        # Ưu tiên tốc độ truy xuất + rút gọn prompt.
FETCH_K = 10                     # Giảm ứng viên để hạ độ trễ khi lấy context.

# ===== Upload =====
MAX_UPLOAD_FILE_MB = 200        # Giới hạn dung lượng file upload (MB).

# ===== OCR =====
# Chế độ OCR: "off" (tắt), "auto" (OCR trang khó + vùng ảnh), "force" (OCR toàn bộ).
OCR_MODE_DEFAULT = "auto"
OCR_MODE_OPTIONS = ["off", "auto", "force"]
OCR_MODE_LABELS = {
	"off": "Tắt OCR (chỉ text native)",
	"auto": "Hybrid: OCR trang khó + vùng ảnh",
	"force": "OCR toàn bộ trang PDF",
}

# Ngôn ngữ OCR theo chuẩn EasyOCR.
OCR_LANGUAGES = ["vi", "en"]

# Ngưỡng nhận diện "trang khó" trong chế độ auto.
OCR_MIN_NATIVE_TEXT_CHARS = 60

# DPI khi render trang PDF thành ảnh để OCR.
OCR_RENDER_DPI = 220

# Bật GPU cho EasyOCR nếu môi trường hỗ trợ.
OCR_GPU = False

# Giới hạn số trang được OCR cho mỗi tài liệu để tránh quá tải khi PDF rất lớn.
# Đặt 0 để bỏ giới hạn.
OCR_MAX_PAGES_PER_DOC = 120