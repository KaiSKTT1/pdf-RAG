# ===== LLM - GEMINI =====
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_API_KEY = "AIzaSyCAp8pahwcpM1Uoz3Q7bSk5jKvgQj_L03M"
LLM_TEMPERATURE = 0.7
LLM_TOP_P = 0.9
LLM_REPEAT_PENALTY = 1.1
# Biến tương thích cho các chỗ cũ vẫn dùng tên LLM_MODEL
LLM_MODEL = GEMINI_MODEL

# ===== EMBEDDING =====
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
EMBEDDING_DEVICE = "cpu"        # đổi thành "cuda" nếu có GPU
EMBEDDING_NORMALIZE = True

# ===== TEXT SPLITTER =====
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# ===== RETRIEVER =====
SEARCH_TYPE = "similarity"      # hoặc "mmr" để kết quả đa dạng hơn
TOP_K = 3                       # số chunks trả về
FETCH_K = 20                    # fetch nhiều rồi lọc

# ===== UPLOAD =====
MAX_UPLOAD_FILE_MB = 200        # Giới hạn dung lượng PDF upload