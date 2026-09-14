#!/usr/bin/env python3
r"""make_fixtures.py — 生成 evals/pdf-cases/ 下 scripts/pdf_extract.py 的 PDF 回归 fixture。

fixture 由此脚本生成，重跑应产出语义相同的结果（同样的页数、同样的可抽取文本、
同样的加密状态；加密样本因随机盐不会逐字节相同）。不要手写这些二进制 PDF，
也不要手改本目录里的 PDF；需要调整时改本脚本后重跑:

    python evals/pdf-cases/make_fixtures.py            # 写入脚本所在目录
    python evals/pdf-cases/make_fixtures.py <输出目录>  # 写入指定目录（便于核对）

产物（默认写在脚本所在目录）:
    三页样例.pdf    3 页，每页一句纯 ASCII 已知文本:
                    PAGE ONE ALPHA / PAGE TWO BRAVO / PAGE THREE CHARLIE
                    → 正常路径: 抽文本、页码锚点、--pages 裁剪
    空白页样例.pdf  2 页无文本层（第 1 页完全空白，第 2 页只有一个填充矩形）
                    → 扫描页告警 + 占位行
    加密样例.pdf    由三页样例.pdf 复制并加非空 user password,
                    → 空密码解密失败, 对应退出码 4
    假PDF.pdf      内容是普通 Markdown 文本，但扩展名是 .pdf
                    → 解析失败, 对应退出码 1

依赖: 仅标准库 + pypdf（与 scripts/pdf_extract.py 同一依赖；两者都不可用时本脚本
      无从生成 fixture，直接报错退出 3）。
"""
from __future__ import annotations

import sys
from pathlib import Path

try:  # Windows GBK 控制台防御（与 scripts/pdf_extract.py 一致）
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import (
        ArrayObject,
        DecodedStreamObject,
        DictionaryObject,
        NameObject,
        NumberObject,
    )
except ImportError:  # 缺依赖时明确报错，不产出半成品 fixture
    print("[ERROR] 缺少 pypdf：pip install pypdf")
    sys.exit(3)

PAGE_TEXTS = ["PAGE ONE ALPHA", "PAGE TWO BRAVO", "PAGE THREE CHARLIE"]
USER_PASSWORD = "paper-reading-fixture"

FAKE_PDF_TEXT = """# 这不是 PDF

这是一份普通 Markdown 文本，只是扩展名被改成了 .pdf，
用来触发 pdf_extract.py 的解析失败分支（退出码 1）。

- 没有 %PDF- 文件头
- 没有 xref 表
- pypdf 应在 PdfReader 构造阶段抛异常
"""


def _font_resources() -> DictionaryObject:
    """标准 Type1 Helvetica（无需内嵌字体文件），供内容流的 Tj 使用。"""
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
            NameObject("/Encoding"): NameObject("/WinAnsiEncoding"),
        }
    )
    return DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})})


def _add_text_page(writer: PdfWriter, text: str):
    """加一页 612x792，用内容流写一行 24pt 文本（纯 ASCII，可被 pypdf 抽出）。"""
    page = writer.add_blank_page(width=612, height=792)
    stream = DecodedStreamObject()
    stream.set_data(f"BT /F1 24 Tf 72 700 Td ({text}) Tj ET".encode("latin-1"))
    page[NameObject("/Resources")] = _font_resources()
    page[NameObject("/Contents")] = writer._add_object(stream)
    return page


def build_three_page(path: Path) -> None:
    """三页样例: 每页一句纯 ASCII 已知文本。"""
    writer = PdfWriter()
    for text in PAGE_TEXTS:
        _add_text_page(writer, text)
    with path.open("wb") as fh:
        writer.write(fh)


def build_blank_pages(path: Path) -> None:
    """空白页样例: 2 页都没有文本层（第 2 页有图形内容但没有 BT/Tj）。"""
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    page = writer.add_blank_page(width=612, height=792)
    stream = DecodedStreamObject()
    stream.set_data(b"0.2 0.2 0.2 rg 100 400 400 300 re f")
    page[NameObject("/Contents")] = writer._add_object(stream)
    with path.open("wb") as fh:
        writer.write(fh)


def build_encrypted(src: Path, path: Path) -> None:
    """加密样例: 从三页样例复制页面，加非空 user password（空密码解密必须失败）。"""
    reader = PdfReader(str(src))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(user_password=USER_PASSWORD, owner_password=USER_PASSWORD)
    with path.open("wb") as fh:
        writer.write(fh)


def verify(out_dir: Path) -> int:
    """生成后自检: 打印每个 fixture 的页数与 pypdf 实际能抽到的文本，便于人工核对。"""
    expected = [
        ("三页样例.pdf", "3 页且能抽出 PAGE ONE/TWO/THREE"),
        ("空白页样例.pdf", "2 页且抽不到文本"),
        ("加密样例.pdf", "已加密且空密码解不开"),
        ("假PDF.pdf", "pypdf 无法解析"),
    ]
    print("[INFO ] 生成后自检:")
    for name, _note in expected:
        target = out_dir / name
        if not target.is_file():
            print(f"[FAIL ] {name}: 未生成")
            return 1
        if name == "假PDF.pdf":
            try:
                PdfReader(str(target))
            except Exception as exc:
                print(f"[OK   ] {name} ({target.stat().st_size} B): 无法解析 {type(exc).__name__}")
            else:
                print(f"[FAIL ] {name}: 竟然被解析成功了")
                return 1
            continue
        reader = PdfReader(str(target))
        if reader.is_encrypted:
            unlocked = reader.decrypt("")
            print(f"[OK   ] {name} ({target.stat().st_size} B): 已加密，空密码解密={unlocked}")
            continue
        texts = [(page.extract_text() or "").strip() for page in reader.pages]
        print(f"[OK   ] {name} ({target.stat().st_size} B): {len(texts)} 页，文本={texts}")
    print("[PASS ] fixture 自检完成")
    return 0


def main(argv: list[str]) -> int:
    out_dir = Path(argv[1]).resolve() if len(argv) > 1 else Path(__file__).resolve().parent
    out_dir.mkdir(parents=True, exist_ok=True)

    three = out_dir / "三页样例.pdf"
    build_three_page(three)
    build_blank_pages(out_dir / "空白页样例.pdf")
    build_encrypted(three, out_dir / "加密样例.pdf")
    (out_dir / "假PDF.pdf").write_text(FAKE_PDF_TEXT, encoding="utf-8", newline="\n")
    print(f"[INFO ] fixture 已写入 {out_dir}")
    return verify(out_dir)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
