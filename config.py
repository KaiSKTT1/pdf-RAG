"""Khai báo cấu hình tập trung cho ứng dụng PDF RAG.

Toàn bộ tham số runtime được gom tại đây để có thể tinh chỉnh hành vi
ứng dụng mà không cần sửa trực tiếp các module nghiệp vụ.
"""

import os

# ===== LLM / Sinh phản hồi =====
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_API_KEY = os.getenv("GEMINI_KEY")
LLM_TEMPERATURE = 0.7
LLM_TOP_P = 0.9
LLM_REPEAT_PENALTY = 1.1
LLM_MODEL = GEMINI_MODEL

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
TOP_K = 10                       # Số chunk trả về cho bước sinh phản hồi.
FETCH_K = 30                     # Số chunk ứng viên trước khi xếp hạng/lọc.

# ===== Upload =====
MAX_UPLOAD_FILE_MB = 200        # Giới hạn dung lượng file upload (MB).