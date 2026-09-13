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


def expect(name: str, cond: bool, detail: str = ""):
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

# ---- 汇总 ------------------------------------------------------------------
if failures:
    print(f"\n[FAIL ] {len(failures)} 条断言未过：")
    for f_ in failures:
        print(f"  - {f_}")
    print("回归门禁未过：禁止升版本，先修复 check_paper_note.py / 模板 / fixture。")
    sys.exit(1)
print("\n[PASS ] 回归门禁全过：校验器与 good/bad 样本一致，可以进入人工 review。")
sys.exit(0)
