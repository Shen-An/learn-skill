#!/usr/bin/env python3
r"""pdf_extract.py — 把 PDF 论文抽成带页码锚点的 Markdown 纯文本，供 paper-reading skill 做可核查精读。

定位: paper-reading skill 的**可移植回退通道**。harness 自带文档读取能力（如 DSH 的 read_document）时优先用它；
      本脚本在 DSH / Claude Code / Codex 等 harness 里用同一份标准库 + pypdf 依赖即可运行。

用法:
    python scripts/pdf_extract.py <输入.pdf | 目录> [--out <目录>] [--pages 1-20 | --pages 3] [--recursive]

参数:
    <输入.pdf | 目录>  单个 PDF；或目录（默认只处理该目录一层的 *.pdf，加 --recursive 递归子目录）
    --out <目录>       输出目录；缺省为 "<PDF 所在目录>\_source"，不存在时自动创建
    --pages <范围>     只抽指定页：闭区间 "1-20" 或单页 "3"（1-based）；越界或格式非法 → 退出码 2
    --recursive        目录输入时递归子目录
    -h, --help         打印本说明

输出: <输出目录>\<PDF 主文件名>.md（去掉扩展名，demo.pdf → demo.md），结构::

    <!-- source: demo.pdf -->
    <!-- pages: 3 -->
    <!-- extracted: 2025-01-01T12:00:00+08:00 -->
    <!-- tool: pdf_extract.py -->

    <!-- page:1 -->
    Page one content about adversarial transferability.

    <!-- page:2 -->
    ...

  * 头部 4 行用 HTML 注释承载元信息，不污染正文解析。
  * 页标记 `<!-- page:N -->` 独占一行、位于该页正文之前，N 是 PDF **物理页码**；--pages 只裁剪输出范围，不改页码。
  * 某页没有文本层时，在页标记之后写一行 "> [本页无可提取文本层，可能是扫描件，需要 OCR]"。
  * 清洗规则: 去掉每行行尾空白；连续 >=3 个空行压缩为 1 个空行；不合并段落，保留原换行。

依赖: 优先 pypdf，其次 PyPDF2（两者 API 基本一致）；两者都不可用时打印安装提示并以退出码 3 退出。

退出码:
    0  全部成功
    1  运行期失败（PDF 解析失败 / 读页数失败 / 写文件失败；契约未定义，用 1 表示）
    2  参数或路径错误：缺参数、未知选项、--pages 格式非法或越界、路径不存在、输入文件不是 .pdf
    3  缺少依赖：pypdf 与 PyPDF2 均不可用
    4  PDF 已加密，且空密码解密失败

实现注记（可预期的取舍）:
    * 只读输入文件，绝不改写输入；不联网；除输出目录外不写任何路径（不建缓存、不落临时文件）。
    * 目录输入时逐文件处理、单个文件失败不影响其它文件；最终退出码取各文件退出码的最大值
      （单个 PDF 输入时即该文件的退出码，故 --pages 越界在单文件模式下就是 2）。
    * 目录下没有任何 PDF 不算失败: 打印 [WARN ] 并返回 0（常是忘了 --recursive）。
    * 疑似扫描页只统计**本次实际抽取**的页: 给了 --pages 时就只覆盖被选中的页，不额外扫全文。
    * --recursive 时不同子目录下的同名 PDF 会写到同一个输出文件名，后者覆盖前者。
    * 一张图片型的整页（无文本层）只会得到占位行；脚本不做 OCR，OCR 交给上游流程决定。
"""
from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path

try:  # Windows GBK 控制台防御：保证中文输出不抛 UnicodeEncodeError
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:  # 依赖回退：优先 pypdf，其次 PyPDF2（两者 API 基本一致，共用同一套调用代码）
    from pypdf import PdfReader

    BACKEND = "pypdf"
except ImportError:
    try:
        from PyPDF2 import PdfReader

        BACKEND = "PyPDF2"
    except ImportError:
        PdfReader = None  # type: ignore[assignment]
        BACKEND = None

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_USAGE = 2
EXIT_NO_DEP = 3
EXIT_ENCRYPTED = 4

USAGE = "python scripts/pdf_extract.py <输入.pdf | 目录> [--out <目录>] [--pages 1-20 | --pages 3] [--recursive]"

NO_DEP_MSG = (
    "[ERROR] 缺少 PDF 解析依赖：pypdf 与 PyPDF2 均不可用，无法提取文本。\n"
    "        请先安装（推荐 pypdf）：\n"
    "            pip install pypdf\n"
    "        受限环境可用：pip install --user pypdf（或 pip install PyPDF2）"
)

SCAN_PLACEHOLDER = "> [本页无可提取文本层，可能是扫描件，需要 OCR]"
PAGES_SPEC_RE = re.compile(r"^(\d+)(?:-(\d+))?$")


class UsageError(Exception):
    """命令行参数错误（对应退出码 2）。"""


def parse_args(argv: list[str]) -> dict:
    """解析命令行，返回 {input, out, pages, recursive}；参数错误抛 UsageError。"""
    positional: list[str] = []
    out: str | None = None
    pages: str | None = None
    recursive = False
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--out":
            i += 1
            if i >= len(argv):
                raise UsageError("--out 缺少目录参数")
            out = argv[i]
        elif arg.startswith("--out="):
            out = arg.split("=", 1)[1]
        elif arg == "--pages":
            i += 1
            if i >= len(argv):
                raise UsageError("--pages 缺少页码范围")
            pages = argv[i]
        elif arg.startswith("--pages="):
            pages = arg.split("=", 1)[1]
        elif arg == "--recursive":
            recursive = True
        elif arg.startswith("-"):
            raise UsageError(f"未知选项: {arg}")
        else:
            positional.append(arg)
        i += 1
    if len(positional) != 1:
        raise UsageError(f"需要且只需要一个输入路径（PDF 或目录），实际收到 {len(positional)} 个")
    if out is not None and out.strip() == "":
        raise UsageError("--out 不能为空")
    return {
        "input": Path(positional[0]),
        "out": Path(out) if out else None,
        "pages": pages,
        "recursive": recursive,
    }


def parse_page_range(spec: str) -> tuple[int, int]:
    """把 '1-20' / '3' 解析成 (start, end)；格式非法或区间倒置抛 UsageError。"""
    m = PAGES_SPEC_RE.match(spec.strip())
    if not m:
        raise UsageError(f"--pages 格式非法: {spec!r}（应为 1-20 或 3）")
    start = int(m.group(1))
    end = int(m.group(2)) if m.group(2) is not None else start
    if start < 1 or end < 1:
        raise UsageError(f"--pages 页码必须从 1 开始: {spec!r}")
    if start > end:
        raise UsageError(f"--pages 区间倒置: {spec!r}（应写 3-9 而不是 9-3）")
    return start, end


def format_range(start: int, end: int) -> str:
    """把 (start, end) 还原成人类可读的页码范围文本。"""
    return str(start) if start == end else f"{start}-{end}"


def collect_pdfs(root: Path, recursive: bool) -> list[Path]:
    """收集待处理 PDF：默认只取该目录一层，recursive 时递归子目录；按路径排序保证输出稳定。"""
    it = root.rglob("*") if recursive else root.glob("*")
    pdfs = [p for p in it if p.is_file() and p.name.lower().endswith(".pdf")]
    return sorted(pdfs, key=lambda p: str(p).lower())


def clean_page_text(raw: str | None) -> str:
    """每行去行尾空白；连续 >=3 个空行压缩为 1 个空行；保留原文换行，不合并段落。"""
    text = (raw or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    out: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        if lines[i] != "":
            out.append(lines[i])
            i += 1
            continue
        j = i
        while j < n and lines[j] == "":
            j += 1
        run = j - i
        out.extend([""] * (1 if run >= 3 else run))
        i = j
    return "\n".join(out).strip("\n")


def resolve_out_path(pdf_path: Path, out_dir: Path | None) -> Path:
    r"""默认 <PDF 所在目录>\_source\<PDF 主文件名>.md；给了 --out 则 <out>\<PDF 主文件名>.md。"""
    base = out_dir if out_dir is not None else pdf_path.parent / "_source"
    return base / f"{pdf_path.stem}.md"


def render_markdown(source_name: str, total_pages: int, blocks: list[tuple[int, str]]) -> str:
    """拼装 Markdown 文本：4 行头部注释 + 逐页（页标记独占一行，页间空行分隔）。"""
    stamp = datetime.now().astimezone().isoformat(timespec="seconds")
    parts = [
        f"<!-- source: {source_name} -->",
        f"<!-- pages: {total_pages} -->",
        f"<!-- extracted: {stamp} -->",
        "<!-- tool: pdf_extract.py -->",
        "",
    ]
    for num, body in blocks:
        parts.append(f"<!-- page:{num} -->")
        parts.append(body)
        parts.append("")
    return "\n".join(parts).rstrip("\n") + "\n"


def extract_one(
    pdf_path: Path, out_dir: Path | None, page_range: tuple[int, int] | None
) -> tuple[int, dict]:
    """抽取单个 PDF，返回 (退出码, 汇总信息)。

    退出码: 0 成功 / 1 解析或写入失败 / 2 页码范围越界 / 4 已加密。
    """
    info = {
        "name": pdf_path.name,
        "path": pdf_path,
        "total": 0,
        "scanned": [],
        "out": "",
        "status": "",
    }
    try:
        reader = PdfReader(str(pdf_path))
    except Exception as exc:  # 损坏/非 PDF 的异常类型不定，必须兜住并如实报错（不静默）
        print(f"[ERROR] 无法解析 PDF: {pdf_path} ({exc!r})")
        info["status"] = "无法解析"
        return EXIT_FAIL, info

    if reader.is_encrypted:
        unlocked = False
        try:  # 先尝试空密码解密（很多 PDF 只是设了空用户口令）
            unlocked = bool(reader.decrypt(""))
        except Exception as exc:
            print(f"[WARN ] 空密码解密抛出异常: {exc!r}")
        if not unlocked:
            print("[ERROR] 该 PDF 已加密，无法提取")
            info["status"] = "已加密"
            return EXIT_ENCRYPTED, info

    try:
        total = len(reader.pages)
    except Exception as exc:
        print(f"[ERROR] 无法读取页数: {pdf_path} ({exc!r})")
        info["status"] = "无法解析"
        return EXIT_FAIL, info
    info["total"] = total

    if page_range is None:
        selected = list(range(1, total + 1))
    else:
        start, end = page_range
        if end > total:
            print(f"[ERROR] --pages {format_range(start, end)} 超出总页数 {total}: {pdf_path}")
            info["status"] = f"页码越界（共 {total} 页）"
            return EXIT_USAGE, info
        selected = list(range(start, end + 1))

    blocks: list[tuple[int, str]] = []
    scanned: list[int] = []
    for num in selected:
        raw = ""
        try:
            raw = reader.pages[num - 1].extract_text() or ""
        except Exception as exc:
            print(f"[WARN ] p.{num} 文本提取抛出异常，按空页处理: {exc!r}")
        body = clean_page_text(raw)
        if not body.strip():
            scanned.append(num)
            body = SCAN_PLACEHOLDER
        blocks.append((num, body))
    info["scanned"] = scanned

    out_path = resolve_out_path(pdf_path, out_dir)
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            render_markdown(pdf_path.name, total, blocks), encoding="utf-8", newline="\n"
        )
    except OSError as exc:
        print(f"[ERROR] 写文件失败: {out_path} ({exc})")
        info["status"] = "写文件失败"
        return EXIT_FAIL, info

    info["out"] = str(out_path)
    info["status"] = f"OK（写出 {len(blocks)} 页）"
    if scanned:
        pages_text = ", p.".join(str(n) for n in scanned)
        print(f"[WARN ] 疑似扫描页（无可提取文本层，需要 OCR）: {pdf_path.name} p.{pages_text}")
    return EXIT_OK, info


def print_summary(results: list[tuple[int, dict]]) -> None:
    """打印汇总表: 文件 | 总页数 | 疑似扫描页 | 输出路径 | 状态。"""
    print()
    print("| 文件 | 总页数 | 疑似扫描页 | 输出路径 | 状态 |")
    print("| --- | --- | --- | --- | --- |")
    for _code, info in results:
        out = str(info["out"]) if info["out"] else "-"
        print(f"| {info['name']} | {info['total']} | {len(info['scanned'])} | {out} | {info['status']} |")
    ok = sum(1 for code, _info in results if code == EXIT_OK)
    scanned_total = sum(len(info["scanned"]) for _code, info in results)
    print(
        f"\n[SUMMARY] 共 {len(results)} 个文件：成功 {ok}，失败 {len(results) - ok}；"
        f"疑似扫描页合计 {scanned_total} 页。"
    )


def main(argv: list[str] | None = None) -> int:
    """脚本入口，返回进程退出码（0/1/2/3/4，含义见模块 docstring）。"""
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print(__doc__)
        return EXIT_USAGE
    if "-h" in argv or "--help" in argv:
        print(__doc__)
        return EXIT_OK

    try:
        opts = parse_args(argv)
        page_range = parse_page_range(opts["pages"]) if opts["pages"] is not None else None
    except UsageError as exc:
        print(f"[ERROR] {exc}")
        print(f"用法: {USAGE}")
        return EXIT_USAGE

    if PdfReader is None:  # 依赖缺失比路径问题更靠前：没有依赖，任何输入都处理不了
        print(NO_DEP_MSG)
        return EXIT_NO_DEP

    target: Path = opts["input"]
    if target.is_dir():
        pdfs = collect_pdfs(target, opts["recursive"])
        if not pdfs:
            hint = "" if opts["recursive"] else "（未扫描子目录；需要时加 --recursive）"
            print(f"[WARN ] 目录下没有 PDF 文件: {target}{hint}")
            print_summary([])
            return EXIT_OK
    elif target.is_file():
        if target.suffix.lower() != ".pdf":
            print(f"[ERROR] 输入不是 PDF 文件: {target}")
            return EXIT_USAGE
        pdfs = [target]
    else:
        print(f"[ERROR] 路径不存在: {target}")
        return EXIT_USAGE

    print(f"[INFO ] PDF 解析后端: {BACKEND}")
    results: list[tuple[int, dict]] = []
    for pdf in pdfs:
        code, info = extract_one(pdf, opts["out"], page_range)
        results.append((code, info))
        if code == EXIT_OK:
            print(f"[OK   ] {info['name']}: {info['status']} → {info['out']}")

    print_summary(results)
    return max((code for code, _info in results), default=EXIT_OK)


if __name__ == "__main__":
    sys.exit(main())
