# 4. TRIỂN KHAI
## 4.1 Công nghệ sử dụng
### 4.1.1 Frontend
- Streamlit 1.55.0: Framework tạo giao diện web nhanh chóng.

### 4.1.2 Backend & AI
- LangChain 0.3.16: Framework xây dựng ứng dụng LLM.
- LangChain Community 0.3.16: Các extension cộng đồng.
- LangChain Text Splitters 0.3.11: Chia nhỏ văn bản.
- LangChain HuggingFace 0.3.1: Tích hợp với model HuggingFace.
- LangChain Google GenAI 2.1.4: Tích hợp với Gemini API.
- FAISS 1.13.2: Thư viện tìm kiếm vector similarity.
- Sentence Transformers 5.3.0: Model embedding đa ngôn ngữ.
- Google Gemini API: Mô hình ngôn ngữ lớn từ Google (dùng qua API cloud).

### 4.1.3 Document Processing
- PyPDF 6.9.1: Trích xuất văn bản từ file PDF.
- Docx2txt 0.9: Trích xuất văn bản từ file DOCX.

### 4.1.4 Python Libraries
- python-dotenv 1.2.2: Quản lý biến môi trường (API key).

## 4.2 Cài đặt môi trường
### 4.2.1 Yêu cầu hệ thống
Phần mềm:
- Python 3.10 hoặc 3.11.
- pip package manager.
- Trình duyệt web (Chrome, Firefox).
- Kết nối Internet (để gọi Gemini API).
Tài khoản:
- Tài khoản Google để lấy Gemini API key.

### 4.2.2 Các bước cài đặt
- Bước 1: Clone hoặc tải project

git clone [repository-url]
cd pdf-RAG

- Bước 2: Tạo virtual environment

python -m venv venv
source venv/bin/activate  # Trên Mac/Linux
venv\Scripts\activate  # Trên Windows

- Bước 3: Cài đặt dependencies

pip install -r requirements.txt

Nội dung file requirements.txt:

streamlit==1.55.0
langchain==0.3.16
langchain-community==0.3.16
langchain-text-splitters==0.3.11
langchain-huggingface==0.3.1
langchain-google-genai==2.1.4
faiss-cpu==1.13.2
sentence-transformers==5.3.0
pypdf==6.9.1
docx2txt==0.9
python-dotenv==1.2.2

- Bước 4: Lấy Gemini API key
    - Truy cập https://aistudio.google.com/apikey
    - Đăng nhập bằng tài khoản Google.
    - Nhấn "Create API Key".
    - Copy key vừa tạo (bắt đầu bằng AIza...).

- Bước 5: Tạo file .env
Tạo file .env trong thư mục gốc với nội dung:

GEMINI_KEY=your_api_key_here
Thay your_api_key_here bằng API key vừa lấy.

- Bước 6: Chạy ứng dụng

streamlit run main.py

## 4.3 Cấu trúc thư mục
pdf-RAG/
│
├── main.py                 # File chạy ứng dụng web
├── app.py                  # File chạy console (debug)
├── config.py               # Cấu hình tập trung
├── requirements.txt        # Danh sách thư viện
├── .env                    # Biến môi trường (API key)
├── README.md               # Tài liệu hướng dẫn
│
├── loaders/                # Module đọc file
│   ├── pdf_loader.py       # Đọc file PDF
│   ├── docx_loader.py      # Đọc file DOCX
│   └── base_loader.py      # Base class
│
├── rag/                    # Module RAG
│   ├── embeddings.py       # Tạo vector embeddings
│   ├── retriever.py        # Truy xuất thông tin
│   └── chain.py            # Chain hỏi đáp (dùng Gemini)
│
├── services/               # Module dịch vụ
│   └── rag_pdf_service.py  # Xử lý pipeline RAG
│
├── ui/                     # Module giao diện
│   ├── streamlit_app.py    # Giao diện chính
│   └── components/         # Các component nhỏ
│       ├── sidebar.py      # Sidebar
│       ├── chat_history.py # Lịch sử chat
│       └── session_state.py # Quản lý session
│
└── data/                   # Thư mục chứa tài liệu mẫu
    └── intro.pdf           # File PDF mẫu