"""Vùng sidebar: điều khiển cấu hình, lịch sử chat và thao tác quản trị."""

import streamlit as st
from ui.components.sidebar_parts.actions import (
    render_action_buttons,
    render_pending_dialogs,
)
from ui.components.sidebar_parts.history import render_chat_history
from ui.components.sidebar_parts.panels import (
    render_chunk_strategy_controls,
    render_instructions,
    render_model_config,
    render_settings,
)
from ui.components.sidebar_parts.state import ensure_sidebar_state

class Sidebar:
    """Lớp điều phối cho toàn bộ thành phần hiển thị ở thanh bên."""

    def render(self):
        """Hiển thị tuần tự các section sidebar và dialog xác nhận thao tác."""
        ensure_sidebar_state()
        with st.sidebar:
            render_instructions()
            st.divider()
            render_chunk_strategy_controls()
            st.divider()
            render_chat_history()
            st.divider()
            render_action_buttons()
            st.divider()
            render_settings()
            st.divider()
            render_model_config()

        # Hiển thị dialog bên ngoài ngữ cảnh sidebar để hành vi click ổn định hơn.
        render_pending_dialogs()