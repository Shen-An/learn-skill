#!/usr/bin/env python3
r"""check_paper_note.py — 对 paper-reading skill 产出的论文学术笔记做机械校验。

用法:
    python scripts/check_paper_note.py <markdown文件> [--mode auto|deep|table|mindmap|mmd|faq|review|index|terms] [--refs N]

模式判定 --mode auto（默认，顺序敏感）:
    首行非空内容恰为 `<!-- paper-reading: collection-index -->` → index（该标记检查先于文件名词干判定）；
    含 深读/精读 → deep；含 表格/填表 → table；含 思维导图 → mindmap；
    否则含 导图/mermaid/mmd → mmd；含 难点/问答/faq（大小写不敏感）→ faq；含 综述 → review；
    含 术语/terms（大小写不敏感）→ terms（token 与上面各项都不重叠，故不会抢走 导图/难点 等既有 token）；
    都没有时按内容启发式: 出现 `## 研究背景与目标` → mindmap；只有一张 `| 维度 | 内容 |` 表 → table；
    出现 `## 研究主题概述` → review；否则 deep。
--refs N 仅 review 模式使用，表示可用文献编号范围 1..N；未给出时取正文出现的最大编号。

检查项（E 必修，W 酌情）:
  deep:    E-DEEP-H1 / E-DEEP-SUM / E-DEEP-SEC / E-DEEP-MATH / E-DEEP-MATH-LINE / E-DEEP-INLINE
           E-DEEP-WRAP / E-DEEP-TABLE / E-DEEP-MIX
           W-DEEP-SRC / W-DEEP-SRC-KIND / W-DEEP-PAGE / W-DEEP-SYM / W-DEEP-TONE / W-DEEP-CITE
  table:   E-TBL-ONLY / E-TBL-HEAD / E-TBL-DIM / E-TBL-EMPTY / E-TBL-LEN / E-TBL-FMT
  mindmap: E-MM-ROOT / E-MM-BRANCH / E-MM-FENCE / E-MM-DEPTH / E-MM-EMPTY / W-MM-BLOAT
  mmd:     E-MMD-H1 / E-MMD-FENCE / E-MMD-KEYWORD / E-MMD-ROOT / E-MMD-BRANCH / E-MMD-DEPTH
           E-MMD-SYNTAX / W-MMD-BLOAT / W-MMD-TEXT
  faq:     E-FAQ-H1 / E-FAQ-SEC / E-FAQ-FIELD / E-FAQ-CITE / E-FAQ-DUP
           W-FAQ-MISCONCEPT / W-FAQ-SELFCHECK / W-FAQ-SHORT / W-FAQ-TONE
  review:  E-RV-SEC / E-RV-CITE / E-RV-NOREF / W-RV-DENSITY / W-RV-GAP
  index:   E-IDX-MARKER / E-IDX-H1 / E-IDX-SEC / E-IDX-LINK / E-IDX-ENTRY
           E-IDX-DUP / E-IDX-SRCKIND / W-IDX-ORPHAN / W-IDX-TERM / W-IDX-UPDATE
           （共 10 项，合集层索引 paper-notes/README.md；--mode index 可对缺标记文件强制生效）
  terms:   E-TERM-SEC / E-TERM-H1 / E-TERM-TABLE / E-TERM-EN / E-TERM-CITE
           E-TERM-EMPTY / E-TERM-DUP / W-TERM-MIN / W-TERM-QUOTE / W-TERM-ABBR / W-TERM-SORT
           （共 11 项，专业术语表中英对照 术语-<短名>.md）

输出: 每条问题一行 `[ERROR] <CODE> <文件名>: <消息>` / `[WARN ] <CODE> <文件名>: <消息>`（WARN 的方括号内为 4 字母 + 1 空格）；
末行汇总:
    0 ERROR 且 0 WARN → `[PASS ] <n> 项检查全部通过`（n = 实际执行的检查项数量，按上表每一项计 1）
    0 ERROR 且有 WARN → `[WARN ] 无 ERROR，但存在 <k> 条 WARN，需人工判断`
    有 ERROR        → `[ERROR] <k> 条 ERROR，必须修复`（最后一行）
退出码: 有 ERROR → 1；否则 0；文件不存在/不可读/非 md/参数错误 → 2。

实现注记（均为可预期的取舍）:
  * `<!-- ... -->` HTML 注释先整体剔除（保留行号），因此 fixture 的说明注释不会被当成正文或"表格外文字"。
  * 公式检查（E-DEEP-MATH / E-DEEP-MATH-LINE / E-DEEP-INLINE）与表格检查（E-DEEP-TABLE、table 模式全部检查）
    先剔除 ``` 围栏内部内容；
    结构性检查（H1、总结段、必备小节、围栏包裹、思维导图、综述）按原文判定，故"整篇被围栏包裹"时
    E-DEEP-WRAP 会与 E-DEEP-H1 级联报出（首个非空行确实是围栏行）。
  * "中文字符数"只统计 CJK 表意字符，不含中英文标点与数字。
  * 表格识别：只有 `line.strip()` 以 `|` 开头的行才算表格行；**连续**以 `|` 开头的行属于同一张表，
    遇到不以 `|` 开头的行即表格结束；同一个文件允许多张表且各表列数可以不同，每行只与**自己那张表的表头**比较。
    因此 `$$ \big\| \nabla L \big\|_1 $$` 这类行内公式既不算表格行、也不会触发表格检查。
  * 切分单元格时：`\\|` 是转义竖线、不算列分隔符；行内代码 span `` `...` `` 里的 `|` 也不算分隔符。
  * E-TBL-DIM 的"第 i 行"指第 i 个维度（1..9），与文件行号无关；且仅在 9 个维度齐全时判顺序。
  * E-DEEP-MATH-LINE 只要求"含 `$$` 的行 strip 后恰好等于 `$$`"，不校验三行是否成对；
    是否闭合由 E-DEEP-MATH 的奇偶判定负责，两项都执行、互不替代。
  * E-DEEP-MIX 只统计标题文本 trim 后**完全等于**思维导图四个固定分支名的标题行数（`#`~`######` 任意级别），
    `## 研究方法与实验设计` 这类含分支名但更长的标题不算；阈值取 ≥2 是为了不与
    "深读文档里恰好用到一个同名小节标题"这类合法写法冲突。
  * `来源类型：` 声明允许 Markdown 粗体包裹（`**来源类型**：PDF 全文`），正则为
    `\*{0,2}\s*来源类型\s*\*{0,2}\s*[:：]\s*(\S.*)`，即标签两侧各允许 0–2 个 `*` 与任意空白；
    取到的声明文本先剥掉 `*` 再判断是否含 `PDF 全文`；同一文件出现多处声明时逐个判定，
    命中 `PDF 全文` 的声明会让 W-DEEP-PAGE 生效。
  * W-DEEP-PAGE 的页码锚点按 `p.\\s?\\d+` 匹配（如 `[原文 p.12]`），不限定方括号形式；
    没有 `来源类型：` 声明时该检查不报（缺声明由 W-DEEP-SRC-KIND 报）。
  * deep 模式的 `executed` 计数为 15：E-DEEP-WRAP / E-DEEP-H1 / E-DEEP-SUM / E-DEEP-SEC /
    E-DEEP-MATH / E-DEEP-MATH-LINE / E-DEEP-INLINE / E-DEEP-TABLE / E-DEEP-MIX /
    W-DEEP-SRC / W-DEEP-SRC-KIND / W-DEEP-PAGE / W-DEEP-SYM / W-DEEP-TONE / W-DEEP-CITE；
    其中 W-DEEP-PAGE 记 1 项、W-DEEP-SRC-KIND 记 1 项，二者在实现上同一分支执行
    （无声明时只报前者，有声明且含 `PDF 全文` 时按锚点决定是否报后者）。
  * mmd 模式的 `executed` 计数为 9：E-MMD-H1 / E-MMD-FENCE / E-MMD-KEYWORD / E-MMD-ROOT /
    E-MMD-BRANCH / E-MMD-DEPTH / E-MMD-SYNTAX / W-MMD-BLOAT / W-MMD-TEXT。
    围栏识别只看 `line.strip()` 恰好等于 ```` ```mermaid ```` 的行；配对闭合栏取其后第一个以 ``` 开头的行，
    找不到即"未闭合"（该块内仍按已有行内容继续判定 KEYWORD/ROOT/BRANCH/DEPTH/SYNTAX）。
    E-MMD-DEPTH 的层级 = 围栏内非空节点行（`mindmap` 关键字行除外）的缩进空格数去重排序后的名次，
    根所在缩进为第 1 层，而不是绝对空格数。
    E-MMD-SYNTAX 的"节点文本"指剥掉 `((...))`/`[...]`/`(...)`/`{}`/中英文引号外壳后的内容，
    根节点允许外壳（`root((MFAA))`）但其内容同样不得含 `( ) [ ] { } , ; : %` 这些 ASCII 字符。
    W-MMD-TEXT 只把围栏行、H1 行、空行视为"合法"，其余任何非空行都报（含多余围栏行与 HTML 注释之外的说明文字）。
  * faq 模式的 `executed` 计数为 4 + 小节数 × 5：E-FAQ-H1 / E-FAQ-SEC / E-FAQ-DUP / W-FAQ-TONE 各 1 项，
    每个 `##` 小节各记 E-FAQ-FIELD / E-FAQ-CITE / W-FAQ-MISCONCEPT / W-FAQ-SELFCHECK / W-FAQ-SHORT 5 项。
    字段识别正则为 `\*\*\s*([^*：:\s]{1,10})\s*\*\*\s*[:：]`，即标签两侧各允许任意空白、冒号半角全角均可。
    E-FAQ-CITE 的"解答段落" = `**解答**：` 所在行 + 其后紧随的非空行，遇到空行或下一个字段行即结束；
    因此把解答拆成"字段行两行 + 空行 + 续写段落"时，续写段落里的来源标记不会被算作该解答的。
    W-FAQ-SHORT 的字数 = 解答段落内 `[\u4e00-\u9fff]` 中文字符数（含扩展 A 区汉字）+ 英文单词数（`[A-Za-z]+`）。
    W-FAQ-TONE 沿用 deep 模式的 TONE_WORDS，但作用范围是全文（围栏内除外）。
  * index 模式的 `executed` 计数为 10（上表逐项各 1）。实现注记：
    标记行判定在**剔除 HTML 注释之前**的原文上做（否则标记会被 strip_comments 抹掉），
    要求"首个非空行 strip 后恰等于标记"；显式 `--mode index` 时该判定失败只报 E-IDX-MARKER，不改变模式。
    E-IDX-H1 的"去掉标记行后"由 strip_comments 自然实现：标记行被置空，故首个非空行即 H1；
    标题文本须形如 `# <方向>论文笔记库`（方向非空），且全文件 H1 唯一。
    E-IDX-SEC 用小节标题**完全相等**匹配五个 `##` 小节（多出的其它 `##` 小节不报）；
    顺序判定只在五节齐全时进行，避免级联。
    E-IDX-ENTRY 的"条目"= `## 一、主题清单` 起、下一个 `##` 前的区间内以 `-`/`*`/`+` 开头的列表项
    （该区间内的普通段落不算条目）；缺链接 / 缺 ` — ` 分隔 / 缺证据括注 / 链接目标不是 `./<短名>/README.md`
    / 证据括注缺 `代码：有|无` 各报一条 E-IDX-ENTRY，互不替代。
    E-IDX-LINK 只对有链接的条目判定，目标路径按**索引文件所在目录**相对解析（支持 `../`），存在即可；
    E-IDX-DUP 以链接目标字符串为键，同一目标登记 ≥2 次报 1 条（不去重后逐条报）。
    E-IDX-SRCKIND 取证据括注里 `；`/`;` 之前的那一段作为"类型词"，须属于 {全文, 摘要, 二手, 代码, OCR}。
    W-IDX-ORPHAN 只扫索引所在目录**一层**的子目录（隐藏目录跳过），命中 `<子目录>/README.md`
    且该 README 未被任何条目链接时各报 1 条；用绝对路径比较，避免 `./` 写法差异造成误判。
    W-IDX-TERM 只看 `## 二、术语速查` 区间内的**第一张**表：表头去空白后须恰为
    `|术语|一句话解释|首次出现|`，且分隔行之外至少一行数据；无表 / 表头错 / 无数据各报 1 条。
    W-IDX-UPDATE 只要求存在一行 `>` 引用行，其中出现 `最近更新：YYYY-MM-DD`（允许行尾附加说明文字）。
  * terms 模式的 `executed` 计数为 11（上表逐项各 1）。实现注记：
    模式识别只靠文件名词干 `术语`（或 `--mode terms` 显式指定），**不**需要 index 那种 HTML 注释标记行；
    该 token 判定排在 综述 之后、内容启发式之前，与 深读/表格/思维导图/导图/难点 各 token 不重叠。
    E-TERM-H1 要求"首个非空行"就是唯一的 H1（HTML 注释已先剔除，故 fixture 的说明注释不影响判定），
    且标题文本须形如 `# <短名> 专业术语表（中英对照）`（全角括号、短名非空）。
    E-TERM-SEC 用小节标题**完全相等**匹配六个 `##` 小节（多出的其它 `##` 小节不报）；
    顺序判定只在六节齐全时进行，避免级联。
    E-TERM-TABLE 只看 `## 二、` 与 `## 三、` 区间内（`## 三、` 里允许 `### <分组名>` 分小组，每组一张表）
    **起始行落在该区间内**的每一张表：表头去空白后必须恰为
    `|英文术语|缩写|中文译名|一句话解释|在本文中的角色|出处|`（列数与列名都查），
    两区间合计至少 1 张表、至少 8 行数据（数据行 = 表头与分隔行之外的 `|` 行）。
    E-TERM-EN / E-TERM-EMPTY / E-TERM-CITE / E-TERM-DUP 逐数据行判定：
    `英文术语`（第 1 列）非空且含至少 1 个拉丁字母；`中文译名`/`一句话解释`/`在本文中的角色`
    （第 3/4/5 列，1 基）非空且不是占位符 `-`/`—`/`TBD`/`无`/`N/A`（ASCII 比较不区分大小写）；
    `出处`（第 6 列）须含合法来源标记 —— 裸标记 `[原文]/[代码]/[摘要]/[二手]/[OCR]/[推断]`
    或**带页码**的 `[原文 p.7]`（`p.` 后允许一个空白，允许 `p.7-8` 这样的范围）；
    重复判定以"英文术语"列归一化（压空白 + 大小写折叠）后的字符串为键，同一键 ≥2 次各报 1 条。
    这里的页码分支从一开始就写在 TERMS_CITE_RE 里，避免重演 FAQ_CITE_RE 与
    `references/faq-template.md` 口径不一致（模板允许 `[原文 p.N]`、正则只认裸标记）的老问题。
    W-TERM-MIN 是"全量收录"的**下限代理指标**而非完整性证明，消息里写明这一点；阈值 15。
    W-TERM-QUOTE 统计 `## 五、英文原句摘录` 区间内的列表项：合格条目 = 去掉合法来源标记后
    仍有 ≥2 个长度 ≥2 的英文单词（"一段英文"）**且**含合法来源标记；合格条目 < 5 报 1 条。
    W-TERM-ABBR / W-TERM-SORT 只看 `## 六、缩略语索引`：缩写候选取该区间内每张表的
    **首个数据列**与每个列表项的行首 token（`**BOLD**`、`ABBR：…`、`ABBR 中文` 都认），
    候选须是"全大写字母数字 token"（长度 ≥2，可含 `-`/`+`/`.`）才当作缩写；
    候选未在二、三两节 `缩写` 列（去空白去反引号去粗体星号后同样判定）出现过即悬空；
    字母序用去空白 + 大小写折叠后的字符串比较，只报第一处逆序。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:  # Windows GBK 控制台防御：保证中文输出不抛 UnicodeEncodeError
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MODES = ("auto", "deep", "table", "mindmap", "mmd", "faq", "review", "index", "terms")

COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
FENCE_LINE_RE = re.compile(r"^\s*```")
H1_RE = re.compile(r"^#\s+\S")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
LIST_RE = re.compile(r"^([ \t]*)-(\s|$)")
CITE_RE = re.compile(r"\[(\d+)\]")
SOURCE_MARK_RE = re.compile(r"\[([^\]\n]{1,8})\](?!\s*\()")
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
INLINE_CODE_RE = re.compile(r"`[^`]*`")
DOLLAR_PAIR_RE = re.compile(r"\$\$.*?\$\$")
PARA_LIST_RE = re.compile(r"^([-*+]|\d+[.)])(\s|$)")
SRC_KIND_RE = re.compile(r"\*{0,2}\s*来源类型\s*\*{0,2}\s*[:：]\s*(\S.*)")
PAGE_ANCHOR_RE = re.compile(r"p\.\s?\d+")

DEEP_SECTIONS = ("背景", "方法", "实验", "贡献", "局限")
TONE_WORDS = ("好的", "当然", "以下是", "希望", "如需", "总结一下", "我们来", "首先我们", "如有需要")
SOURCE_LABELS = frozenset({"原文", "代码", "摘要", "图表", "公式", "实验", "二手", "注释", "注", "推断", "未核实"})
TABLE_DIMS = (
    "论文标题", "作者", "发表年份", "研究问题", "研究方法",
    "主要发现", "创新点", "局限性", "与本研究的关联",
)
SENT_END_RE = re.compile(r"[。！？；]")
MM_BRANCHES = ("研究背景与目标", "研究方法", "关键研究结果", "研究结论与意义")
FAQ_FIELD_RE = re.compile(r"\*\*\s*([^*：:\s]{1,10})\s*\*\*\s*[:：]")
EN_WORD_RE = re.compile(r"[A-Za-z]+")
_FAQ_CITE_LABELS = ("原文", "代码", "摘要", "二手", "OCR", "推断")
FAQ_CITE_RE = re.compile(
    r"\[(?:" + "|".join(_FAQ_CITE_LABELS) + r"|\d+)\]"
)
RV_SECTIONS = ("研究主题概述", "各论文主要贡献", "研究方法对比", "主要发现汇总", "研究趋势与展望")

# index 模式（合集层索引 paper-notes/README.md）
INDEX_MARKER = "<!-- paper-reading: collection-index -->"
IDX_H1_RE = re.compile(r"^#\s+\S.*论文笔记库\s*$")
IDX_SECTIONS = ("一、主题清单", "二、术语速查", "三、跨论文对比", "四、未解决问题", "五、证据强度总览")
IDX_SRC_KINDS = ("全文", "摘要", "二手", "代码", "OCR")
IDX_TERM_HEADER = "|术语|一句话解释|首次出现|"
IDX_UPDATE_RE = re.compile(r"^\s*>.*最近更新\s*[:：]\s*\d{4}-\d{2}-\d{2}")
IDX_ENTRY_LINK_RE = re.compile(r"^\[([^\]\n]+)\]\(([^)\s]+)\)")
IDX_ENTRY_TARGET_RE = re.compile(r"^\./([^/\s]+)/README\.md$")
IDX_ENTRY_DASH_RE = re.compile(r"^\s+—\s+(\S.*?)\s*$")
IDX_ENTRY_EVIDENCE_RE = re.compile(r"（证据：([^）]*)）\s*$")
IDX_ENTRY_CODE_RE = re.compile(r"代码\s*[:：]\s*(?:有|无)")
IDX_SEPARATOR_CELL_RE = re.compile(r"^:?-{2,}:?$")

# terms 模式（专业术语表 术语-<短名>.md）
TERMS_SECTIONS = (
    "一、怎么用这份表",
    "二、核心术语（本文自造与方法名）",
    "三、分领域术语",
    "四、易混对照",
    "五、英文原句摘录",
    "六、缩略语索引",
)
# 术语表的六列表头（与 references/terms-template.md 的骨架逐字一致）
TERMS_HEADER_CELLS = ("英文术语", "缩写", "中文译名", "一句话解释", "在本文中的角色", "出处")
TERMS_TABLE_HEADER = "|" + "|".join(TERMS_HEADER_CELLS) + "|"
# 二、三两节（术语注册区）；三节里允许 `### <分组名>` 分小组，每组一张同形状的表
TERMS_TERM_SECTIONS = ("二、核心术语（本文自造与方法名）", "三、分领域术语")
TERMS_QUOTE_SECTION = "五、英文原句摘录"
TERMS_ABBR_SECTION = "六、缩略语索引"
TERMS_H1_RE = re.compile(r"^#\s+\S.*?\s+专业术语表（中英对照）\s*$")
# 出处列：裸标记，或带页码的 [原文 p.7] / [原文 p.7-8]（页码分支必须从一开始就合法）
_TERMS_CITE_LABELS = ("原文", "代码", "摘要", "二手", "OCR", "推断")
TERMS_CITE_RE = re.compile(
    r"\[(?:" + "|".join(_TERMS_CITE_LABELS) + r")(?:\s*p\.\s?\d+(?:-\d+)?)?\]",
    re.IGNORECASE,
)
TERMS_PLACEHOLDERS = frozenset({"-", "—", "tbd", "无", "n/a"})
TERMS_TABLE_MIN_ROWS = 8
TERMS_MIN_ROWS = 15
TERMS_MIN_QUOTES = 5
TERMS_ABBR_RE = re.compile(r"^[A-Z0-9][A-Z0-9+\-.]{1,15}$")
TERMS_ITEM_RE = re.compile(r"^([-*+]|\d+[.)])(\s+|$)")
TERMS_EN_WORD_RE = re.compile(r"[A-Za-z]{2,}")


# ---------------------------------------------------------------- 通用工具

def strip_comments(text: str) -> str:
    """剔除 HTML 注释，但保留换行数，使行号仍可对齐。"""
    return COMMENT_RE.sub(lambda m: "\n" * m.group(0).count("\n"), text)


def mask_fences(text: str) -> str:
    """把 ``` 围栏（含围栏行本身）整段置空，保留行数，便于按行号报错。"""
    out: list[str] = []
    in_fence = False
    for line in text.split("\n"):
        if FENCE_LINE_RE.match(line):
            in_fence = not in_fence
            out.append("")
            continue
        out.append("" if in_fence else line)
    return "\n".join(out)


def first_nonempty(lines: list[str]) -> int | None:
    for i, ln in enumerate(lines):
        if ln.strip():
            return i
    return None


def heading_map(lines: list[str]) -> list[tuple[int, int, str]]:
    """[(行号0基, 级别, 标题文本)]"""
    res = []
    for i, ln in enumerate(lines):
        m = HEADING_RE.match(ln)
        if m:
            res.append((i, len(m.group(1)), m.group(2)))
    return res


PIPE_HIDE = "\x00"  # 转义竖线/行内代码竖线的占位符


def _mask_pipes(line: str) -> str:
    """把 `\\|`（转义竖线）与行内代码 span 内的 `|` 换成占位符，使其不被当作列分隔符。"""
    out: list[str] = []
    i = 0
    in_code = False
    while i < len(line):
        ch = line[i]
        if ch == "\\" and i + 1 < len(line):
            nxt = line[i + 1]
            if nxt == "|":
                out.append(PIPE_HIDE)
            else:
                out.append(ch)
                out.append(nxt)
            i += 2
            continue
        if ch == "`":
            in_code = not in_code
            out.append(ch)
            i += 1
            continue
        if ch == "|" and in_code:
            out.append(PIPE_HIDE)
            i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def split_cells(line: str) -> list[str]:
    """按 `|` 切出单元格，忽略首尾空壳；`\\|` 与行内代码里的竖线不参与切分。"""
    parts = _mask_pipes(line.strip()).split("|")
    if parts and not parts[0].strip():
        parts = parts[1:]
    if parts and not parts[-1].strip():
        parts = parts[:-1]
    return [p.replace(PIPE_HIDE, "|") for p in parts]


def table_runs(lines: list[str]) -> list[tuple[int, int]]:
    """找表格：连续以 `|` 开头的行属于同一张表（不以 `|` 开头即结束）。

    返回 [(表头行0基, 结束行0基 exclusive)]，多张表互不影响，各表列数可以不同。
    """
    runs = []
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith("|"):
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith("|"):
                j += 1
            runs.append((i, j))
            i = j
        else:
            i += 1
    return runs


def block_kind(line: str) -> str:
    s = line.strip()
    if not s:
        return "empty"
    if s.startswith("#"):
        return "heading"
    if s.startswith("```"):
        return "fence"
    if s.startswith("|"):
        return "table"
    if s.startswith(">"):
        return "quote"
    if PARA_LIST_RE.match(s):
        return "list"
    return "para"


def cjk_count(text: str) -> int:
    return len(CJK_RE.findall(text))


def has_source_mark(text: str) -> bool:
    for m in SOURCE_MARK_RE.finditer(text):
        label = m.group(1).strip()
        if label in SOURCE_LABELS or CJK_RE.search(label):
            return True
    return False


# ---------------------------------------------------------------- deep 模式

def check_deep(raw_lines: list[str], masked_lines: list[str]) -> tuple[list[tuple[str, str]], int]:
    problems: list[tuple[str, str]] = []
    executed = 0
    masked_text = "\n".join(masked_lines)
    headings = heading_map(raw_lines)
    hnames = [t for _, lvl, t in headings if lvl >= 2]
    h1_idx = [i for i, ln in enumerate(raw_lines) if H1_RE.match(ln)]
    fi = first_nonempty(raw_lines)

    # E-DEEP-WRAP
    executed += 1
    if fi is not None and raw_lines[fi].lstrip().startswith("```"):
        problems.append(("E-DEEP-WRAP", "整篇被代码围栏包裹，应直接输出 Markdown"))

    # E-DEEP-H1
    executed += 1
    if fi is None or not H1_RE.match(raw_lines[fi]) or len(h1_idx) != 1:
        problems.append(("E-DEEP-H1", "首个非空行必须是唯一的 H1 论文标题"))

    # E-DEEP-SUM
    executed += 1
    start = (h1_idx[0] + 1) if h1_idx else (fi if fi is not None else 0)
    j = start
    while j < len(raw_lines) and not raw_lines[j].strip():
        j += 1
    kind = block_kind(raw_lines[j]) if j < len(raw_lines) else "empty"
    opening = (j, j)
    para_parts: list[str] = []
    if kind == "para":
        k = j
        while k < len(raw_lines) and block_kind(raw_lines[k]) == "para":
            para_parts.append(raw_lines[k])
            k += 1
        opening = (j, k)
    m = cjk_count("".join(para_parts))
    if kind != "para" or m < 120:
        problems.append(
            ("E-DEEP-SUM", f"H1 之后必须紧跟一段核心内容总结（≥120 字纯段落），实际 {m} 字")
        )

    # E-DEEP-SEC
    executed += 1
    for kw in DEEP_SECTIONS:
        if not any(kw in t for t in hnames):
            problems.append(("E-DEEP-SEC", f"缺少必备小节：{kw}"))

    # E-DEEP-MATH
    executed += 1
    dollars = masked_text.count("$$")
    if dollars % 2:
        problems.append(("E-DEEP-MATH", f"行间公式 $$ 数量为 {dollars}（奇数，未闭合）"))

    # E-DEEP-MATH-LINE
    executed += 1
    for i, ln in enumerate(masked_lines, 1):
        if "$$" in ln and ln.strip() != "$$":
            problems.append(
                ("E-DEEP-MATH-LINE",
                 f"第 {i} 行行间公式未独占行（应写成 $$ 单独一行 + 公式单独一行 + $$ 单独一行）")
            )

    # E-DEEP-INLINE
    executed += 1
    for i, ln in enumerate(masked_lines, 1):
        s = DOLLAR_PAIR_RE.sub("", ln)
        s = INLINE_CODE_RE.sub("", s)
        c = s.count("$")
        if c % 2:
            problems.append(("E-DEEP-INLINE", f"第 {i} 行行内 $ 数量为 {c}（奇数，未闭合）"))

    # E-DEEP-TABLE（每张表各自与自己的表头比较列数）
    executed += 1
    for a, b in table_runs(masked_lines):
        header_cells = len(split_cells(masked_lines[a]))
        for k in range(a, b):
            n = len(split_cells(masked_lines[k]))
            if n != header_cells:
                problems.append(
                    ("E-DEEP-TABLE", f"第 {k + 1} 行表格列数 {n} 与表头 {header_cells} 不一致")
                )

    # E-DEEP-MIX（标题文本完全等于思维导图固定分支名才算，避免误伤同名小节）
    executed += 1
    mix = sum(1 for _, _, t in headings if t in MM_BRANCHES)
    if mix >= 2:
        problems.append(
            ("E-DEEP-MIX", f"深读文档内混装了思维导图分支（{mix} 个），思维导图必须独立成文件")
        )

    # W-DEEP-SRC
    executed += 1
    if not any(("证据" in t or "出处" in t) for t in hnames):
        problems.append(
            ("W-DEEP-SRC", "缺少「证据与出处」小节，无法区分原文可查/二手推断/未核实")
        )

    # W-DEEP-SRC-KIND / W-DEEP-PAGE（来源类型声明及其页码锚点义务，按原文判定）
    raw_text = "\n".join(raw_lines)
    executed += 1
    declared_kinds = [m.group(1).replace("*", "") for m in SRC_KIND_RE.finditer(raw_text)]
    executed += 1
    if not declared_kinds:
        problems.append(
            ("W-DEEP-SRC-KIND",
             "缺少「来源类型：」声明（PDF 全文 / 官方摘要 / 二手转述 / 代码）")
        )
    elif any(("PDF 全文" in k or "PDF全文" in k) for k in declared_kinds):
        if not PAGE_ANCHOR_RE.search(raw_text):
            problems.append(
                ("W-DEEP-PAGE",
                 "声明来源为 PDF 全文，但全文没有页码锚点（如 [原文 p.12]）")
            )

    # W-DEEP-SYM
    executed += 1
    blocks = dollars // 2
    if blocks >= 3 and not any(("符号" in t or "记号" in t) for t in hnames):
        problems.append(("W-DEEP-SYM", f"公式块 {blocks} 个但缺少符号与记号表"))

    # W-DEEP-TONE（开头段 + 最后一节）
    executed += 1
    regions = [opening]
    last_h2 = [i for i, lvl, _ in headings if lvl == 2]
    if last_h2:
        regions.append((last_h2[-1], len(raw_lines)))
    seen: set[int] = set()
    for a, b in regions:
        for i in range(a, min(b, len(raw_lines))):
            if i in seen:
                continue
            seen.add(i)
            for w in TONE_WORDS:
                if w in raw_lines[i]:
                    problems.append(("W-DEEP-TONE", f"第 {i + 1} 行出现助手口吻/寒暄词：「{w}」"))
                    break

    # W-DEEP-CITE（来源标注属内容检查，按原文判定）
    executed += 1
    if not (CITE_RE.search(raw_text) or has_source_mark(raw_text)):
        problems.append(("W-DEEP-CITE", "未发现引用标注或来源标记，无法回溯证据"))

    return problems, executed


# ---------------------------------------------------------------- table 模式

def check_table(lines: list[str]) -> tuple[list[tuple[str, str]], int]:
    problems: list[tuple[str, str]] = []
    executed = 0
    idxs = [i for i, ln in enumerate(lines) if ln.strip()]
    block: list[int] = []
    if idxs:
        for i in range(idxs[0], len(lines)):
            if lines[i].strip():
                block.append(i)
            else:
                break
    block_set = set(block)

    # E-TBL-ONLY（表格外文字 / 超过 11 行的多余行）
    executed += 1
    outside = sorted({i for i in idxs if i not in block_set} | set(block[11:]))
    for i in outside:
        problems.append(
            ("E-TBL-ONLY", f'第 {i + 1} 行存在表格外文字，违反"只输出填好的表格，不要添加额外说明"')
        )

    # E-TBL-HEAD
    executed += 1
    head = lines[block[0]].strip() if block else ""
    if re.sub(r"\s+", "", head) != "|维度|内容|":
        problems.append(("E-TBL-HEAD", f"表头必须是 | 维度 | 内容 |，实际：{head}"))

    rows = block[2:11]
    actual = [split_cells(lines[i])[0].strip() if split_cells(lines[i]) else "" for i in rows]

    # E-TBL-DIM
    executed += 1
    missing = [d for d in TABLE_DIMS if d not in actual]
    for d in missing:
        problems.append(("E-TBL-DIM", f"缺少维度：{d}"))
    if not missing and tuple(actual[: len(TABLE_DIMS)]) != TABLE_DIMS:
        for pos, (exp, act) in enumerate(zip(TABLE_DIMS, actual), 1):
            if exp != act:
                problems.append(
                    ("E-TBL-DIM", f"维度顺序与模板不一致，第 {pos} 行应为「{exp}」，实际「{act}」")
                )

    def row_name(pos: int, i: int) -> str:
        cells = split_cells(lines[i])
        name = cells[0].strip() if cells else ""
        return name or (TABLE_DIMS[pos] if pos < len(TABLE_DIMS) else f"第{pos + 1}行")

    # E-TBL-EMPTY
    executed += 1
    for pos, i in enumerate(rows):
        cells = split_cells(lines[i])
        content = cells[1].strip() if len(cells) > 1 else ""
        if not content:
            problems.append(
                ("E-TBL-EMPTY", f'维度「{row_name(pos, i)}」内容为空（应填内容或"未提及"）')
            )

    # E-TBL-LEN
    executed += 1
    for pos, i in enumerate(rows):
        cells = split_cells(lines[i])
        content = cells[1].strip() if len(cells) > 1 else ""
        k = len(SENT_END_RE.findall(content))
        if k > 3:
            problems.append(
                ("E-TBL-LEN", f"维度「{row_name(pos, i)}」内容 {k} 句，超过 3 句上限")
            )

    # E-TBL-FMT
    executed += 1
    for i in rows:
        s = lines[i].strip()
        if not (s.startswith("|") and s.endswith("|")):
            problems.append(("E-TBL-FMT", f"第 {i + 1} 行表格未闭合（应以 | 结尾）"))

    return problems, executed


# ---------------------------------------------------------------- mindmap 模式

def check_mindmap(lines: list[str]) -> tuple[list[tuple[str, str]], int]:
    problems: list[tuple[str, str]] = []
    executed = 0
    headings = heading_map(lines)
    fi = first_nonempty(lines)

    # E-MM-ROOT
    executed += 1
    h1_idx = [i for i, ln in enumerate(lines) if H1_RE.match(ln)]
    if fi is None or not H1_RE.match(lines[fi]) or len(h1_idx) != 1:
        problems.append(("E-MM-ROOT", "首个非空行必须是唯一的 H1 论文标题"))

    # E-MM-BRANCH
    executed += 1
    h2 = [(i, t) for i, lvl, t in headings if lvl == 2]
    branches = [t for _, t in h2]
    if branches != list(MM_BRANCHES):
        problems.append(
            ("E-MM-BRANCH", f"一级分支必须恰好为四个固定分支，实际：{' | '.join(branches)}")
        )

    # E-MM-FENCE
    executed += 1
    if any(FENCE_LINE_RE.match(ln) for ln in lines):
        problems.append(("E-MM-FENCE", "思维导图不得包含代码围栏"))

    nodes: list[tuple[int, int]] = []
    for i, ln in enumerate(lines):
        m = LIST_RE.match(ln)
        if m:
            indent = m.group(1).replace("\t", "  ")
            nodes.append((i, len(indent) // 2 + 1))

    # E-MM-DEPTH
    executed += 1
    for i, d in nodes:
        if d > 4:
            problems.append(("E-MM-DEPTH", f"第 {i + 1} 行节点层级 {d} 超过 4 层"))

    # E-MM-EMPTY
    executed += 1
    for k, (i, t) in enumerate(h2):
        end = h2[k + 1][0] if k + 1 < len(h2) else len(lines)
        cnt = sum(1 for lineno, _ in nodes if i < lineno < end)
        if cnt < 2:
            problems.append(("E-MM-EMPTY", f"分支「{t}」子节点不足 2 个"))

    # W-MM-BLOAT
    executed += 1
    if len(nodes) > 80:
        problems.append(
            ("W-MM-BLOAT", f"节点总数 {len(nodes)} 超过 80，建议精简（思维导图不是全文搬家）")
        )

    return problems, executed


# ---------------------------------------------------------------- mmd 模式

def fence_blocks(lines: list[str], lang: str) -> list[tuple[int, int | None]]:
    """找 ```<lang> 开栏及其配对闭合栏，返回 [(开栏行0基, 闭合行0基 或 None)]。

    只有 `line.strip()` 恰好等于 ```` ```<lang> ```` 才算开栏；未配对的闭栏在遇到下一个
    同类开栏或文件结束时也算闭合（Markdown 围栏本来就以"下一个围栏行"收尾）。
    """
    opens = [i for i, ln in enumerate(lines) if ln.strip() == "```" + lang]
    blocks: list[tuple[int, int | None]] = []
    for pos, a in enumerate(opens):
        end = opens[pos + 1] if pos + 1 < len(opens) else len(lines)
        close = None
        for j in range(a + 1, end):
            if ln_starts_fence(lines[j]):
                close = j
                break
        blocks.append((a, close))
    return blocks


def ln_starts_fence(line: str) -> bool:
    return bool(FENCE_LINE_RE.match(line))


MMD_DANGER_RE = re.compile(r"[()\[\]{},;:%]")
MMD_WRAP_PAIRS = (("((", "))"), ("[[", "]]"), ("{{", "}}"), ("(", ")"), ("[", "]"),
                  ("{", "}"), ("“", "”"), ("‘", "’"), ('"', '"'), ("'", "'"))


def strip_root_keyword(text: str) -> str:
    """`root((短名))` / `root[短名]` 的外壳由 root 关键字 + 括号共同构成，先摘掉关键字。

    仅当关键字后面紧跟括号/引号时才摘，避免误伤 `root cause` 这类普通节点名。
    """
    s = text.strip()
    for kw in ("root", "Root", "ROOT"):
        if s.startswith(kw) and s[len(kw):len(kw) + 1] in ("(", "[", "{", "“", '"', "'"):
            return s[len(kw):].strip()
    return s


def unwrap_node(text: str) -> str:
    """剥掉节点文本外壳（`((...))` / `[[...]]` / `[...]` / `(...)` / 引号），返回内容 trim 后的文本。"""
    s = strip_root_keyword(text)
    changed = True
    while changed and len(s) >= 2:
        changed = False
        for left, right in MMD_WRAP_PAIRS:
            if s.startswith(left) and s.endswith(right) and len(s) > len(left) + len(right) - 1:
                s = s[len(left):len(s) - len(right)].strip()
                changed = True
                break
    return s.strip()


def mermaid_lines(lines: list[str], a: int, b: int) -> list[tuple[int, str]]:
    """围栏内的非空行 [(行号0基, 行内容)]。"""
    return [(i, lines[i]) for i in range(a + 1, b) if lines[i].strip()]


def indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" \t"))


def check_mmd(lines: list[str]) -> tuple[list[tuple[str, str]], int]:
    problems: list[tuple[str, str]] = []
    executed = 0
    fi = first_nonempty(lines)
    h1_idx = [i for i, ln in enumerate(lines) if H1_RE.match(ln)]
    blocks = fence_blocks(lines, "mermaid")
    mermaid_opens = [i for i, ln in enumerate(lines) if ln.strip() == "```mermaid"]
    main = blocks[0] if len(blocks) == 1 else None
    inner: list[tuple[int, str]] = []
    if main is not None and main[1] is not None:
        inner = mermaid_lines(lines, main[0], main[1])
    fence_span = set()
    if main is not None:
        end = main[1] if main[1] is not None else len(lines)
        fence_span = set(range(main[0], end + 1))

    # E-MMD-H1
    executed += 1
    if fi is None or not H1_RE.match(lines[fi]) or len(h1_idx) != 1:
        problems.append(("E-MMD-H1", "首个非空行必须是唯一的 H1 论文标题"))

    # E-MMD-FENCE（恰好一个 ```mermaid 开栏，且必须成对闭合）
    executed += 1
    block_ok = False
    if len(blocks) == 0:
        problems.append(("E-MMD-FENCE", "缺少 ```mermaid 开栏（必须恰好一个 mermaid 围栏块）"))
    elif len(blocks) > len(mermaid_opens):
        a, _ = blocks[len(mermaid_opens)]
        problems.append(
            ("E-MMD-FENCE", f"```mermaid 开栏 {len(blocks)} 个，必须恰好一个（第 {a + 1} 行为多余开栏）")
        )
    else:
        a, b = blocks[0]
        if b is None:
            problems.append(("E-MMD-FENCE", f"第 {a + 1} 行的 ```mermaid 围栏未闭合（缺少 ``` 闭合栏）"))
        else:
            extra = sorted(j for j in range(b + 1, len(lines)) if ln_starts_fence(lines[j]))
            if extra:
                problems.append(
                    ("E-MMD-FENCE", f"第 {extra[0] + 1} 行出现多余围栏行，必须以一个 mermaid 块收尾")
                )
            else:
                block_ok = True

    # E-MMD-KEYWORD（仅在 mermaid 块本身合法时判定，避免与 E-MMD-FENCE 级联）
    executed += 1
    if block_ok:
        if not inner:
            problems.append(("E-MMD-KEYWORD", "围栏内为空，第一个非空行必须是 mindmap"))
        elif inner[0][1].strip() != "mindmap":
            problems.append(
                ("E-MMD-KEYWORD", f"围栏内第一个非空行必须是 mindmap，实际：{inner[0][1].strip()}")
            )

    # 关键字不对时后续层级判定没有意义（关键字符号也未必是节点），只由 E-MMD-KEYWORD 报
    parsed = block_ok and bool(inner) and inner[0][1].strip() == "mindmap"
    nodes = inner[1:] if parsed else []
    indents = sorted({indent_of(t) for _, t in nodes})
    levels = {ind: k + 1 for k, ind in enumerate(indents)}

    # E-MMD-ROOT
    executed += 1
    roots: list[tuple[int, str]] = []
    if nodes:
        roots = [(i, t) for i, t in nodes if indent_of(t) == indents[0]]
    if parsed:
        if not nodes:
            problems.append(("E-MMD-ROOT", "围栏内没有节点行，无法确定唯一根节点"))
        elif len(roots) != 1:
            problems.append(
                ("E-MMD-ROOT", f"缩进最小的节点行有 {len(roots)} 条，根节点必须唯一")
            )

    # E-MMD-BRANCH
    executed += 1
    if len(roots) == 1 and len(indents) >= 2:
        first_level = [(i, t) for i, t in nodes if indent_of(t) == indents[1]]
        names = [unwrap_node(t) for _, t in first_level]
        if names != list(MM_BRANCHES):
            problems.append(
                ("E-MMD-BRANCH",
                 f"根的一级子节点必须恰好为四个固定分支（顺序一致），实际：{' | '.join(names) or '（无）'}")
            )
    elif len(roots) == 1:
        problems.append(("E-MMD-BRANCH", "根节点下没有一级子节点，必须恰好为四个固定分支"))

    # E-MMD-DEPTH
    executed += 1
    for i, t in nodes:
        d = levels[indent_of(t)]
        if d > 4:
            problems.append(("E-MMD-DEPTH", f"第 {i + 1} 行节点层级 {d} 超过 4 层"))

    # E-MMD-SYNTAX（根节点允许 root((短名)) 外壳，但内容同样不得含危险字符）
    executed += 1
    for i, t in nodes:
        content = unwrap_node(t)
        m = MMD_DANGER_RE.search(content)
        if m:
            kind = "根节点" if (len(roots) == 1 and i == roots[0][0]) else "节点"
            problems.append(
                ("E-MMD-SYNTAX",
                 f"第 {i + 1} 行{kind}文本含 Mermaid 危险字符「{m.group(0)}」（改用中文标点或去掉标点，否则解析失败）")
            )

    # W-MMD-BLOAT
    executed += 1
    if len(inner) > 80:
        problems.append(
            ("W-MMD-BLOAT", f"节点总数 {len(inner)} 超过 80，建议精简（可渲染导图不是全文搬家）")
        )

    # W-MMD-TEXT（导图文件应只有标题 + 一个 mermaid 块）
    executed += 1
    for i, ln in enumerate(lines):
        if not ln.strip() or i in fence_span or i in h1_idx:
            continue
        problems.append(
            ("W-MMD-TEXT", f"第 {i + 1} 行存在 mermaid 围栏与 H1 之外的内容，导图文件应只有标题 + 一个 mermaid 块")
        )

    return problems, executed


# ---------------------------------------------------------------- faq 模式

def field_labels(line: str) -> list[str]:
    """返回该行出现的 **字段**：标签（如 难点 / 解答 / 常见误解 / 自检）。"""
    return [m.group(1) for m in FAQ_FIELD_RE.finditer(line)]


def faq_body_len(text: str) -> int:
    """中文字符数 + 英文单词数。"""
    return len(CJK_RE.findall(text)) + len(EN_WORD_RE.findall(text))


def check_faq(lines: list[str]) -> tuple[list[tuple[str, str]], int]:
    problems: list[tuple[str, str]] = []
    executed = 0
    masked = mask_fences("\n".join(lines)).split("\n")
    headings = heading_map(masked)
    h1_idx = [i for i, ln in enumerate(lines) if H1_RE.match(ln)]
    fi = first_nonempty(lines)

    # E-FAQ-H1
    executed += 1
    if fi is None or not H1_RE.match(lines[fi]) or len(h1_idx) != 1:
        problems.append(("E-FAQ-H1", "首个非空行必须是唯一的 H1 论文标题"))

    sections = [(i, t) for i, lvl, t in headings if lvl == 2]

    # E-FAQ-SEC
    executed += 1
    if len(sections) < 3:
        problems.append(
            ("E-FAQ-SEC", f"## 小节数 {len(sections)} 不足 3，一份难点文档至少 3 条难点")
        )

    # E-FAQ-DUP
    executed += 1
    seen: set[str] = set()
    for _, t in sections:
        key = re.sub(r"\s+", "", t)
        if key in seen:
            problems.append(("E-FAQ-DUP", f"## 小节标题重复：{t}"))
        seen.add(key)

    for k, (start, title) in enumerate(sections):
        end = sections[k + 1][0] if k + 1 < len(sections) else len(lines)
        body = list(range(start + 1, end))
        labels: set[str] = set()
        for i in body:
            labels.update(field_labels(lines[i]))

        # E-FAQ-FIELD
        executed += 1
        for need in ("难点", "解答"):
            if need not in labels:
                problems.append(("E-FAQ-FIELD", f"小节「{title}」缺少 **{need}**：字段"))

        # 解答段落 = 含 **解答**：字段的行 + 其后紧随的非空行，直到下一个字段行或空行
        para_idx: list[int] = []
        for i in body:
            if "解答" not in field_labels(lines[i]):
                continue
            para_idx.append(i)
            for j in range(i + 1, end):
                if not lines[j].strip() or field_labels(lines[j]):
                    break
                para_idx.append(j)

        # E-FAQ-CITE
        executed += 1
        para = "\n".join(lines[i] for i in para_idx)
        if not FAQ_CITE_RE.search(para):
            problems.append(
                ("E-FAQ-CITE",
                 f"小节「{title}」的 **解答** 段落没有任何来源标记（[原文]/[代码]/[摘要]/[二手]/[OCR]/[推断]/[数字]）")
            )

        # W-FAQ-MISCONCEPT / W-FAQ-SELFCHECK
        executed += 1
        if "常见误解" not in labels:
            problems.append(("W-FAQ-MISCONCEPT", f"小节「{title}」缺少 **常见误解**：字段（❌ 错法 → ✅ 正解）"))

        executed += 1
        if "自检" not in labels:
            problems.append(("W-FAQ-SELFCHECK", f"小节「{title}」缺少 **自检**：字段"))

        # W-FAQ-SHORT（解答正文字数 = 中文字符数 + 英文单词数）
        executed += 1
        n = faq_body_len("\n".join(lines[i] for i in para_idx))
        if n < 80:
            problems.append(
                ("W-FAQ-SHORT", f"小节「{title}」的 **解答** 正文 {n} 字，少于 80 字（中文字符 + 英文单词）")
            )

    # W-FAQ-TONE
    executed += 1
    for i, ln in enumerate(masked, 1):
        for w in TONE_WORDS:
            if w in ln:
                problems.append(("W-FAQ-TONE", f"第 {i} 行出现助手口吻/寒暄词：「{w}」"))
                break

    return problems, executed


# ---------------------------------------------------------------- review 模式

def check_review(lines: list[str], refs: int | None) -> tuple[list[tuple[str, str]], int]:
    problems: list[tuple[str, str]] = []
    executed = 0
    text = "\n".join(lines)
    headings = heading_map(lines)

    found: dict[str, tuple[int, int, str]] = {}
    for i, lvl, t in headings:
        if lvl in (2, 3):
            for kw in RV_SECTIONS:
                if kw in t and kw not in found:
                    found[kw] = (i, lvl, t)

    # E-RV-SEC
    executed += 1
    for kw in RV_SECTIONS:
        if kw not in found:
            problems.append(("E-RV-SEC", f"缺少综述必备小节：{kw}"))

    nums = sorted({int(m.group(1)) for m in CITE_RE.finditer(text)})
    N = refs if refs is not None else (max(nums) if nums else 0)

    # E-RV-CITE
    executed += 1
    for k in nums:
        if k < 1 or k > N:
            problems.append(("E-RV-CITE", f"引用编号 [{k}] 超出文献范围 1..{N}"))

    # E-RV-NOREF
    executed += 1
    for _, _, t in headings:
        if "参考文献" in t:
            problems.append(("E-RV-NOREF", "不得出现「参考文献」小节（按需求不输出文献列表）"))
            break

    # W-RV-DENSITY
    executed += 1
    for kw in RV_SECTIONS:
        if kw not in found:
            continue
        i, lvl, t = found[kw]
        end = len(lines)
        for j, lvl2, _ in headings:
            if j > i and lvl2 <= lvl:
                end = j
                break
        body = "\n".join(lines[i + 1:end])
        if not CITE_RE.search(body):
            problems.append(("W-RV-DENSITY", f"小节「{t}」内没有任何 [num] 引用"))

    # W-RV-GAP
    executed += 1
    for k in nums:
        if k >= 2 and (k - 1) not in nums:
            problems.append(("W-RV-GAP", f"引用编号不连续：出现 [{k}] 但缺少 [{k - 1}]"))

    return problems, executed


# ---------------------------------------------------------------- index 模式

def section_span(lines: list[str], headings: list[tuple[int, int, str]],
                 title: str) -> tuple[int, int] | None:
    """标题文本完全等于 title 的二级小节区间 [start, end)（0 基，end exclusive）；没有则 None。"""
    start = None
    for i, lvl, t in headings:
        if lvl == 2 and t == title:
            start = i
            break
    if start is None:
        return None
    end = len(lines)
    for i, lvl, _ in headings:
        if lvl <= 2 and i > start:
            end = i
            break
    return (start, end)


def check_index(lines: list[str], marker_ok: bool, path: Path) -> tuple[list[tuple[str, str]], int]:
    """校验合集层索引 paper-notes/README.md（lines 为已剔除 HTML 注释的原文行）。"""
    problems: list[tuple[str, str]] = []
    executed = 0
    index_dir = path.parent
    headings = heading_map(lines)
    h1_idx = [i for i, ln in enumerate(lines) if H1_RE.match(ln)]
    fi = first_nonempty(lines)

    # E-IDX-MARKER（标记行判定在剔除注释之前的原文上做，见 main）
    executed += 1
    if not marker_ok:
        problems.append(
            ("E-IDX-MARKER",
             f"首行非空内容必须是 {INDEX_MARKER}（合集索引的唯一识别标记）")
        )

    # E-IDX-H1（标记行已被剔除为空行，故首个非空行即"标记行之后的 H1"）
    executed += 1
    head_text = lines[fi].strip() if fi is not None else ""
    if (fi is None or not H1_RE.match(lines[fi]) or len(h1_idx) != 1
            or h1_idx[0] != fi or not IDX_H1_RE.match(head_text)):
        problems.append(
            ("E-IDX-H1",
             f"标记行之后的首个非空行必须是唯一的 H1「# <方向>论文笔记库」，实际：{head_text or '（无）'}")
        )

    # E-IDX-SEC
    executed += 1
    spans: dict[str, tuple[int, int]] = {}
    for kw in IDX_SECTIONS:
        sp = section_span(lines, headings, kw)
        if sp is not None:
            spans[kw] = sp
    for kw in IDX_SECTIONS:
        if kw not in spans:
            problems.append(("E-IDX-SEC", f"缺少必备小节：## {kw}"))
    if len(spans) == len(IDX_SECTIONS):
        order = [spans[kw][0] for kw in IDX_SECTIONS]
        if order != sorted(order) or len(set(order)) != len(order):
            problems.append(
                ("E-IDX-SEC",
                 "五个必备小节的顺序必须是 " + " → ".join(f"## {kw}" for kw in IDX_SECTIONS))
            )

    # ---- 条目扫描（一、主题清单 区间内的列表项）
    entry_problems: list[tuple[str, str]] = []
    link_problems: list[tuple[str, str]] = []
    kind_problems: list[tuple[str, str]] = []
    targets_seen: list[str] = []
    span1 = spans.get("一、主题清单")
    if span1 is not None:
        for i in range(span1[0] + 1, span1[1]):
            s = lines[i].strip()
            m_item = re.match(r"^([-*+]|\d+[.)])(\s+|$)", s)
            if not m_item:
                continue
            body = s[m_item.end():].strip()
            m_link = IDX_ENTRY_LINK_RE.match(body)
            m_ev = IDX_ENTRY_EVIDENCE_RE.search(body)
            m_dash = IDX_ENTRY_DASH_RE.match(body[m_link.end():]) if m_link else None

            # E-IDX-ENTRY
            if not m_link:
                entry_problems.append(
                    ("E-IDX-ENTRY",
                     f"第 {i + 1} 行条目缺少链接（应写成 - [短名](./短名/README.md) — <一句话结论>"
                     "（证据：<类型>；代码：<有|无>））")
                )
            elif not m_dash:
                entry_problems.append(
                    ("E-IDX-ENTRY", f"第 {i + 1} 行条目缺少「 — 」分隔（链接与一句话结论之间）")
                )
            if not m_ev:
                entry_problems.append(
                    ("E-IDX-ENTRY",
                     f"第 {i + 1} 行条目缺少证据括注（形如「（证据：<类型>；代码：<有|无>）」）")
                )
            elif not IDX_ENTRY_CODE_RE.search(m_ev.group(1)):
                entry_problems.append(
                    ("E-IDX-ENTRY", f"第 {i + 1} 行条目证据括注缺少「代码：有|无」")
                )

            if m_link:
                target = m_link.group(2)
                targets_seen.append(target)
                if not IDX_ENTRY_TARGET_RE.match(target):
                    entry_problems.append(
                        ("E-IDX-ENTRY",
                         f"第 {i + 1} 行条目的链接目标必须是 ./<短名>/README.md，实际：{target}")
                    )
                # E-IDX-LINK（按索引文件所在目录相对解析）
                if not (index_dir / target).exists():
                    link_problems.append(
                        ("E-IDX-LINK",
                         f"第 {i + 1} 行条目链接的目标文件不存在：{target}（相对 {path.name} 所在目录解析）")
                    )
            # E-IDX-SRCKIND（证据括注里 `；` 之前那一段作为类型词）
            if m_ev:
                kind = re.split(r"[；;]", m_ev.group(1))[0].strip()
                if kind not in IDX_SRC_KINDS:
                    kind_problems.append(
                        ("E-IDX-SRCKIND",
                         f"第 {i + 1} 行条目证据类型「{kind}」非法，只允许 {'/'.join(IDX_SRC_KINDS)}")
                    )

    executed += 1
    problems.extend(entry_problems)

    executed += 1
    problems.extend(link_problems)

    # E-IDX-DUP
    executed += 1
    dup_seen: dict[str, int] = {}
    for target in targets_seen:
        dup_seen[target] = dup_seen.get(target, 0) + 1
    for target, n in dup_seen.items():
        if n >= 2:
            problems.append(("E-IDX-DUP", f"链接目标重复登记：{target} 共出现 {n} 次"))

    executed += 1
    problems.extend(kind_problems)

    # W-IDX-ORPHAN（反向完整性：索引所在目录一层的子目录里有 README.md 却没被登记）
    executed += 1
    linked = set()
    for target in targets_seen:
        try:
            linked.add((index_dir / target).resolve())
        except OSError:
            pass
    if index_dir.is_dir():
        for d in sorted(index_dir.iterdir(), key=lambda p: p.name):
            if not d.is_dir() or d.name.startswith("."):
                continue
            readme = d / "README.md"
            if not readme.is_file():
                continue
            try:
                if readme.resolve() in linked:
                    continue
            except OSError:
                pass
            problems.append(
                ("W-IDX-ORPHAN", f"子目录笔记未登记进「一、主题清单」：{d.name}/README.md")
            )

    # W-IDX-TERM
    executed += 1
    term_msg = ""
    span2 = spans.get("二、术语速查")
    if span2 is None:
        term_msg = "缺少「## 二、术语速查」小节，无法检查术语表"
    else:
        a, b = span2
        head_i = next((i for i in range(a + 1, b) if lines[i].strip().startswith("|")), None)
        if head_i is None:
            term_msg = "「二、术语速查」内没有表格，必须画三列表 | 术语 | 一句话解释 | 首次出现 |"
        else:
            head = lines[head_i].strip()
            if re.sub(r"\s+", "", head) != IDX_TERM_HEADER:
                term_msg = f"术语速查表表头必须恰为三列 | 术语 | 一句话解释 | 首次出现 |，实际：{head}"
            else:
                data_rows = 0
                j = head_i + 1
                while j < b and lines[j].strip().startswith("|"):
                    cells = [c.strip() for c in split_cells(lines[j]) if c.strip()]
                    if not (cells and all(IDX_SEPARATOR_CELL_RE.match(c) for c in cells)):
                        data_rows += 1
                    j += 1
                if data_rows == 0:
                    term_msg = "术语速查表至少需要一行数据（当前只有表头与分隔行）"
    if term_msg:
        problems.append(("W-IDX-TERM", term_msg))

    # W-IDX-UPDATE
    executed += 1
    if not any(IDX_UPDATE_RE.match(ln) for ln in lines):
        problems.append(
            ("W-IDX-UPDATE", "缺少「最近更新」行（增量续写要留时间戳）：> 最近更新：YYYY-MM-DD")
        )

    return problems, executed


# ---------------------------------------------------------------- terms 模式

def check_terms(lines: list[str], path: Path) -> tuple[list[tuple[str, str]], int]:
    """校验专业术语表 术语-<短名>.md（模式 H，中英对照全量术语）。

    契约见 references/terms-template.md：六节骨架 + 六列表头 + 11 个检查码。
    出处列从实现第一天起就同时接受裸标记与带页码形式（[原文 p.7] / [原文 p.7-8]）——
    FAQ_CITE_RE 那种"模板说合法、校验器不认"的口径不一致不允许在新模式里复发。
    """
    problems: list[tuple[str, str]] = []
    executed = 0
    headings = heading_map(lines)
    h1_idx = [i for i, ln in enumerate(lines) if H1_RE.match(ln)]
    fi = first_nonempty(lines)

    # E-TERM-H1
    executed += 1
    head_text = lines[fi].strip() if fi is not None else ""
    if fi is None or len(h1_idx) != 1 or h1_idx[0] != fi or not TERMS_H1_RE.match(head_text):
        problems.append(
            ("E-TERM-H1",
             "首个非空行必须是唯一的 H1「# <短名> 专业术语表（中英对照）」，"
             f"实际：{head_text or '（无）'}")
        )

    # E-TERM-SEC
    executed += 1
    spans: dict[str, tuple[int, int]] = {}
    for kw in TERMS_SECTIONS:
        sp = section_span(lines, headings, kw)
        if sp is not None:
            spans[kw] = sp
    for kw in TERMS_SECTIONS:
        if kw not in spans:
            problems.append(("E-TERM-SEC", f"缺少必备小节：## {kw}"))
    if len(spans) == len(TERMS_SECTIONS):
        order = [spans[kw][0] for kw in TERMS_SECTIONS]
        if order != sorted(order):
            problems.append(
                ("E-TERM-SEC",
                 "六个必备小节必须按此顺序：" + " → ".join(f"## {kw}" for kw in TERMS_SECTIONS))
            )

    # ---- 术语注册区（二、三两节）逐表逐行扫描
    terms_seen: dict[str, list[int]] = {}
    abbr_seen: set[str] = set()
    table_problems: list[tuple[str, str]] = []
    en_problems: list[tuple[str, str]] = []
    empty_problems: list[tuple[str, str]] = []
    cite_problems: list[tuple[str, str]] = []
    dup_problems: list[tuple[str, str]] = []
    data_row_count = 0

    for sec in TERMS_TERM_SECTIONS:
        sp = spans.get(sec)
        if sp is None:
            continue
        start, end = sp
        for a, b in table_runs(lines[start + 1:end]):
            base = start + 1 + a
            header_cells = [c.strip() for c in split_cells(lines[base])]
            if header_cells != list(TERMS_HEADER_CELLS):
                table_problems.append(
                    ("E-TERM-TABLE",
                     f"第 {base + 1} 行表头必须是六列「{' | '.join(TERMS_HEADER_CELLS)}」，"
                     f"实际：{' | '.join(header_cells) or '（空）'}")
                )
                continue
            for j in range(base + 1, start + 1 + b):
                if not lines[j].strip().startswith("|"):
                    continue
                cells = [c.strip() for c in split_cells(lines[j])]
                if not cells or all(IDX_SEPARATOR_CELL_RE.match(c) for c in cells if c):
                    continue  # 分隔行或空行
                data_row_count += 1
                if len(cells) != len(TERMS_HEADER_CELLS):
                    table_problems.append(
                        ("E-TERM-TABLE",
                         f"第 {j + 1} 行数据是 {len(cells)} 列，六列表头要求 6 列")
                    )
                    continue
                en, abbr, cn, expl, role, cite = cells

                # E-TERM-EN：本模式存在的理由——英文原词必须留下
                if not TERMS_EN_WORD_RE.search(en):
                    en_problems.append(
                        ("E-TERM-EN",
                         f"第 {j + 1} 行「英文术语」列缺少英文原词（必须含拉丁字母）：{en or '（空）'}")
                    )
                # E-TERM-EMPTY
                bad_cols = [
                    name for name, val in (("中文译名", cn), ("一句话解释", expl), ("在本文中的角色", role))
                    if not val or val.lower() in TERMS_PLACEHOLDERS
                ]
                if bad_cols:
                    empty_problems.append(
                        ("E-TERM-EMPTY",
                         f"第 {j + 1} 行这些列为空或占位符：{'、'.join(bad_cols)}")
                    )
                # E-TERM-CITE
                if not TERMS_CITE_RE.search(cite):
                    cite_problems.append(
                        ("E-TERM-CITE",
                         f"第 {j + 1} 行「出处」列不是合法来源标记"
                         f"（[原文 p.7] 这类带页码形式合法）：{cite or '（空）'}")
                    )
                if abbr and abbr.lower() not in TERMS_PLACEHOLDERS:
                    abbr_seen.add(abbr.lower())
                key = re.sub(r"\s+", " ", en).strip().lower()
                if key:
                    terms_seen.setdefault(key, []).append(j + 1)

    executed += 1
    problems.extend(table_problems)
    executed += 1
    problems.extend(en_problems)
    executed += 1
    problems.extend(empty_problems)
    executed += 1
    problems.extend(cite_problems)

    # E-TERM-DUP（跨二、三两节）
    executed += 1
    for key, lns in terms_seen.items():
        if len(lns) >= 2:
            dup_problems.append(
                ("E-TERM-DUP",
                 f"同一英文术语重复登记 {len(lns)} 次（第 {'、'.join(str(n) for n in lns)} 行）：{key}")
            )
    problems.extend(dup_problems)

    # W-TERM-MIN（"全量"的下限代理指标，不是完整性证明）
    executed += 1
    if data_row_count < TERMS_MIN_ROWS:
        problems.append(
            ("W-TERM-MIN",
             f"二、三两节合计只有 {data_row_count} 行术语，少于 {TERMS_MIN_ROWS} 行"
             "（这只是「全量收录」的下限代理指标，不是完整性证明）")
        )

    # W-TERM-QUOTE
    executed += 1
    quote_count = 0
    sp5 = spans.get(TERMS_QUOTE_SECTION)
    if sp5 is not None:
        for i in range(sp5[0] + 1, sp5[1]):
            s = lines[i].strip()
            if not TERMS_ITEM_RE.match(s):
                continue
            if TERMS_EN_WORD_RE.search(s) and TERMS_CITE_RE.search(s):
                quote_count += 1
    if quote_count < TERMS_MIN_QUOTES:
        problems.append(
            ("W-TERM-QUOTE",
             f"第五节英文原句摘录只有 {quote_count} 条合格条目"
             f"（需要 ≥{TERMS_MIN_QUOTES} 条：英文原句 + 中文直译 + 来源标记）")
        )

    # ---- 六、缩略语索引
    abbr_entries: list[str] = []
    sp6 = spans.get(TERMS_ABBR_SECTION)
    if sp6 is not None:
        for a, b in table_runs(lines[sp6[0] + 1:sp6[1]]):
            base = sp6[0] + 1 + a
            for j in range(base + 1, sp6[0] + 1 + b):
                if not lines[j].strip().startswith("|"):
                    continue
                cells = [c.strip() for c in split_cells(lines[j])]
                if not cells or all(IDX_SEPARATOR_CELL_RE.match(c) for c in cells if c):
                    continue
                if TERMS_ABBR_RE.match(cells[0]):
                    abbr_entries.append(cells[0])

    # W-TERM-ABBR（悬空缩写）
    executed += 1
    dangling = [a for a in abbr_entries if a.lower() not in abbr_seen]
    if dangling:
        problems.append(
            ("W-TERM-ABBR",
             f"缩略语索引里的缩写未在二、三节的「缩写」列出现过（悬空缩写）：{'、'.join(dangling)}")
        )

    # W-TERM-SORT
    executed += 1
    keys = [a.lower() for a in abbr_entries]
    if keys != sorted(keys):
        problems.append(("W-TERM-SORT", "缩略语索引未按字母升序排列"))

    return problems, executed


# ---------------------------------------------------------------- 模式判定与入口

def detect_mode(path: Path, lines: list[str], index_marker: bool = False) -> str:
    if index_marker:  # 合集索引标记最先判定，优先于文件名词干
        return "index"
    name = path.name
    if "深读" in name or "精读" in name:
        return "deep"
    if "表格" in name or "填表" in name:
        return "table"
    if "思维导图" in name:
        return "mindmap"
    low = name.lower()
    if "导图" in name or "mermaid" in low or "mmd" in low:
        return "mmd"
    if "难点" in name or "问答" in name or "faq" in low:
        return "faq"
    if "术语" in name or "terms" in low:
        return "terms"
    if "综述" in name:
        return "review"
    headings = heading_map(lines)
    if any(lvl == 2 and "研究背景与目标" in t for _, lvl, t in headings):
        return "mindmap"
    tables = table_runs(lines)
    if len(tables) == 1:
        a, _ = tables[0]
        if re.sub(r"\s+", "", lines[a].strip()) == "|维度|内容|":
            return "table"
    if any(lvl in (2, 3) and "研究主题概述" in t for _, lvl, t in headings):
        return "review"
    return "deep"


def _fail(msg: str) -> int:
    print(f"[ERROR] {msg}")
    return 2


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv) if argv is None else list(argv)
    if args and args[0].endswith(".py"):  # 允许 main(["check_paper_note.py", ...]) 或 main([...])
        args = args[1:]

    target: str | None = None
    mode = "auto"
    refs: int | None = None
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-h", "--help"):
            print(__doc__)
            return 2
        if a == "--mode" or a.startswith("--mode="):
            if a == "--mode":
                i += 1
                if i >= len(args):
                    return _fail("--mode 缺少取值")
                mode = args[i]
            else:
                mode = a.split("=", 1)[1]
        elif a == "--refs" or a.startswith("--refs="):
            raw = a.split("=", 1)[1] if a.startswith("--refs=") else ""
            if not raw:
                i += 1
                if i >= len(args):
                    return _fail("--refs 缺少取值")
                raw = args[i]
            try:
                refs = int(raw)
            except ValueError:
                return _fail(f"--refs 必须是正整数，实际：{raw}")
            if refs < 1:
                return _fail(f"--refs 必须是正整数，实际：{raw}")
        elif a.startswith("-"):
            return _fail(f"未知参数：{a}")
        elif target is None:
            target = a
        else:
            return _fail(f"只接受一个 Markdown 文件，多余参数：{a}")
        i += 1

    if target is None:
        print(__doc__)
        return 2
    if mode not in MODES:
        return _fail(f"--mode 只支持 {'|'.join(MODES)}，实际：{mode}")

    path = Path(target)
    if not path.exists():
        return _fail(f"文件不存在：{path}")
    if not path.is_file():
        return _fail(f"不是普通文件：{path}")
    if path.suffix.lower() not in (".md", ".markdown"):
        return _fail(f"仅支持 Markdown 文件（.md/.markdown），实际：{path.name}")
    raw = None
    for enc in ("utf-8", "utf-8-sig"):
        try:
            raw = path.read_text(encoding=enc)
            break
        except UnicodeDecodeError:
            continue
        except OSError as exc:
            return _fail(f"文件不可读：{path}（{exc}）")
    if raw is None:
        return _fail(f"文件不可读（需 UTF-8 编码）：{path.name}")

    text = strip_comments(raw)
    raw_lines = text.split("\n")
    masked_lines = mask_fences(text).split("\n")

    # index 模式的识别标记是 HTML 注释，故必须在剔除注释之前的原文上判定
    orig_lines = raw.split("\n")
    fi_raw = first_nonempty(orig_lines)
    index_marker = fi_raw is not None and orig_lines[fi_raw].strip() == INDEX_MARKER

    if mode == "auto":
        mode = detect_mode(path, raw_lines, index_marker)

    if mode == "deep":
        problems, executed = check_deep(raw_lines, masked_lines)
    elif mode == "table":
        problems, executed = check_table(masked_lines)
    elif mode == "mindmap":
        problems, executed = check_mindmap(raw_lines)
    elif mode == "mmd":
        problems, executed = check_mmd(raw_lines)
    elif mode == "faq":
        problems, executed = check_faq(raw_lines)
    elif mode == "index":
        problems, executed = check_index(raw_lines, index_marker, path)
    elif mode == "terms":
        problems, executed = check_terms(raw_lines, path)
    else:
        problems, executed = check_review(raw_lines, refs)

    errors = [(c, m) for c, m in problems if c.startswith("E")]
    warns = [(c, m) for c, m in problems if c.startswith("W")]
    for code, msg in errors:
        print(f"[ERROR] {code} {path.name}: {msg}")
    for code, msg in warns:
        print(f"[WARN ] {code} {path.name}: {msg}")
    if errors:
        print(f"[ERROR] {len(errors)} 条 ERROR，必须修复")
        return 1
    if warns:
        print(f"[WARN ] 无 ERROR，但存在 {len(warns)} 条 WARN，需人工判断")
        return 0
    print(f"[PASS ] {executed} 项检查全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
