<!-- paper-reading: note-index -->

# Muon 论文笔记索引

论文：Muon is Scalable for LLM Training（arXiv:2502.16982，2025，Moonshot AI，Keller Jordan 等）

一句话结论：把原本只在 CIFAR 级小模型上验证过的 Muon 优化器（对动量矩阵做 Newton-Schulz 正交化后再更新）搬到 3B/16B 的 MoE 预训练上，靠"一致性 RMS 缩放"对齐 AdamW 的更新尺度并复用权重衰减与动量 warmup，省下约 52% 的训练算力，代价是每步多一次正交化迭代、且作者自述更大规模下的收益尚未完整验证。

**交付约定（skill v1.7.0）**：深读、表格、导图、难点、术语五件各自独立成文件；公式一律用 Markdown 数学语法；本轮未做思维导图的文本大纲形态（C），故只有 Mermaid 形态（E）。

## 文件

- [深读-Muon.md](./深读-Muon.md)：精读讲解（模式 A）——背景谱系、符号表、正交化更新与 RMS 匹配两模块、实验、贡献、局限、证据与出处
- [表格-Muon.md](./表格-Muon.md)：逐篇填表（模式 B）——九维单表，每格 ≤3 句
- [导图-Muon.md](./导图-Muon.md)：四分支思维导图的 Mermaid 可渲染形态（模式 E，需 Obsidian/GitHub 才能出图）
- [难点-Muon.md](./难点-Muon.md)：难点与解答（模式 F）——7 条卡点，每条解答带来源标记
- [术语-Muon.md](./术语-Muon.md)：中英对照全量专业术语表（模式 H）——41 条术语 + 易混对照 + 缩略语索引
- [_source/Muon-2502.16982.md](./_source/Muon-2502.16982.md)：arXiv 页面与正文片段的抽取产物（带页锚点）

## 证据强度提示

- 高置信（原文/代码可核）：论文身份与 arXiv 编号；Table 2 的 3B/16B 验证集损失对比；正交化系数与迭代步数 [原文 p.3]。
- 低置信（我的推断，非论文主张）：52% 算力节省的折算口径；Muon 与 AdamW 学习率区间的可比性。
- 未核实（本版本无法核）：附录里的收敛性讨论；16B 以上规模的消融；官方代码与论文描述的差异。

## 待核入口

- 正文：arXiv:2502.16982（附录含收敛性讨论）
- 代码：github.com/KellerJordan/Muon（正交化实现与 `zeropower_via_newtonschulz5`）
- 对照工作：Shampoo / SOAP 等二阶方法在同等规模下的报告值
