#!/usr/bin/env python3
"""check_wiki.py — 对 learning-wiki skill 生成的 Wiki 目录做机械校验。

用法:
    python scripts/check_wiki.py <wiki目录> [--strict]

检查项(ERROR 必修, WARN 酌情):
  E1  README.md 缺失
  E2  README 中的相对 .md 链接指向不存在的文件
  E3  章节编号不连续 / 不符合 NN-标题.md 命名
  E4  任一文件中 ``` 围栏未闭合（含 mermaid 渲染失败风险）
  W1  章节缺少必备小节: 自测题 / 参考答案 / 一句话总结 / mermaid 图
  W2  README 缺少: 目录表 / 术语速查 / 因果链(一图流)
退出码: 有 ERROR → 1; --strict 时 WARN 也算失败 → 1; 否则 0
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:  # Windows GBK 控制台防御：保证中文输出不抛 UnicodeEncodeError
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

CHAPTER_RE = re.compile(r"^(\d{2})-(.+)\.md$")

def check_fences(md_files):
    """E4: 每个文件 ``` 围栏计数必须是偶数。"""
    for f in md_files:
        text = f.read_text(encoding="utf-8", errors="replace")
        if text.count("```") % 2 != 0:
            yield "E4", f"{f.name}: ``` 围栏未闭合（奇数个），渲染会错乱"

def check_readme_links(root):
    """E2: README 里的相对 md 链接必须存在。"""
    readme = root / "README.md"
    text = readme.read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(r"\[[^\]]*\]\((?!https?://|mailto:)([^)\s]+?\.md)\)", text):
        target = (readme.parent / m.group(1)).resolve()
        if not target.exists():
            yield "E2", f"README 链接指向不存在的文件: {m.group(1)}"

def check_chapter_numbers(root):
    """E3: NN-*.md 编号从 01 起连续。"""
    nums = sorted(
        int(m.group(1)) for m in (CHAPTER_RE.match(p.name) for p in root.iterdir() if p.is_file()) if m
    )
    if not nums:
        yield "E3", "未发现任何 NN-标题.md 章节文件（单文件模式可忽略本条）"
        return
    expected = list(range(1, len(nums) + 1))
    if nums != expected:
        yield "E3", f"章节编号不连续: 实际 {nums}, 期望 {expected}"

def check_chapter_sections(root):
    """W1: 每章必备小节。"""
    for p in sorted(root.iterdir()):
        m = CHAPTER_RE.match(p.name)
        if not m:
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        missing = [
            label for label, pat in [
                ("一句话总结", "一句话总结"),
                ("自测题", "自测题"),
                ("参考答案", "参考答案"),
                ("mermaid 流程图", "```mermaid"),
            ] if pat not in text
        ]
        if missing:
            yield "W1", f"{p.name} 缺少: {', '.join(missing)}"

def check_readme_sections(root):
    """W2: README 必备板块。"""
    text = (root / "README.md").read_text(encoding="utf-8", errors="replace")
    missing = [
        label for label, pat in [
            ("目录表", "## 目录"),
            ("术语速查", "术语速查"),
            ("因果链一图流", "一图流"),
        ] if pat not in text
    ]
    if missing:
        yield "W2", f"README.md 缺少板块: {', '.join(missing)}"

def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    strict = "--strict" in argv
    if len(args) != 1:
        print(__doc__)
        return 2
    root = Path(args[0])
    if not root.is_dir():
        print(f"[ERROR] 目录不存在: {root}")
        return 2
    md_files = [p for p in root.rglob("*.md") if p.is_file()]
    problems = []
    if not (root / "README.md").exists():
        problems.append(("E1", "缺少 README.md（总览与因果链入口）"))
    else:
        problems += check_readme_links(root)
        problems += check_readme_sections(root)
    problems += check_fences(md_files)
    problems += check_chapter_numbers(root)
    problems += check_chapter_sections(root)

    errors = [msg for code, msg in problems if code.startswith("E")]
    warns = [msg for code, msg in problems if code.startswith("W")]
    for msg in errors:
        print(f"[ERROR] {msg}")
    for msg in warns:
        print(f"[WARN ] {msg}")
    if not problems:
        print(f"[PASS ] {len(md_files)} 个文件全部通过机械检查")
    else:
        print(f"\n共 {len(errors)} 个错误, {len(warns)} 个警告；WARN 请对照 references/quality-rubric.md 人工判断。")
    return 1 if errors or (strict and warns) else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
