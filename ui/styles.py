"""Khai báo CSS giao diện toàn cục và kiểu chi tiết cho các thành phần."""

PRIMARY_COLOR = "#007BFF"
SECONDARY_COLOR = "#FFC107"
BACKGROUND_COLOR = "#F8F9FA"
SIDEBAR_COLOR = "#2C2F33"
TEXT_COLOR = "#212529"
SIDEBAR_TEXT_COLOR = "#FFFFFF"
ASSISTANT_BG_COLOR = "#E9F2FF"
ASSISTANT_TEXT_COLOR = "#0F172A"
USER_BG_COLOR = "#007BFF"
USER_TEXT_COLOR = "#FFFFFF"


def get_css() -> str:
    """Trả về chuỗi CSS được inject vào Streamlit mỗi lần chạy app."""
    return f"""
    <style>
        /* Nền chính */
        .stApp {{
            background-color: {BACKGROUND_COLOR};
            color: {TEXT_COLOR};
        }}
        /* Thanh bên */
        [data-testid="stSidebar"] {{
            background-color: {SIDEBAR_COLOR};
            color: {SIDEBAR_TEXT_COLOR};
        }}
        /* Màu chữ trong thanh bên */
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {{
            color: {SIDEBAR_TEXT_COLOR};
        }}
        /* Nút chính */
        .stButton > button {{
            background-color: {PRIMARY_COLOR};
            color: white;
            border: none;
            border-radius: 8px;
        }}
        /* Khu vực uploader */
        [data-testid="stFileUploader"] {{
            border: 2px dashed {SECONDARY_COLOR};
            border-radius: 8px;
        }}
        /* Khung chat cơ bản */
        [data-testid="stChatMessage"] {{
            border-radius: 12px;
            padding: 6px 10px;
            margin-bottom: 8px;
        }}
        /* Tin nhắn assistant */
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {{
            background-color: {ASSISTANT_BG_COLOR};
            color: {ASSISTANT_TEXT_COLOR};
        }}
        /* Tin nhắn người dùng */
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {{
            background-color: {USER_BG_COLOR};
            color: {USER_TEXT_COLOR};
        }}
        /* Giữ khả năng đọc tốt trong từng bubble chat */
        [data-testid="stChatMessage"] p,
        [data-testid="stChatMessage"] li,
        [data-testid="stChatMessage"] span,
        [data-testid="stChatMessage"] div {{
            color: inherit;
        }}

        /* Giao diện citation tracking */
        .citation-answer {{
            line-height: 1.8;
            font-size: 1.01rem;
            white-space: normal;
        }}
        .citation-highlight {{
            text-decoration: none;
            color: inherit !important;
            padding: 2px 7px;
            border-radius: 8px;
            border-bottom: 3px solid transparent;
            transition: all 0.2s ease;
            display: inline;
        }}
        .citation-highlight:hover {{
            filter: brightness(0.96);
            box-shadow: 0 0 0 1px rgba(15, 23, 42, 0.12) inset;
        }}
        .citation-divider {{
            height: 1px;
            background: rgba(15, 23, 42, 0.14);
            margin: 0.75rem 0 0.85rem;
            width: 100%;
        }}
        .citation-meta-row,
        .citation-legend-row {{
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 8px;
            margin-top: 0.35rem;
            margin-bottom: 0.2rem;
        }}
        .citation-meta-title {{
            font-weight: 700;
            color: #1f2937;
            margin-right: 4px;
        }}
        .citation-badge {{
            text-decoration: none;
            color: #1f2937 !important;
            font-weight: 700;
            border-radius: 999px;
            padding: 4px 12px;
            border: 1px solid transparent;
            display: inline-flex;
            align-items: center;
        }}
        .citation-badge:hover {{
            transform: translateY(-1px);
        }}
        .citation-legend-chip {{
            border-radius: 6px;
            font-weight: 700;
            color: #334155;
            padding: 1px 7px;
            border: 1px solid transparent;
        }}
        .citation-legend-label {{
            color: #374151;
            margin-right: 8px;
            font-weight: 600;
        }}
        .citation-source-1 {{
            background: #f6e8c5;
            border-color: #d8b267;
        }}
        .citation-source-2 {{
            background: #d9f0e9;
            border-color: #70bca6;
        }}
        .citation-source-3 {{
            background: #e3ecfd;
            border-color: #7ea3f5;
        }}
        .citation-source-4 {{
            background: #f4dff2;
            border-color: #cc86c0;
        }}
        .citation-context-box {{
            border: 1px solid rgba(15, 23, 42, 0.18);
            border-radius: 10px;
            padding: 12px 14px;
            background: #f8fafc;
            line-height: 1.65;
            max-height: 48vh;
            overflow: auto;
        }}
        .citation-context-box mark {{
            background: #fde68a;
            border-radius: 4px;
            padding: 0 2px;
        }}

        .citation-overlay-reset-anchor {{
            position: fixed;
            top: 0;
        }}
        .citation-overlay-target {{
            display: none;
            position: fixed !important;
            inset: 0 !important;
            z-index: 2147483000 !important;
        }}
        .citation-overlay-target:target {{
            display: block;
        }}
        .citation-overlay-backdrop {{
            position: fixed !important;
            inset: 0 !important;
            background: rgba(15, 23, 42, 0.5);
            backdrop-filter: blur(2px);
            text-decoration: none;
            z-index: 2147483001 !important;
        }}
        .citation-modal {{
            position: fixed !important;
            z-index: 2147483002 !important;
            width: min(860px, 92vw);
            max-height: 82vh;
            overflow: auto;
            top: 7vh;
            left: 50%;
            transform: translateX(-50%);
            background: #ffffff;
            border-radius: 16px;
            border: 1px solid rgba(15, 23, 42, 0.14);
            box-shadow: 0 20px 50px rgba(15, 23, 42, 0.35);
            padding: 18px 18px 16px;
        }}
        .citation-modal-title {{
            font-size: 1.08rem;
            font-weight: 800;
            color: #0f172a;
            padding-right: 32px;
        }}
        .citation-modal-subtitle {{
            margin-top: 4px;
            margin-bottom: 10px;
            color: #334155;
            font-weight: 600;
        }}
        .citation-modal-label {{
            margin-top: 8px;
            margin-bottom: 7px;
            color: #0f172a;
            font-weight: 800;
        }}
        .citation-modal-close {{
            position: absolute;
            top: 10px;
            right: 12px;
            width: 30px;
            height: 30px;
            border-radius: 999px;
            text-decoration: none;
            background: #e2e8f0;
            color: #0f172a !important;
            font-size: 1.2rem;
            font-weight: 900;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .citation-modal-close:hover {{
            background: #cbd5e1;
        }}

        @media (max-width: 768px) {{
            .citation-modal {{
                top: 4vh;
                width: min(94vw, 94vw);
                max-height: 88vh;
                padding: 14px;
            }}
        }}
    </style>
    """