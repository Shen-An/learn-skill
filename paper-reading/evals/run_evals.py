#!/usr/bin/env python3
"""run_evals.py — paper-reading 的回归评测门禁。

references/self-iteration.md 规定：任何对 SKILL.md 规则、check_paper_note.py
或模板的修改，必须先通过本脚本，才允许升版本。

用法:
    python evals/run_evals.py

用例:
  1) 正样本 good-sample：6 个 fixture 逐个跑（deep/table/mindmap/mmd/faq/review 各一），
     必须退出码 0、输出含 `[PASS ]` 且不含 `[ERROR]`、不含 `[WARN ]`（即 0 ERROR 0 WARN）
  2) 负样本 bad-sample：每个 fixture 必须退出码 1，且输出包含它设计要触发的
     **每个** CODE 与关键消息片段（逐项断言）
  3) 警告样本 warn-sample：每个 fixture 必须退出码 0、输出含 `[WARN ] <CODE>`
     且不含 `[ERROR]`、不含 `[PASS ]`（有 WARN 时汇总行走 WARN 分支，不会出现 PASS 行）；
     同样做"每个 fixture 都在断言表内"的完整性校验
  4) 回归正样本 ../sample：目录存在且含 .md 时，每个文件按文件名 token 判模式后
     必须退出码 0 且不含 `[ERROR]`、不含 `[WARN ]`；目录不存在时打印 `[SKIP]` 且不算失败
  5) PDF 抽取器 scripts/pdf_extract.py：用 pdf-cases/ 下由 make_fixtures.py 生成的
     真实 PDF（正常 3 页 / 无文本层 / 加密 / 假 PDF）跑**子进程**，逐条断言它的
     docstring 契约：输出文件名与头部字段、页锚点格式与顺序、--pages 裁剪不重编号、
     越界与参数错误退出码 2、解析失败 1、加密 4、缺依赖 3、目录模式一层/递归、
     默认与 --out 输出位置、只读不改动源 PDF；用例结束前清理全部临时产物
  6) 合集层索引 index-cases：check_paper_note.py 的 `--mode index`（10 个 CODE）逐项断言——
     good/索引.md 必须 0 ERROR 0 WARN；每个 bad fixture 退出码 1 且**只报它设计的那一个
     ERROR 码**；每个 warn fixture 退出码 0 且只报它设计的那一个 WARN 码；
     orphan/（有笔记未登记）报 W-IDX-ORPHAN 而 linked/（已登记）不报，证明该 WARN 不是恒真；
     `--mode auto` 对首行带 `<!-- paper-reading: collection-index -->` 的文件判为 index，
     缺标记文件则不会被 auto 判成 index；最后做"每个索引 fixture 都在断言表内"的完整性自检
  7) 专业术语表 terms-cases：check_paper_note.py 的 `--mode terms`（11 个 CODE）逐项断言——
     good/术语-示例.md 必须 0 ERROR 0 WARN 且以 `[PASS ] 11 项检查全部通过` 结尾；每个 bad
     fixture 退出码 1 且**命中的 ERROR 码集合恰为**它设计的那一个；每个 warn fixture 退出码 0、
     无任何 E 码、命中的 WARN 码集合恰为它设计的那一个；`--mode auto` 对每个 `术语-*.md`
     与显式 `--mode terms` 输出逐字一致；good fixture 同时用 `[原文 p.7]` 与 `[原文 p.7-8]`
     守住"模板说合法、校验器就必须认"的带页码出处口径；最后做"每个术语表 fixture 都在
     断言表内"的完整性自检
退出码: 全部断言通过 → 0；任一失败 → 1
"""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:  # Windows GBK 控制台防御
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.dont_write_bytecode = True  # 门禁自身不落 __pycache__（import 校验器只读源码）

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

_spec = importlib.util.spec_from_file_location("check_paper_note", ROOT / "scripts" / "check_paper_note.py")
cpn = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cpn)


def run_check(path: Path, mode: str | None = None, refs: int | None = None) -> tuple[int, str]:
    argv = ["check_paper_note.py", str(path)]
    if mode is not None:
        argv += ["--mode", mode]
    if refs is not None:
        argv += ["--refs", str(refs)]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cpn.main(argv)
    return code, buf.getvalue()


failures: list[str] = []
assertions = 0


def expect(name: str, cond: bool, detail: str = ""):
    global assertions
    assertions += 1
    mark = "PASS" if cond else "FAIL"
    print(f"[{mark}] {name}")
    if not cond:
        failures.append(f"{name}{(': ' + detail) if detail else ''}")


# ---- 用例 1：正样本必须干净 -------------------------------------------------
GOOD_FIXTURES = ["深读-示例.md", "表格-示例.md", "思维导图-示例.md",
                 "导图-示例.md", "难点-示例.md", "综述-示例.md"]
good_dir = HERE / "good-sample"
present = sorted(p.name for p in good_dir.glob("*.md"))
expect("good-sample 六个 fixture 齐全", all(n in present for n in GOOD_FIXTURES), f"实际 {present}")
for name in sorted(present):
    code, out = run_check(good_dir / name)
    expect(f"good-sample/{name} 退出码为 0", code == 0, f"实际 {code}\n{out}")
    expect(f"good-sample/{name} 输出含 [PASS ]", "[PASS ]" in out, out)
    expect(f"good-sample/{name} 无 ERROR 行", "[ERROR]" not in out, out)
    expect(f"good-sample/{name} 无 WARN 行", "[WARN ]" not in out, out)

# ---- 用例 2：负样本的每种埋错必须被抓到 -------------------------------------
# (fixture, mode, refs, [(CODE, 关键消息片段), ...])
BAD_CASES: list[tuple[str, str, int | None, list[tuple[str, str]]]] = [
    ("深读-标题与总结不合格.md", "deep", None, [
        ("E-DEEP-H1", "首个非空行必须是唯一的 H1 论文标题"),
        ("E-DEEP-SUM", "实际 22 字"),
        ("E-DEEP-SEC", "缺少必备小节：背景"),
        ("E-DEEP-SEC", "缺少必备小节：局限"),
    ]),
    ("深读-公式未闭合.md", "deep", None, [
        ("E-DEEP-MATH", "行间公式 $$ 数量为 1（奇数，未闭合）"),
        ("E-DEEP-INLINE", "行内 $ 数量为 1（奇数，未闭合）"),
    ]),
    ("深读-被围栏包裹.md", "deep", None, [
        ("E-DEEP-WRAP", "整篇被代码围栏包裹，应直接输出 Markdown"),
        ("E-DEEP-H1", "首个非空行必须是唯一的 H1 论文标题"),
    ]),
    ("深读-表格列数错.md", "deep", None, [
        ("E-DEEP-TABLE", "表格列数 2 与表头 3 不一致"),
    ]),
    ("表格-表头错误.md", "table", None, [
        ("E-TBL-HEAD", "实际：| 维度 | 说明 |"),
    ]),
    ("表格-缺少维度.md", "table", None, [
        ("E-TBL-DIM", "缺少维度：创新点"),
    ]),
    ("表格-维度顺序错.md", "table", None, [
        ("E-TBL-DIM", "第 5 行应为「研究方法」，实际「主要发现」"),
        ("E-TBL-DIM", "第 6 行应为「主要发现」，实际「研究方法」"),
    ]),
    ("表格-内容为空.md", "table", None, [
        ("E-TBL-EMPTY", "维度「作者」内容为空"),
        ("E-TBL-EMPTY", "维度「局限性」内容为空"),
    ]),
    ("表格-句子超长.md", "table", None, [
        ("E-TBL-LEN", "维度「局限性」内容 4 句，超过 3 句上限"),
    ]),
    ("表格-表格外文字.md", "table", None, [
        ("E-TBL-ONLY", "第 14 行存在表格外文字"),
    ]),
    ("表格-行未闭合.md", "table", None, [
        ("E-TBL-FMT", "第 12 行表格未闭合（应以 | 结尾）"),
    ]),
    ("思维导图-根标题不合规.md", "mindmap", None, [
        ("E-MM-ROOT", "首个非空行必须是唯一的 H1 论文标题"),
    ]),
    ("思维导图-分支不符.md", "mindmap", None, [
        ("E-MM-BRANCH", "实际：研究背景 | 研究方法 | 关键结果 | 结论"),
    ]),
    ("思维导图-层级过深.md", "mindmap", None, [
        ("E-MM-DEPTH", "第 11 行节点层级 5 超过 4 层"),
    ]),
    ("思维导图-节点不足.md", "mindmap", None, [
        ("E-MM-EMPTY", "分支「研究结论与意义」子节点不足 2 个"),
    ]),
    ("思维导图-含围栏.md", "mindmap", None, [
        ("E-MM-FENCE", "思维导图不得包含代码围栏"),
    ]),
    ("综述-缺小节.md", "review", None, [
        ("E-RV-SEC", "缺少综述必备小节：研究趋势与展望"),
    ]),
    ("综述-引用越界.md", "review", 3, [
        ("E-RV-CITE", "引用编号 [4] 超出文献范围 1..3"),
        ("E-RV-CITE", "引用编号 [5] 超出文献范围 1..3"),
    ]),
    ("综述-含参考文献.md", "review", None, [
        ("E-RV-NOREF", "不得出现「参考文献」小节（按需求不输出文献列表）"),
    ]),
    # 新增：deep 模式的 E-DEEP-MATH-LINE / E-DEEP-MIX
    ("深读-公式未独占行.md", "deep", None, [
        ("E-DEEP-MATH-LINE", "第 28 行行间公式未独占行（应写成 $$ 单独一行 + 公式单独一行 + $$ 单独一行）"),
        ("E-DEEP-MATH", "行间公式 $$ 数量为 1（奇数，未闭合）"),
    ]),
    ("深读-混装思维导图.md", "deep", None, [
        ("E-DEEP-MIX", "深读文档内混装了思维导图分支（3 个），思维导图必须独立成文件"),
    ]),
    # 新增：mmd 模式（可渲染导图）的 7 个 ERROR 码
    ("导图-缺围栏.md", "mmd", None, [
        ("E-MMD-FENCE", "缺少 ```mermaid 开栏（必须恰好一个 mermaid 围栏块）"),
    ]),
    ("导图-围栏未闭合.md", "mmd", None, [
        ("E-MMD-FENCE", "第 5 行的 ```mermaid 围栏未闭合（缺少 ``` 闭合栏）"),
    ]),
    ("导图-围栏过多.md", "mmd", None, [
        ("E-MMD-FENCE", "第 32 行出现多余围栏行，必须以一个 mermaid 块收尾"),
    ]),
    ("导图-缺mindmap关键字.md", "mmd", None, [
        ("E-MMD-KEYWORD", "围栏内第一个非空行必须是 mindmap，实际：graph"),
    ]),
    ("导图-多根节点.md", "mmd", None, [
        ("E-MMD-ROOT", "缩进最小的节点行有 2 条，根节点必须唯一"),
    ]),
    ("导图-无节点.md", "mmd", None, [
        ("E-MMD-ROOT", "围栏内没有节点行，无法确定唯一根节点"),
    ]),
    ("导图-分支不符.md", "mmd", None, [
        ("E-MMD-BRANCH", "实际：研究背景 | 研究方法 | 关键结果 | 结论与意义"),
    ]),
    ("导图-层级过深.md", "mmd", None, [
        ("E-MMD-DEPTH", "第 11 行节点层级 5 超过 4 层"),
    ]),
    ("导图-裸括号.md", "mmd", None, [
        ("E-MMD-SYNTAX", "第 17 行节点文本含 Mermaid 危险字符「,」"),
        ("E-MMD-SYNTAX", "第 30 行节点文本含 Mermaid 危险字符「:」"),
    ]),
    # 新增：faq 模式（难点与解答）的 6 个 ERROR 码
    ("难点-标题不合规.md", "faq", None, [
        ("E-FAQ-H1", "首个非空行必须是唯一的 H1 论文标题"),
    ]),
    ("难点-小节不足.md", "faq", None, [
        ("E-FAQ-SEC", "## 小节数 2 不足 3，一份难点文档至少 3 条难点"),
    ]),
    ("难点-缺字段.md", "faq", None, [
        ("E-FAQ-FIELD", "小节「二、双重增强里为什么能保证标签不变」缺少 **难点**：字段"),
        ("E-FAQ-FIELD", "小节「二、双重增强里为什么能保证标签不变」缺少 **解答**：字段"),
    ]),
    ("难点-解答无来源标记.md", "faq", None, [
        ("E-FAQ-CITE", "小节「二、双重增强里为什么能保证标签不变」的 **解答** 段落没有任何来源标记"
                       "（[原文]/[代码]/[摘要]/[二手]/[OCR]/[推断]/[数字]）"),
    ]),
    ("难点-小节重名.md", "faq", None, [
        ("E-FAQ-DUP", "## 小节标题重复：一、为什么黑盒迁移攻击里扰动会过拟合源模型"),
    ]),
]

bad_dir = HERE / "bad-sample"
bad_present = sorted(p.name for p in bad_dir.glob("*.md"))
covered = {name for name, _, _, _ in BAD_CASES}
expect("bad-sample 每个 fixture 都在断言表内", set(bad_present) <= covered, f"未覆盖: {sorted(set(bad_present) - covered)}")

for name, mode, refs, checks in BAD_CASES:
    code, out = run_check(bad_dir / name, mode, refs)
    tag = f"bad-sample/{name} --mode {mode}" + (f" --refs {refs}" if refs else "")
    expect(f"{tag} 退出码为 1", code == 1, f"实际 {code}\n{out}")
    for want_code, frag in checks:
        expect(f"{tag} 命中 {want_code}：{frag}", want_code in out and frag in out, f"输出未含 {want_code} / {frag}\n{out}")

# ---- 用例 2 附加：--refs 只影响 review 模式的编号范围 -----------------------
code, out = run_check(bad_dir / "综述-引用越界.md", "review", None)
expect("不传 --refs 时 N 取正文最大编号，同一文件退出码为 0", code == 0, f"实际 {code}\n{out}")
expect("不传 --refs 时无 E-RV-CITE", "E-RV-CITE" not in out, out)

# ---- 用例 3：warn-sample 每个 WARN 码各有最小 fixture -----------------------
# 每个 fixture 只埋它自己那一类问题（个别 fixture 不可避免会多带 1 条 WARN），
# 断言只要求：退出码 0、无 `[ERROR]`、含目标 `[WARN ] <CODE>`、不含 `[PASS ]`。
# (fixture, mode, refs, CODE, 关键消息片段)
WARN_CASES: list[tuple[str, str, int | None, str, str]] = [
    ("深读-缺来源类型.md", "deep", None, "W-DEEP-SRC-KIND",
     "缺少「来源类型：」声明（PDF 全文 / 官方摘要 / 二手转述 / 代码）"),
    ("深读-无页码锚点.md", "deep", None, "W-DEEP-PAGE",
     "声明来源为 PDF 全文，但全文没有页码锚点（如 [原文 p.12]）"),
    ("深读-缺符号表.md", "deep", None, "W-DEEP-SYM",
     "公式块 3 个但缺少符号与记号表"),
    ("深读-无引用标记.md", "deep", None, "W-DEEP-CITE",
     "未发现引用标注或来源标记，无法回溯证据"),
    ("深读-含寒暄.md", "deep", None, "W-DEEP-TONE",
     "行出现助手口吻/寒暄词：「以下是」"),
    ("思维导图-节点过多.md", "mindmap", None, "W-MM-BLOAT",
     "节点总数 85 超过 80，建议精简（思维导图不是全文搬家）"),
    ("综述-引用不连续.md", "review", 3, "W-RV-GAP",
     "引用编号不连续：出现 [3] 但缺少 [2]"),
    ("综述-小节无引用.md", "review", None, "W-RV-DENSITY",
     "小节「二、各论文主要贡献」内没有任何 [num] 引用"),
    # 新增：mmd 模式的两个 WARN 码
    ("导图-节点过多.md", "mmd", None, "W-MMD-BLOAT",
     "节点总数 86 超过 80，建议精简（可渲染导图不是全文搬家）"),
    ("导图-围栏外有文字.md", "mmd", None, "W-MMD-TEXT",
     "第 5 行存在 mermaid 围栏与 H1 之外的内容，导图文件应只有标题 + 一个 mermaid 块"),
    # 新增：faq 模式的四个 WARN 码
    ("难点-缺常见误解.md", "faq", None, "W-FAQ-MISCONCEPT",
     "小节「二、双重增强里为什么能保证标签不变」缺少 **常见误解**：字段（❌ 错法 → ✅ 正解）"),
    ("难点-缺自检.md", "faq", None, "W-FAQ-SELFCHECK",
     "小节「二、双重增强里为什么能保证标签不变」缺少 **自检**：字段"),
    ("难点-解答过短.md", "faq", None, "W-FAQ-SHORT",
     "小节「二、双重增强里为什么能保证标签不变」的 **解答** 正文 31 字，少于 80 字（中文字符 + 英文单词）"),
    ("难点-含寒暄.md", "faq", None, "W-FAQ-TONE",
     "第 10 行出现助手口吻/寒暄词：「以下是」"),
]

warn_dir = HERE / "warn-sample"
warn_present = sorted(p.name for p in warn_dir.glob("*.md"))
warn_covered = {name for name, _, _, _, _ in WARN_CASES}
expect("warn-sample 目录存在且不为空", bool(warn_present), f"{warn_dir} 下没有 .md fixture")
expect("warn-sample 每个 fixture 都在断言表内",
       bool(warn_present) and set(warn_present) <= warn_covered,
       f"未覆盖: {sorted(set(warn_present) - warn_covered)}")

for name, mode, refs, want_code, frag in WARN_CASES:
    code, out = run_check(warn_dir / name, mode, refs)
    tag = f"warn-sample/{name} --mode {mode}" + (f" --refs {refs}" if refs else "")
    expect(f"{tag} 退出码为 0", code == 0, f"实际 {code}\n{out}")
    expect(f"{tag} 无 ERROR 行", "[ERROR]" not in out, out)
    expect(f"{tag} 命中 {want_code}：{frag}", f"[WARN ] {want_code}" in out and frag in out,
           f"输出未含 {want_code} / {frag}\n{out}")
    expect(f"{tag} 无 [PASS ] 行", "[PASS ]" not in out, out)

# ---- 用例 4 附加：--mode auto 的模式判定（顺序敏感） ------------------------
# 文件名判定顺序：思维导图 → mindmap；导图/mermaid/mmd → mmd；难点/问答/faq → faq。
# 判定结果用"该模式专属的 E 码是否出现"来反推，避免直接依赖内部函数。
def auto_mode_probe(path: Path) -> tuple[int, str]:
    return run_check(path, "auto")


code, out = auto_mode_probe(good_dir / "思维导图-示例.md")
expect("auto: 思维导图-示例.md 判为 mindmap（输出无 mmd/faq 专属码）",
       code == 0 and "E-MMD-" not in out and "E-FAQ-" not in out, f"实际 {code}\n{out}")

code, out = auto_mode_probe(good_dir / "导图-示例.md")
expect("auto: 导图-示例.md 判为 mmd（9 项检查全过）",
       code == 0 and "[PASS ] 9 项检查全部通过" in out, f"实际 {code}\n{out}")

code, out = auto_mode_probe(good_dir / "难点-示例.md")
expect("auto: 难点-示例.md 判为 faq（19 项检查全过）",
       code == 0 and "[PASS ] 19 项检查全部通过" in out, f"实际 {code}\n{out}")

# 显式 --mode mmd / --mode faq 必须与 auto 结论一致
code_auto, out_auto = run_check(good_dir / "导图-示例.md", "auto")
code_mmd, out_mmd = run_check(good_dir / "导图-示例.md", "mmd")
expect("显式 --mode mmd 与 auto 对导图-示例.md 结论一致",
       code_auto == code_mmd == 0 and out_auto == out_mmd, f"{out_auto}\n---\n{out_mmd}")
code_auto, out_auto = run_check(good_dir / "难点-示例.md", "auto")
code_faq, out_faq = run_check(good_dir / "难点-示例.md", "faq")
expect("显式 --mode faq 与 auto 对难点-示例.md 结论一致",
       code_auto == code_faq == 0 and out_auto == out_faq, f"{out_auto}\n---\n{out_faq}")

# ---- 用例 4：回归正样本 ../sample（可有可无） -------------------------------
sample_dir = ROOT / "sample"
sample_md = sorted(p for p in sample_dir.glob("*.md")) if sample_dir.is_dir() else []
if not sample_md:
    print(f"[SKIP] {sample_dir.name}/ 不存在或不含 .md，用例 4 跳过")
else:
    for path in sample_md:
        code, out = run_check(path, "auto")
        expect(f"sample/{path.name} 退出码为 0", code == 0, f"实际 {code}\n{out}")
        expect(f"sample/{path.name} 无 ERROR 行", "[ERROR]" not in out, out)
        expect(f"sample/{path.name} 无 WARN 行", "[WARN ]" not in out, out)

# ---- 用例 5：PDF 抽取器 scripts/pdf_extract.py ------------------------------
# pdf_extract.py 的契约写在它的模块 docstring 里：CLI 形态、输出文件名、头部注释字段、
# 每页 `<!-- page:N -->` 锚点、--pages 裁剪但**不重编号**、扫描页占位与告警、目录模式
# （默认一层 / --recursive）、退出码 0/1/2/3/4、依赖回退 pypdf → PyPDF2 → 3。
# 这里用 pdf-cases/ 下由 make_fixtures.py 生成的真实 PDF，一律**子进程**调用脚本，
# 断言 CLI 行为（而不是内部函数），因为用户与上游 harness 看到的就是 CLI。
PDF_SCRIPT = ROOT / "scripts" / "pdf_extract.py"
PDF_CASES = HERE / "pdf-cases"
PDF_FIXTURES = ["三页样例.pdf", "空白页样例.pdf", "加密样例.pdf", "假PDF.pdf"]
PAGE_ANCHOR_RE = re.compile(r"^<!-- page:(\d+) -->$")
SCAN_PLACEHOLDER_LINE = "> [本页无可提取文本层，可能是扫描件，需要 OCR]"

# 缺依赖场景的 wrapper：用 MetaPathFinder 把 pypdf / PyPDF2 的导入变成 ImportError，
# 再以 __main__ 运行被测脚本（不修改被测脚本、不真卸依赖）。
NODEP_WRAPPER = '''\
import importlib.abc
import runpy
import sys


class _Blocker(importlib.abc.MetaPathFinder):
    """让 pypdf / PyPDF2 无法导入，模拟两个后端都缺失的环境。"""

    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in ("pypdf", "PyPDF2"):
            raise ImportError("blocked by eval: " + fullname)
        return None


script, target = sys.argv[1], sys.argv[2]
sys.meta_path.insert(0, _Blocker())
sys.argv = ["pdf_extract.py", target]
runpy.run_path(script, run_name="__main__")
'''

case5_start = assertions


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_pdf(*args: object, cwd: Path | None = None) -> tuple[int, str, str]:
    """子进程运行 pdf_extract.py，返回 (退出码, stdout, stderr)。

    统一带 PYTHONDONTWRITEBYTECODE=1，避免在仓库里留下 __pycache__ 残留。
    """
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.run(
        [sys.executable, str(PDF_SCRIPT), *[str(a) for a in args]],
        cwd=str(cwd or PDF_WORK), capture_output=True, text=True,
        encoding="utf-8", errors="replace", env=env,
    )
    return proc.returncode, proc.stdout, proc.stderr


def anchor_lines(md: str) -> list[str]:
    """取出所有含 `<!-- page:` 的行（含格式不合规的行，便于断言"独占一行"）。"""
    return [line for line in md.split("\n") if "<!-- page:" in line]


def anchor_numbers(md: str) -> list[int]:
    """按出现顺序返回页锚点页码；格式不合规的锚点记为 -1，使断言直接失败。"""
    nums = []
    for line in anchor_lines(md):
        m = PAGE_ANCHOR_RE.match(line)
        nums.append(int(m.group(1)) if m else -1)
    return nums


def page_body(md: str, num: int) -> str:
    """返回 `<!-- page:N -->` 之后的第一个非空行；'--' 表示该锚点不存在，'' 表示锚点后没有正文。"""
    lines = md.split("\n")
    try:
        idx = lines.index(f"<!-- page:{num} -->")
    except ValueError:
        return "--"
    for line in lines[idx + 1:]:
        if line.strip():
            return line
    return ""


def read_md(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


PDF_WORK = Path(tempfile.mkdtemp(prefix="paper-reading-pdf-evals-"))
PDF_SRC_HASHES = {name: sha256_of(PDF_CASES / name) for name in PDF_FIXTURES if (PDF_CASES / name).is_file()}

expect("pdf-cases fixture 齐全（4 个 PDF + make_fixtures.py）",
       all((PDF_CASES / name).is_file() for name in PDF_FIXTURES) and (PDF_CASES / "make_fixtures.py").is_file(),
       f"实际 {sorted(p.name for p in PDF_CASES.glob('*'))}")

try:
    # fixture 一律复制到临时目录再跑：万一脚本行为回归到"写进 fixture 目录"，
    # 也不会污染仓库（并有独立断言检查仓库目录未被写入）。
    demo = PDF_WORK / "demo.pdf"
    shutil.copy2(PDF_CASES / "三页样例.pdf", demo)
    demo_hash = sha256_of(demo)

    # --- 正常路径：3 页样例，输出结构与正文 ---
    out1 = PDF_WORK / "out1"
    code, out, _err = run_pdf(demo, "--out", out1)
    expect("用例5 三页样例退出码为 0", code == 0, f"实际 {code}\n{out}")
    md1_path = out1 / "demo.md"
    expect("用例5 输出文件名为 <stem>.md（demo.pdf → demo.md）", md1_path.is_file(),
           f"{out1} 下实际: {sorted(p.name for p in out1.glob('*')) if out1.is_dir() else '目录不存在'}")
    expect("用例5 没有生成 demo.pdf.md（去掉扩展名而不是叠加）", not (out1 / "demo.pdf.md").exists(),
           f"{out1} 下实际: {sorted(p.name for p in out1.glob('*')) if out1.is_dir() else '目录不存在'}")
    md1 = read_md(md1_path)
    head1 = md1.split("\n")[:4]
    expect("用例5 头部含 source 字段 <!-- source: demo.pdf -->", head1[0] == "<!-- source: demo.pdf -->", f"头 4 行: {head1}")
    expect("用例5 头部含 pages 字段 <!-- pages: 3 -->", head1[1] == "<!-- pages: 3 -->", f"头 4 行: {head1}")
    expect("用例5 头部含 extracted 字段（ISO 时间戳）",
           bool(re.match(r"^<!-- extracted: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2} -->$", head1[2])),
           f"头 4 行: {head1}")
    expect("用例5 头部含 tool 字段 <!-- tool: pdf_extract.py -->", head1[3] == "<!-- tool: pdf_extract.py -->", f"头 4 行: {head1}")
    expect("用例5 头部四行元信息的顺序为 source/pages/extracted/tool", len(head1) == 4 and all(l.startswith("<!--") for l in head1),
           f"头 4 行: {head1}")
    expect("用例5 <!-- page:1 --> 恰好出现一次", md1.count("<!-- page:1 -->") == 1, md1)
    expect("用例5 <!-- page:2 --> 恰好出现一次", md1.count("<!-- page:2 -->") == 1, md1)
    expect("用例5 <!-- page:3 --> 恰好出现一次", md1.count("<!-- page:3 -->") == 1, md1)
    expect("用例5 页锚点按 1→2→3 递增排列", anchor_numbers(md1) == [1, 2, 3], f"实际 {anchor_numbers(md1)}\n{md1}")
    expect("用例5 每个页锚点独占一行（行内无其它内容）",
           len(anchor_lines(md1)) == 3 and all(PAGE_ANCHOR_RE.match(l) for l in anchor_lines(md1)),
           f"实际 {anchor_lines(md1)}\n{md1}")
    expect("用例5 第 1 页正文确实抽出了 PAGE ONE ALPHA", "PAGE ONE ALPHA" in md1, md1)
    expect("用例5 第 2 页正文确实抽出了 PAGE TWO BRAVO", "PAGE TWO BRAVO" in md1, md1)
    expect("用例5 第 3 页正文确实抽出了 PAGE THREE CHARLIE", "PAGE THREE CHARLIE" in md1, md1)
    expect("用例5 页锚点紧邻该页正文（锚点下一非空行就是正文）",
           [page_body(md1, n) for n in (1, 2, 3)]
           == ["PAGE ONE ALPHA", "PAGE TWO BRAVO", "PAGE THREE CHARLIE"],
           f"实际 {[page_body(md1, n) for n in (1, 2, 3)]}\n{md1}")

    # --- --pages 裁剪：只抽选中页，且页码保持物理页码不重编号 ---
    out2 = PDF_WORK / "out2"
    code, out, _err = run_pdf(demo, "--pages", "2", "--out", out2)
    md2 = read_md(out2 / "demo.md")
    expect("用例5 --pages 2 退出码为 0", code == 0, f"实际 {code}\n{out}")
    expect("用例5 --pages 2 只输出一个页锚点", len(anchor_lines(md2)) == 1, md2)
    expect("用例5 --pages 2 的锚点是物理页码 2（不是 1）", md2.count("<!-- page:2 -->") == 1 and anchor_numbers(md2) == [2],
           f"实际 {anchor_numbers(md2)}\n{md2}")
    expect("用例5 --pages 2 未把选中页重编号（无 page:1 / page:3 锚点）",
           "<!-- page:1 -->" not in md2 and "<!-- page:3 -->" not in md2, md2)
    expect("用例5 --pages 2 正文只含第 2 页标记词（不含第 1 页）",
           "PAGE TWO BRAVO" in md2 and "PAGE ONE ALPHA" not in md2, md2)
    expect("用例5 --pages 2 头部 pages 字段仍报 PDF 总页数 3", "<!-- pages: 3 -->" in md2, md2)

    # --- --pages= / --out= 等号写法（与空格写法同效） ---
    out3 = PDF_WORK / "out3"
    code, out, _err = run_pdf(demo, "--pages=2", f"--out={out3}")
    expect("用例5 --pages=2 / --out=DIR 等号写法可用且与空格写法同效",
           code == 0 and (out3 / "demo.md").is_file() and anchor_numbers(read_md(out3 / "demo.md")) == [2],
           f"实际 {code}\n{out}")

    # --- 退出码 2：--pages 越界与参数/路径错误 ---
    out_oob = PDF_WORK / "out_oob"
    code, out, _err = run_pdf(demo, "--pages", "9-10", "--out", out_oob)
    expect("用例5 --pages 9-10 越界退出码为 2", code == 2, f"实际 {code}\n{out}")
    expect("用例5 --pages 越界报错含「超出总页数 3」", "超出总页数 3" in out, out)
    expect("用例5 --pages 越界时不写输出文件", not out_oob.exists(), f"{out_oob} 存在")

    code, out, _err = run_pdf()
    expect("用例5 缺参数（无 argv）退出码为 2", code == 2, f"实际 {code}\n{out}")
    expect("用例5 缺参数时打印用法/帮助（含「用法:」与退出码说明）",
           "用法:" in out and "退出码:" in out and "--pages" in out, out)

    code, out, _err = run_pdf(demo, PDF_CASES / "三页样例.pdf")
    expect("用例5 两个位置参数退出码为 2", code == 2, f"实际 {code}\n{out}")
    expect("用例5 两个位置参数报错含「需要且只需要一个输入路径」并打印用法行",
           "需要且只需要一个输入路径" in out and "用法: python scripts/pdf_extract.py" in out, out)

    code, out, _err = run_pdf(demo, "--pages", "0")
    expect("用例5 --pages 0 退出码为 2（页码必须从 1 开始）", code == 2 and "必须从 1 开始" in out,
           f"实际 {code}\n{out}")

    code, out, _err = run_pdf(demo, "--bogus")
    expect("用例5 未知选项退出码为 2", code == 2 and "未知选项" in out, f"实际 {code}\n{out}")

    code, out, _err = run_pdf(demo, "--out=")
    expect("用例5 --out= 空值退出码为 2", code == 2 and "--out 不能为空" in out, f"实际 {code}\n{out}")

    code, out, _err = run_pdf(PDF_WORK / "不存在的.pdf")
    expect("用例5 路径不存在退出码为 2", code == 2 and "路径不存在" in out, f"实际 {code}\n{out}")

    not_pdf = PDF_WORK / "note.md"
    not_pdf.write_text("# 不是 PDF\n", encoding="utf-8", newline="\n")
    code, out, _err = run_pdf(not_pdf)
    expect("用例5 输入文件扩展名不是 .pdf 时退出码为 2", code == 2 and "输入不是 PDF 文件" in out,
           f"实际 {code}\n{out}")

    code, out, _err = run_pdf("-h")
    expect("用例5 -h 打印用法并以退出码 0 结束",
           code == 0 and "用法:" in out and "退出码:" in out, f"实际 {code}\n{out}")

    # --- 退出码 1：假 PDF（扩展名是 .pdf，内容不是 PDF） ---
    fake = PDF_WORK / "假PDF.pdf"
    shutil.copy2(PDF_CASES / "假PDF.pdf", fake)
    code, out, _err = run_pdf(fake, "--out", PDF_WORK / "out_fake")
    expect("用例5 假PDF.pdf 解析失败退出码为 1", code == 1, f"实际 {code}\n{out}")
    expect("用例5 假PDF.pdf 报错含 [ERROR] 无法解析 PDF", "[ERROR] 无法解析 PDF" in out, out)

    # --- 无文本层：扫描页告警 + 占位行，且退出码仍为 0 ---
    blank = PDF_WORK / "空白页样例.pdf"
    shutil.copy2(PDF_CASES / "空白页样例.pdf", blank)
    out_blank = PDF_WORK / "out_blank"
    code, out, _err = run_pdf(blank, "--out", out_blank)
    expect("用例5 空白页样例退出码为 0", code == 0, f"实际 {code}\n{out}")
    expect("用例5 空白页样例打印 [WARN ] 疑似扫描页", "[WARN ] 疑似扫描页" in out, out)
    expect("用例5 扫描页告警列出全部无文本层的页（p.1, p.2）", "p.1, p.2" in out, out)
    md_blank = read_md(out_blank / "空白页样例.md")
    expect("用例5 两个无文本层页各写一行占位", md_blank.count(SCAN_PLACEHOLDER_LINE) == 2, md_blank)
    expect("用例5 无文本层的页没有正文（除头部/锚点/占位外无内容行）",
           [l for l in md_blank.split("\n")
            if l.strip() and not l.startswith("<!--") and l != SCAN_PLACEHOLDER_LINE] == [],
           md_blank)

    # --- 退出码 4：加密 PDF，空密码解密失败 ---
    enc = PDF_WORK / "加密样例.pdf"
    shutil.copy2(PDF_CASES / "加密样例.pdf", enc)
    out_enc = PDF_WORK / "out_enc"
    code, out, _err = run_pdf(enc, "--out", out_enc)
    expect("用例5 加密样例退出码为 4", code == 4, f"实际 {code}\n{out}")
    expect("用例5 加密样例报错信息含「已加密」", "已加密" in out, out)
    expect("用例5 加密样例失败时不写输出文件", not out_enc.exists(), f"{out_enc} 存在")

    # --- 目录模式：默认一层 / --recursive 递归 ---
    dirtest = PDF_WORK / "dirtest"
    (dirtest / "sub").mkdir(parents=True)
    shutil.copy2(PDF_CASES / "三页样例.pdf", dirtest / "top.pdf")
    shutil.copy2(PDF_CASES / "三页样例.pdf", dirtest / "sub" / "nested.pdf")

    out_d1 = PDF_WORK / "out_dir1"
    code, out, _err = run_pdf(dirtest, "--out", out_d1)
    expect("用例5 目录模式默认处理该目录一层的 PDF（top.md 写出）",
           code == 0 and (out_d1 / "top.md").is_file(), f"实际 {code}\n{out}")
    expect("用例5 目录模式默认不递归子目录（nested.md 未生成）", not (out_d1 / "nested.md").exists(),
           f"{out_d1} 下实际: {sorted(p.name for p in out_d1.glob('*')) if out_d1.is_dir() else '目录不存在'}")

    out_d2 = PDF_WORK / "out_dir2"
    code, out, _err = run_pdf(dirtest, "--recursive", "--out", out_d2)
    expect("用例5 加 --recursive 后递归处理子目录（top.md 与 nested.md 都写出）",
           code == 0 and (out_d2 / "top.md").is_file() and (out_d2 / "nested.md").is_file(),
           f"实际 {code}\n{out}")

    # --- 输出位置：不给 --out 时默认 <PDF 所在目录>/_source/ ---
    solo_dir = PDF_WORK / "solo"
    solo_dir.mkdir()
    solo = solo_dir / "demo.pdf"
    shutil.copy2(PDF_CASES / "三页样例.pdf", solo)
    code, out, _err = run_pdf(solo)
    expect("用例5 不给 --out 时默认写到 <PDF 所在目录>/_source/<stem>.md",
           code == 0 and (solo_dir / "_source" / "demo.md").is_file(),
           f"实际 {code}，{solo_dir} 下: {sorted(p.name for p in solo_dir.iterdir())}\n{out}")

    # --- 空目录：不算失败，退出码 0 + [WARN ]（常是忘了 --recursive） ---
    empty_dir = PDF_WORK / "emptydir"
    empty_dir.mkdir()
    code, out, _err = run_pdf(empty_dir)
    expect("用例5 空目录（无 PDF）退出码为 0", code == 0, f"实际 {code}\n{out}")
    expect("用例5 空目录打印 [WARN ] 并提示 --recursive",
           "[WARN ]" in out and "没有 PDF 文件" in out and "--recursive" in out, out)

    code, out, _err = run_pdf(demo, "--pages", "abc")
    expect("用例5 --pages 格式非法（abc）退出码为 2", code == 2 and "格式非法" in out, f"实际 {code}\n{out}")

    code, out, _err = run_pdf(demo, "--pages", "9-3")
    expect("用例5 --pages 区间倒置（9-3）退出码为 2", code == 2 and "区间倒置" in out, f"实际 {code}\n{out}")

    # --- 疑似扫描页只统计**本次实际抽取**的页（给 --pages 时不额外扫全文） ---
    out_blank2 = PDF_WORK / "out_blank2"
    code, out, _err = run_pdf(blank, "--pages", "2", "--out", out_blank2)
    expect("用例5 空白页样例 --pages 2 退出码为 0", code == 0, f"实际 {code}\n{out}")
    expect("用例5 给 --pages 时扫描页告警只列选中页（p.2，不含 p.1）",
           "p.2" in out and "p.1" not in out, out)
    md_blank2 = read_md(out_blank2 / "空白页样例.md")
    expect("用例5 给 --pages 时占位行只出现在选中页（1 行）",
           md_blank2.count(SCAN_PLACEHOLDER_LINE) == 1 and anchor_numbers(md_blank2) == [2], md_blank2)

    # --- 目录模式下单个文件失败不影响其它文件，退出码取最大值 ---
    mixed = PDF_WORK / "mixeddir"
    mixed.mkdir()
    shutil.copy2(PDF_CASES / "假PDF.pdf", mixed / "bad.pdf")
    shutil.copy2(PDF_CASES / "三页样例.pdf", mixed / "good.pdf")
    out_mixed = PDF_WORK / "out_mixed"
    code, out, _err = run_pdf(mixed, "--out", out_mixed)
    expect("用例5 目录内单个文件失败时退出码取最大值（假PDF → 1）", code == 1, f"实际 {code}\n{out}")
    expect("用例5 目录内单个文件失败不影响其它文件（good.md 仍写出）",
           (out_mixed / "good.md").is_file() and not (out_mixed / "bad.md").exists(),
           f"{out_mixed} 下: {sorted(p.name for p in out_mixed.glob('*')) if out_mixed.is_dir() else '目录不存在'}\n{out}")

    # --- 退出码 3：pypdf 与 PyPDF2 都不可用 ---
    nodep_dir = PDF_WORK / "nodep"
    nodep_dir.mkdir()
    wrapper = nodep_dir / "run_without_pypdf.py"
    wrapper.write_text(NODEP_WRAPPER, encoding="utf-8", newline="\n")
    proc = subprocess.run(
        [sys.executable, str(wrapper), str(PDF_SCRIPT), str(demo)],
        cwd=str(nodep_dir), capture_output=True, text=True,
        encoding="utf-8", errors="replace", env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
    )
    expect("用例5 缺依赖（pypdf / PyPDF2 均不可导入）退出码为 3", proc.returncode == 3,
           f"实际 {proc.returncode}\n{proc.stdout}\n{proc.stderr}")
    expect("用例5 缺依赖时打印安装提示（pypdf 与 PyPDF2、pip install pypdf）",
           "缺少 PDF 解析依赖" in proc.stdout and "pip install pypdf" in proc.stdout
           and "PyPDF2" in proc.stdout, proc.stdout)
    expect("用例5 缺依赖时不产出任何输出文件", not (nodep_dir / "_source").exists()
           and sorted(p.name for p in nodep_dir.iterdir()) == ["run_without_pypdf.py"],
           f"{nodep_dir} 下: {sorted(p.name for p in nodep_dir.iterdir())}")

    # --- 只读契约与仓库清洁度 ---
    changed = [name for name, digest in PDF_SRC_HASHES.items() if sha256_of(PDF_CASES / name) != digest]
    expect("用例5 全部运行后仓库源 PDF 的 SHA-256 未变（脚本只读输入）", not changed, f"变化: {changed}")
    expect("用例5 全部运行后临时副本 demo.pdf 的 SHA-256 未变", sha256_of(demo) == demo_hash)
    expect("用例5 未在仓库 fixture 目录写入任何输出（含 _source）",
           not (PDF_CASES / "_source").exists()
           and sorted(p.name for p in PDF_CASES.glob("*")) == sorted(PDF_FIXTURES + ["make_fixtures.py"]),
           f"{PDF_CASES} 下: {sorted(p.name for p in PDF_CASES.glob('*'))}")
    pycache = sorted(str(p.relative_to(ROOT)) for p in ROOT.rglob("__pycache__"))
    expect("用例5 全程未产生 __pycache__ 残留", not pycache, f"残留: {pycache}")
finally:
    shutil.rmtree(PDF_WORK, ignore_errors=True)

expect("用例5 用例结束前临时目录与 wrapper 已全部清理", not PDF_WORK.exists(), f"{PDF_WORK} 仍然存在")

# ---- 用例 6：合集层索引 paper-notes/README.md（--mode index） ----------------
# 契约：首行非空内容恰为 `<!-- paper-reading: collection-index -->` 时 --mode auto 判为 index；
# 显式 --mode index 对缺标记文件同样生效（报 E-IDX-MARKER）。
# index-cases/ 只放索引 fixture（被链接的目标笔记 README.md 不算 fixture），
# 不放进 good-sample / warn-sample / bad-sample，避免干扰既有用例的完整性校验。
IDX_CASES = HERE / "index-cases"
IDX_DIRS = ("good", "warn", "bad", "orphan", "linked")
IDX_GOOD_REL = "good/索引.md"
# (相对 index-cases 的路径, 设计要触发的 ERROR 码, 关键消息片段)
IDX_BAD_CASES: list[tuple[str, str, str]] = [
    ("bad/索引-缺标记.md", "E-IDX-MARKER",
     "首行非空内容必须是 <!-- paper-reading: collection-index -->（合集索引的唯一识别标记）"),
    ("bad/索引-标题不合规.md", "E-IDX-H1",
     "必须是唯一的 H1「# <方向>论文笔记库」，实际：# 论文索引"),
    ("bad/索引-缺小节.md", "E-IDX-SEC", "缺少必备小节：## 五、证据强度总览"),
    ("bad/索引-链接不可达.md", "E-IDX-LINK",
     "第 11 行条目链接的目标文件不存在：./不存在的论文/README.md"),
    ("bad/索引-条目格式错.md", "E-IDX-ENTRY", "第 10 行条目缺少链接"),
    ("bad/索引-重复登记.md", "E-IDX-DUP", "链接目标重复登记：./某论文/README.md 共出现 2 次"),
    ("bad/索引-证据类型非法.md", "E-IDX-SRCKIND",
     "第 10 行条目证据类型「网文」非法，只允许 全文/摘要/二手/代码/OCR"),
]
# (相对 index-cases 的路径, 设计要触发的 WARN 码, 关键消息片段)
IDX_WARN_CASES: list[tuple[str, str, str]] = [
    ("warn/索引-缺更新行.md", "W-IDX-UPDATE",
     "缺少「最近更新」行（增量续写要留时间戳）：> 最近更新：YYYY-MM-DD"),
    ("warn/索引-术语表缺列.md", "W-IDX-TERM",
     "术语速查表表头必须恰为三列 | 术语 | 一句话解释 | 首次出现 |，实际：| 术语 | 一句话解释 |"),
]

case6_start = assertions


def run_index(rel: str, mode: str = "index") -> tuple[int, str]:
    return run_check(IDX_CASES / rel, mode)


def idx_codes(out: str, prefix: str) -> list[str]:
    """取出输出里出现的 <prefix>-XXX 码并去重排序（prefix 传 E-IDX / W-IDX）。"""
    return sorted(set(re.findall(r"\[(?:ERROR|WARN )\] (" + prefix + r"-[A-Z0-9-]+)", out)))


expect("index-cases/ 五个子目录齐全（good/warn/bad/orphan/linked）",
       all((IDX_CASES / d).is_dir() for d in IDX_DIRS),
       f"实际 {sorted(p.name for p in IDX_CASES.iterdir()) if IDX_CASES.is_dir() else '目录不存在'}")

idx_present = sorted(f"{d}/{p.name}" for d in IDX_DIRS for p in (IDX_CASES / d).glob("索引*.md"))
idx_covered = ({"good/索引.md", "orphan/索引.md", "linked/索引.md"}
               | {rel for rel, _, _ in IDX_BAD_CASES}
               | {rel for rel, _, _ in IDX_WARN_CASES})
expect("index-cases 每个索引 fixture 都在断言表内",
       bool(idx_present) and set(idx_present) <= idx_covered,
       f"未覆盖: {sorted(set(idx_present) - idx_covered)}")

# --- good：0 ERROR 0 WARN（10 项检查全过） ---
code, out = run_index(IDX_GOOD_REL)
expect("用例6 good/索引.md --mode index 退出码为 0", code == 0, f"实际 {code}\n{out}")
expect("用例6 good/索引.md 10 项检查全过（0 ERROR 0 WARN）",
       "[PASS ] 10 项检查全部通过" in out, out)
expect("用例6 good/索引.md 无 ERROR 行", "[ERROR]" not in out, out)
expect("用例6 good/索引.md 无 WARN 行", "[WARN ]" not in out, out)

# --- bad：退出码 1，且只报它设计的那一个 ERROR 码 ---
for rel, want_code, frag in IDX_BAD_CASES:
    code, out = run_index(rel)
    tag = f"index-cases/{rel} --mode index"
    expect(f"{tag} 退出码为 1", code == 1, f"实际 {code}\n{out}")
    expect(f"{tag} 命中 {want_code}：{frag}", f"[ERROR] {want_code} " in out and frag in out,
           f"输出未含 {want_code} / {frag}\n{out}")
    got = idx_codes(out, "E-IDX")
    expect(f"{tag} 只报 {want_code} 这一个 ERROR 码（实际 {got}）", got == [want_code], out)

# --- warn：退出码 0、无 ERROR，且只报它设计的那一个 WARN 码 ---
for rel, want_code, frag in IDX_WARN_CASES:
    code, out = run_index(rel)
    tag = f"index-cases/{rel} --mode index"
    expect(f"{tag} 退出码为 0", code == 0, f"实际 {code}\n{out}")
    expect(f"{tag} 无 ERROR 行", "[ERROR]" not in out, out)
    expect(f"{tag} 命中 {want_code}：{frag}", f"[WARN ] {want_code}" in out and frag in out,
           f"输出未含 {want_code} / {frag}\n{out}")
    got = idx_codes(out, "W-IDX")
    expect(f"{tag} 只报 {want_code} 这一个 WARN 码（实际 {got}）", got == [want_code], out)

# --- W-IDX-ORPHAN 的反向完整性：有笔记未登记才报，已登记不报（证明不是恒真） ---
code, out = run_index("orphan/索引.md")
expect("用例6 orphan/索引.md 有笔记未登记时退出码仍为 0（WARN 不改退出码）", code == 0,
       f"实际 {code}\n{out}")
expect("用例6 orphan/索引.md 命中 W-IDX-ORPHAN 且指名未登记的 某论文/README.md",
       "[WARN ] W-IDX-ORPHAN" in out and "某论文/README.md" in out, out)
expect("用例6 orphan/索引.md 不把已登记的 已登记论文 报成孤儿",
       "已登记论文/README.md" not in out, out)
code, out = run_index("linked/索引.md")
expect("用例6 linked/索引.md 唯一笔记已登记 → 0 ERROR 0 WARN（W-IDX-ORPHAN 不是恒真）",
       code == 0 and "[PASS ] 10 项检查全部通过" in out and "[WARN ]" not in out,
       f"实际 {code}\n{out}")

# --- --mode auto 的判定：带标记 → index（且与显式 --mode index 完全一致） ---
code_auto, out_auto = run_check(IDX_CASES / IDX_GOOD_REL, "auto")
code_idx, out_idx = run_check(IDX_CASES / IDX_GOOD_REL, "index")
expect("用例6 --mode auto 对带标记的 good/索引.md 判为 index（与显式 --mode index 输出一致）",
       code_auto == code_idx == 0 and out_auto == out_idx
       and "[PASS ] 10 项检查全部通过" in out_auto, f"{out_auto}\n---\n{out_idx}")
code_auto, out_auto = run_check(IDX_CASES / "warn" / "索引-缺更新行.md", "auto")
expect("用例6 --mode auto 对带标记的 warn/索引-缺更新行.md 同样判为 index",
       code_auto == 0 and "[WARN ] W-IDX-UPDATE" in out_auto, f"实际 {code_auto}\n{out_auto}")
code_auto, out_auto = run_check(IDX_CASES / "bad" / "索引-缺标记.md", "auto")
expect("用例6 缺标记文件不会被 auto 判为 index（不报任何 E-IDX-* 码）",
       "E-IDX-" not in out_auto, out_auto)

# ---- 用例 7：专业术语表 术语-<短名>.md（--mode terms） ----------------------
# 契约写在 check_paper_note.py 的 check_terms() 与 references/terms-template.md：
# 六节骨架 + 六列表头 + 11 个检查码；文件名词干含 `术语` 时 --mode auto 即判为 terms
# （不需要 index 那种 HTML 注释标记，所以 fixture 文件名一律 `术语-*.md`）。
# terms-cases/ 只放术语表 fixture（good/warn/bad 三个子目录），不放进
# good-sample / warn-sample / bad-sample，避免干扰既有用例的完整性校验。
TERMS_CASES = HERE / "terms-cases"
TERMS_DIRS = ("good", "warn", "bad")
TERMS_GOOD_REL = "good/术语-示例.md"
# (相对 terms-cases 的路径, 设计要触发的 ERROR 码, 关键消息片段)
TERMS_BAD_CASES: list[tuple[str, str, str]] = [
    # 删掉整个第五节 → 摘录条数必然为 0，连带 W-TERM-QUOTE（WARN 不影响退出码，
    # 下面的断言只要求 ERROR 码集合恰为设计的那一个）
    ("bad/术语-缺小节.md", "E-TERM-SEC", "缺少必备小节：## 五、英文原句摘录"),
    ("bad/术语-标题不合规.md", "E-TERM-H1",
     "首个非空行必须是唯一的 H1「# <短名> 专业术语表（中英对照）」，实际：# 特征层动量攻击术语表"),
    ("bad/术语-列数不符.md", "E-TERM-TABLE", "第 48 行数据是 5 列，六列表头要求 6 列"),
    ("bad/术语-英文缺失.md", "E-TERM-EN",
     "第 36 行「英文术语」列缺少英文原词（必须含拉丁字母）：攻击成功率"),
    ("bad/术语-出处非法.md", "E-TERM-CITE",
     "第 38 行「出处」列不是合法来源标记（[原文 p.7] 这类带页码形式合法）：[不明来源]"),
    ("bad/术语-空列.md", "E-TERM-EMPTY", "第 37 行这些列为空或占位符：一句话解释"),
    ("bad/术语-重复登记.md", "E-TERM-DUP",
     "同一英文术语重复登记 2 次（第 19、28 行）：transferability"),
]
# (相对 terms-cases 的路径, 设计要触发的 WARN 码, 关键消息片段)
TERMS_WARN_CASES: list[tuple[str, str, str]] = [
    ("warn/术语-条数不足.md", "W-TERM-MIN", "二、三两节合计只有 12 行术语，少于 15 行"),
    ("warn/术语-摘录不足.md", "W-TERM-QUOTE", "第五节英文原句摘录只有 3 条合格条目"),
    ("warn/术语-悬空缩写.md", "W-TERM-ABBR", "悬空缩写）：TI-FGSM"),
    ("warn/术语-缩写乱序.md", "W-TERM-SORT", "缩略语索引未按字母升序排列"),
]

case7_start = assertions


def run_terms(rel: str, mode: str = "terms") -> tuple[int, str]:
    return run_check(TERMS_CASES / rel, mode)


def term_codes(out: str, level: str) -> list[str]:
    """取出输出里 level（E / W）级的 TERM 码并去重排序。"""
    return sorted(set(re.findall(r"\[(?:ERROR|WARN )\] (" + level + r"-TERM-[A-Z0-9-]+)", out)))


expect("terms-cases/ 三个子目录齐全（good/warn/bad）",
       all((TERMS_CASES / d).is_dir() for d in TERMS_DIRS),
       f"实际 {sorted(p.name for p in TERMS_CASES.iterdir()) if TERMS_CASES.is_dir() else '目录不存在'}")

terms_present = sorted(p.relative_to(TERMS_CASES).as_posix() for p in TERMS_CASES.rglob("*.md"))
terms_covered = ({TERMS_GOOD_REL}
                 | {rel for rel, _, _ in TERMS_BAD_CASES}
                 | {rel for rel, _, _ in TERMS_WARN_CASES})
expect("terms-cases 每个 .md fixture 都在断言表内",
       bool(terms_present) and set(terms_present) <= terms_covered,
       f"未覆盖: {sorted(set(terms_present) - terms_covered)}")

# --- good：0 ERROR 0 WARN（11 项检查全过） ---
code_good, out_good = run_terms(TERMS_GOOD_REL)
expect("用例7 good/术语-示例.md --mode terms 退出码为 0", code_good == 0, f"实际 {code_good}\n{out_good}")
expect("用例7 good/术语-示例.md 11 项检查全过（check_terms 的 executed 计数没被静默减项）",
       "[PASS ] 11 项检查全部通过" in out_good, out_good)
expect("用例7 good/术语-示例.md 输出以 [PASS ] 11 项检查全部通过 结尾",
       out_good.strip().endswith("[PASS ] 11 项检查全部通过"), out_good)
expect("用例7 good/术语-示例.md 无 ERROR 行", "[ERROR]" not in out_good, out_good)
expect("用例7 good/术语-示例.md 无 WARN 行", "[WARN ]" not in out_good, out_good)
expect("用例7 good/术语-示例.md 未命任何 E-TERM-* 码（实际 "
       f"{term_codes(out_good, 'E')}）", term_codes(out_good, "E") == [], out_good)
expect("用例7 good/术语-示例.md 未命任何 W-TERM-* 码（实际 "
       f"{term_codes(out_good, 'W')}）", term_codes(out_good, "W") == [], out_good)

# --- bad：退出码 1，且只报它设计的那一个 ERROR 码 ---
for rel, want_code, frag in TERMS_BAD_CASES:
    code, out = run_terms(rel)
    tag = f"terms-cases/{rel} --mode terms"
    expect(f"{tag} 退出码为 1", code == 1, f"实际 {code}\n{out}")
    expect(f"{tag} 命中 {want_code}：{frag}", f"[ERROR] {want_code} " in out and frag in out,
           f"输出未含 {want_code} / {frag}\n{out}")
    got = term_codes(out, "E")
    expect(f"{tag} 命中的 ERROR 码集合恰为 [{want_code}]（实际 {got}）", got == [want_code], out)

# --- warn：退出码 0、无 ERROR，且只报它设计的那一个 WARN 码 ---
for rel, want_code, frag in TERMS_WARN_CASES:
    code, out = run_terms(rel)
    tag = f"terms-cases/{rel} --mode terms"
    expect(f"{tag} 退出码为 0（WARN 不改退出码）", code == 0, f"实际 {code}\n{out}")
    expect(f"{tag} 未命任何 E- 码（实际 {term_codes(out, 'E')}）", term_codes(out, "E") == [], out)
    expect(f"{tag} 命中 {want_code}：{frag}", f"[WARN ] {want_code}" in out and frag in out,
           f"输出未含 {want_code} / {frag}\n{out}")
    got = term_codes(out, "W")
    expect(f"{tag} 命中的 WARN 码集合恰为 [{want_code}]（实际 {got}）", got == [want_code], out)

# --- --mode auto 的判定：文件名词干含 `术语` → terms（与显式 --mode terms 逐字一致） ---
for rel in terms_present:
    code_auto, out_auto = run_check(TERMS_CASES / rel, "auto")
    code_terms, out_terms = run_check(TERMS_CASES / rel, "terms")
    expect(f"用例7 --mode auto 对 {rel} 判为 terms（退出码与输出与 --mode terms 逐字一致）",
           code_auto == code_terms and out_auto == out_terms,
           f"auto {code_auto}:\n{out_auto}\n--- terms {code_terms}:\n{out_terms}")

# --- 带页码出处的口径守卫：模板说合法，校验器就必须认（FAQ_CITE_RE 那类不一致不许复发） ---
terms_good_text = read_md(TERMS_CASES / TERMS_GOOD_REL)
terms_tpl_text = read_md(ROOT / "references" / "terms-template.md")
expect("用例7 good fixture 同时用到 [原文 p.7] 与 [原文 p.7-8]（这条守卫不是空转）",
       "[原文 p.7]" in terms_good_text and "[原文 p.7-8]" in terms_good_text,
       terms_good_text)
expect("用例7 模板 references/terms-template.md 仍把 [原文 p.7] / [原文 p.7-8] 写成合法出处",
       "[原文 p.7]" in terms_tpl_text and "[原文 p.7-8]" in terms_tpl_text, terms_tpl_text)
expect("用例7 带页码出处过校验：good fixture 0 ERROR 且不含 E-TERM-CITE",
       code_good == 0 and "E-TERM-CITE" not in out_good, out_good)

# ---- 汇总 ------------------------------------------------------------------
print(f"\n[INFO ] 断言总数: {assertions}（用例 1-4：{case5_start}，"
      f"用例 5 PDF 抽取器：{case6_start - case5_start}，用例 6 合集索引：{case7_start - case6_start}，"
      f"用例 7 专业术语表：{assertions - case7_start}）")
if failures:
    print(f"\n[FAIL ] {len(failures)} 条断言未过：")
    for f_ in failures:
        print(f"  - {f_}")
    print("回归门禁未过：禁止升版本，先修复 check_paper_note.py / 模板 / fixture。")
    sys.exit(1)
print("\n[PASS ] 回归门禁全过：校验器与 good/bad 样本一致，可以进入人工 review。")
sys.exit(0)
