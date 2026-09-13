#!/usr/bin/env python3
"""run_evals.py — learning-wiki 的回归评测门禁。

自迭代协议（references/self-iteration.md）规定：任何对 SKILL.md 规则、
check_wiki.py 或模板的修改，必须先通过本脚本，才允许升版本。

用法:
    python evals/run_evals.py

用例:
  1) 正样本 ../sample-wiki ：check_wiki 必须 0 ERROR / 0 WARN（退出码 0 且输出含 [PASS ]）
  2) 负样本 bad-wiki ：每种故意埋下的违规，必须被对应检查抓到（退出码 1 且输出含各断言片段）
退出码: 全部断言通过 → 0；任一失败 → 1
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
from pathlib import Path

try:  # Windows GBK 控制台防御
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

_spec = importlib.util.spec_from_file_location("check_wiki", ROOT / "scripts" / "check_wiki.py")
cw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cw)


def run_check(target: Path) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cw.main(["check_wiki.py", str(target)])
    return code, buf.getvalue()


failures: list[str] = []


def expect(name: str, cond: bool, detail: str = ""):
    mark = "PASS" if cond else "FAIL"
    print(f"[{mark}] {name}")
    if not cond:
        failures.append(f"{name}{(': ' + detail) if detail else ''}")


# ---- 用例 1：正样本必须干净 -------------------------------------------------
code, out = run_check(ROOT / "sample-wiki")
expect("sample-wiki 退出码为 0", code == 0, f"实际 {code}\n{out}")
expect("sample-wiki 输出含 [PASS ]", "[PASS ]" in out, out)
expect("sample-wiki 无 ERROR 行", "[ERROR]" not in out, out)
expect("sample-wiki 无 WARN 行", "[WARN ]" not in out, out)

# ---- 用例 2：负样本的每种埋错必须被抓到 -------------------------------------
code, out = run_check(HERE / "bad-wiki")
expect("bad-wiki 退出码为 1", code == 1, f"实际 {code}\n{out}")
for name, frag in [
    ("E2 README 坏链接", "README 链接指向不存在的文件"),
    ("E3 章节编号断档", "章节编号不连续"),
    ("E4 围栏未闭合", "围栏未闭合"),
    ("E5 章节内坏链接", "01-坏章.md: 链接指向不存在的文件"),
    ("W1 缺必备小节", "01-坏章.md 缺少"),
    ("W2 README 缺板块", "README.md 缺少板块"),
    ("W3 悬空引用·章节缺失", "悬空引用 见 09"),
    ("W3 悬空引用·小节缺失", "悬空引用 见 01 §脑裂"),
]:
    expect(name, frag in out, f"输出未含: {frag}")

# ---- 汇总 ------------------------------------------------------------------
if failures:
    print(f"\n[FAIL ] {len(failures)} 条断言未过：")
    for f_ in failures:
        print(f"  - {f_}")
    print("回归门禁未过：禁止升版本，先修复 check_wiki.py / 模板 / fixture。")
    sys.exit(1)
print("\n[PASS ] 回归门禁全过：校验器与 good/bad 样本一致，可以进入人工 review。")
sys.exit(0)
