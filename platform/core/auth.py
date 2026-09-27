"""
访问口令（可选的安全门）
==========================
本地使用时默认**不启用**，零摩擦。
通过公网隧道访问时建议启用：设置环境变量 PLATFORM_PASSWORD 即可。

启用方式：
    export PLATFORM_PASSWORD="你的口令"
    streamlit run app.py

设计说明：
  - 口令用 hmac.compare_digest 做定时安全比较，避免时序侧信道
  - 登录状态保存在会话内（st.session_state），刷新页面需重新输入
  - 未设置环境变量时完全放行，不影响本地使用
"""
from __future__ import annotations

import hmac
import os

import streamlit as st


def _expected() -> str | None:
    pwd = os.environ.get("PLATFORM_PASSWORD", "").strip()
    return pwd or None


def check() -> bool:
    """返回 True 表示已通过（或无需）验证。"""
    expected = _expected()
    if expected is None:
        return True
    if st.session_state.get("__auth_ok__"):
        return True

    st.markdown(
        '<div class="hero"><div class="eyebrow">Restricted Access</div>'
        '<h1>医学影像 AI 学习平台</h1>'
        '<p class="lede">本平台当前通过公网隧道开放，需要访问口令。</p>'
        '<div class="rule"></div></div>',
        unsafe_allow_html=True,
    )
    with st.form("auth", clear_on_submit=False):
        pwd = st.text_input("访问口令", type="password", placeholder="请输入")
        if st.form_submit_button("进入平台", type="primary"):
            if hmac.compare_digest(pwd, expected):
                st.session_state["__auth_ok__"] = True
                st.rerun()
            else:
                st.error("口令不正确")
    st.caption("口令由启动脚本设置（环境变量 PLATFORM_PASSWORD）。")
    return False


def enabled() -> bool:
    return _expected() is not None
