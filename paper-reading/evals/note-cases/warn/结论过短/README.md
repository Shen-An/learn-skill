<!-- paper-reading: note-index -->

# LoRA 论文笔记索引

论文：LoRA: Low-Rank Adaptation of Large Language Models（ICLR 2022，arXiv:2106.09685，Edward J. Hu 等）

一句话结论：给预训练权重旁挂一个低秩分解矩阵、冻结原参数只训两个小矩阵，把可训练参数降了四个数量级。

## 文件

- [深读-LoRA.md](./深读-LoRA.md)：精读讲解（模式 A）——低秩假设、A/B 初始化、秩与缩放消融、与 Adapter 的对比
- [表格-LoRA.md](./表格-LoRA.md)：逐篇填表（模式 B）

## 证据强度提示

- 高置信（原文可核）：论文身份与 arXiv 编号；GPT-3 175B 上可训练参数 4.7M 的计数 [原文 p.1]。
- 低置信（我的推断）：把"训练显存下降"归因到优化器状态减少这一条的口径。

## 待核入口

- 正文：arXiv:2106.09685
- 代码：github.com/microsoft/LoRA
