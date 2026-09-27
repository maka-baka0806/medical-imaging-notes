#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
平台冒烟测试
=============
用 Streamlit 官方 AppTest 框架跑真实入口 app.py 与全部页面，捕获渲染异常。

用法：
    conda activate medimg
    cd platform
    python tests/test_app.py

为什么必须测 app.py？
    逐页单独调用 render() 会漏掉「导航配置」这一类错误
    （例如六个页面函数都叫 render 导致 URL 路径冲突）。
    只有跑真实入口才能覆盖到。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

PLATFORM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATFORM))
os.chdir(PLATFORM)

from streamlit.testing.v1 import AppTest  # noqa: E402

VIEWS = ["home", "replication", "publications", "radiomic_filtering", "segmentation_uq", "modeling_survival",
         "dosimetry_tools", "registration", "glossary", "imaging_lab",
         "phantom_lab", "roadmap", "toolbox"]
TMP = Path("/tmp/dsh_platform_tests")
TMP.mkdir(exist_ok=True)

passed, failed = 0, 0


def check(name: str, at: AppTest) -> None:
    global passed, failed
    if at.exception:
        failed += 1
        print(f"❌ {name}")
        for e in at.exception[:2]:
            msg = getattr(e, "value", e)
            print(f"     {str(msg)[:400]}")
    else:
        passed += 1
        print(f"✅ {name}（markdown {len(at.markdown)} 段，button {len(at.button)} 个）")


def main() -> int:
    print("=" * 60)
    print("1) 真实入口 app.py（覆盖 st.navigation 配置）")
    print("=" * 60)
    at = AppTest.from_file(str(PLATFORM / "app.py"), default_timeout=300)
    at.run()
    check("app.py 入口 + 默认页", at)

    print()
    print("=" * 60)
    print("2) 逐个页面")
    print("=" * 60)
    for view in VIEWS:
        entry = TMP / f"page_{view}.py"
        entry.write_text(
            "import sys\n"
            f"sys.path.insert(0, {str(PLATFORM)!r})\n"
            "import streamlit as st\n"
            'st.set_page_config(layout="wide")\n'
            f"from views import {view}\n"
            f"{view}.render()\n",
            encoding="utf-8",
        )
        at = AppTest.from_file(str(entry), default_timeout=300)
        at.run()
        check(f"views/{view}.py", at)

    print()
    print("=" * 60)
    print(f"结果：通过 {passed} 项，失败 {failed} 项")
    print("=" * 60)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
