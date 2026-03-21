# ui/styles.py
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

# CSS inject vào Streamlit
def get_css() -> str:
    return f"""
    <style>
        /* Main background */
        .stApp {{
            background-color: {BACKGROUND_COLOR};
            color: {TEXT_COLOR};
        }}
        /* Sidebar */
        [data-testid="stSidebar"] {{
            background-color: {SIDEBAR_COLOR};
            color: {SIDEBAR_TEXT_COLOR};
        }}
        /* Sidebar text */
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {{
            color: {SIDEBAR_TEXT_COLOR};
        }}
        /* Primary button */
        .stButton > button {{
            background-color: {PRIMARY_COLOR};
            color: white;
            border: none;
            border-radius: 8px;
        }}
        /* Upload button */
        [data-testid="stFileUploader"] {{
            border: 2px dashed {SECONDARY_COLOR};
            border-radius: 8px;
        }}
        /* Chat bubble base */
        [data-testid="stChatMessage"] {{
            border-radius: 12px;
            padding: 6px 10px;
            margin-bottom: 8px;
        }}
        /* Assistant message */
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {{
            background-color: {ASSISTANT_BG_COLOR};
            color: {ASSISTANT_TEXT_COLOR};
        }}
        /* User message */
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {{
            background-color: {USER_BG_COLOR};
            color: {USER_TEXT_COLOR};
        }}
        /* Keep text readable inside chat */
        [data-testid="stChatMessage"] p,
        [data-testid="stChatMessage"] li,
        [data-testid="stChatMessage"] span,
        [data-testid="stChatMessage"] div {{
            color: inherit;
        }}
    </style>
    """