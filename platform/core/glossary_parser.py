"""术语库解析：把 glossary/*.md 解析成结构化词条，供网站搜索与筛选。"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GLOSSARY_DIR = REPO_ROOT / "glossary"

# 词条行形如：**术语（English）** `L2` ✅ — 定义……
ENTRY_RE = re.compile(r"^\*\*(?P<term>.+?)\*\*\s*(?P<rest>.*)$")
DIFF_RE = re.compile(r"`(L[123])`")
EVID_RE = re.compile(r"(✅|🔶|⚪)")


@dataclass
class Term:
    term: str
    difficulty: str          # L1 / L2 / L3 / ""
    evidence: str            # ✅ / 🔶 / ⚪ / ""
    definition: str
    details: list[str] = field(default_factory=list)
    section: str = ""
    group: str = ""          # 所属大类（A/B/C…）
    source: str = ""         # 所在文件

    @property
    def searchable(self) -> str:
        return " ".join([self.term, self.definition, *self.details]).lower()


def _clean_definition(rest: str) -> tuple[str, str, str]:
    """从 '`L2` ✅ — 定义……' 中拆出难度、证据、定义正文。"""
    diff = DIFF_RE.search(rest)
    evid = EVID_RE.search(rest)
    text = DIFF_RE.sub("", rest)
    text = EVID_RE.sub("", text)
    text = re.sub(r"^[\s—\-–]+", "", text).strip()
    return (diff.group(1) if diff else "",
            evid.group(1) if evid else "",
            text)


def parse_file(path: Path) -> list[Term]:
    terms: list[Term] = []
    section = ""
    group = ""
    current: Term | None = None

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()

        # 大类标题：## D. 影像组学与图像特征
        if line.startswith("## "):
            section = line[3:].strip()
            m = re.match(r"^([A-L])[.、]", section)
            group = m.group(1) if m else ""
            current = None
            continue

        # 词条行
        m = ENTRY_RE.match(line)
        if m and not line.startswith("**——"):
            diff, evid, definition = _clean_definition(m.group("rest"))
            current = Term(
                term=m.group("term").strip(),
                difficulty=diff,
                evidence=evid,
                definition=definition,
                section=section,
                group=group,
                source=path.name,
            )
            terms.append(current)
            continue

        # 续行（↳ 直觉 / 坑 / 出处）
        if current is not None and line.strip():
            if line.lstrip().startswith(("↳", "- ", "  - ")):
                current.details.append(line.strip().lstrip("↳ ").strip())
            elif line.startswith(("|", "#", ">", "```")):
                current = None

    return terms


def load_terms() -> list[Term]:
    """读取 glossary 目录下全部术语。"""
    if not GLOSSARY_DIR.exists():
        return []
    all_terms: list[Term] = []
    for f in sorted(GLOSSARY_DIR.glob("*.md")):
        all_terms.extend(parse_file(f))
    return all_terms


# 四个文件的简短标签
FILE_LABELS = {
    "01-临床-影像-放疗.md": "01 临床 · 影像 · 放疗",
    "02-放射组学-图像处理.md": "02 放射组学 · 图像处理",
    "03-机器学习-统计-可解释性.md": "03 机器学习 · 统计 · 可解释性",
    "04-工程-标准-代号-数据集.md": "04 工程 · 标准 · 代号 · 数据集",
}


def file_label(name: str) -> str:
    return FILE_LABELS.get(name, name)
