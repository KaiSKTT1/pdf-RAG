import streamlit as st

from config import CHUNK_SIZE, CHUNK_OVERLAP


_SESSION_DEFAULT_FACTORIES = {
    "chain": lambda: None,
    "messages": list,
    "chat_history": list,
    "selected_history_idx": lambda: None,
    "selected_document_name": lambda: None,
    "active_document_name": lambda: None,
    "uploader_key_seed": lambda: 0,
    "chunk_size": lambda: CHUNK_SIZE,
    "chunk_overlap": lambda: CHUNK_OVERLAP,
    "chain_chunk_size": lambda: None,
    "chain_chunk_overlap": lambda: None,
    "show_clear_history_dialog": lambda: False,
    "show_clear_vector_store_dialog": lambda: False,
}


def ensure_app_session_state() -> None:
    for key, factory in _SESSION_DEFAULT_FACTORIES.items():
        if key not in st.session_state:
            st.session_state[key] = factory()


def normalize_chunk_selection(
    chunk_size_options: list[int],
    chunk_overlap_options: list[int],
) -> None:
    if st.session_state.chunk_size not in chunk_size_options:
        st.session_state.chunk_size = CHUNK_SIZE
    if st.session_state.chunk_overlap not in chunk_overlap_options:
        st.session_state.chunk_overlap = CHUNK_OVERLAP


def reset_chat_history_state() -> None:
    st.session_state.messages = []
    st.session_state.chat_history = []
    st.session_state.selected_history_idx = None


def reset_vector_store_state() -> None:
    st.session_state.chain = None
    st.session_state.active_document_name = None
    st.session_state.selected_document_name = None
    st.session_state.chain_chunk_size = None
    st.session_state.chain_chunk_overlap = None
    reset_chat_history_state()
    st.session_state.uploader_key_seed = st.session_state.get("uploader_key_seed", 0) + 1


def rebuild_chat_history_from_messages() -> None:
    """Sync chat history with chat messages to avoid count mismatches."""
    messages = st.session_state.get("messages", [])
    rebuilt_history = []

    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")

        if role == "user":
            rebuilt_history.append(
                {
                    "question": content,
                    "answer": "",
                    "status": "pending",
                }
            )
        elif role == "assistant":
            for item in reversed(rebuilt_history):
                if not item.get("answer"):
                    item["answer"] = content
                    item["status"] = "answered"
                    break

    existing_history = st.session_state.get("chat_history", [])
    if len(rebuilt_history) >= len(existing_history):
        st.session_state.chat_history = rebuilt_history
