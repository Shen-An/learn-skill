<!-- paper-reading: note-index -->

# FlashAttention 论文笔记索引

论文：FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness（NeurIPS 2022，arXiv:2205.14135，Tri Dao 等）

一句话结论：把注意力计算的瓶颈从"算力"改判为"显存层级间的读写量"，用分块 + 在线 softmax 在 SRAM 内完成归约、反向时重算而不存注意力矩阵，结果是同精度下训练更快、可放到更长序列，代价是要为每代 GPU 的 SRAM 大小重写 kernel 且实现复杂度显著上升。

## 文件

- [深读-FlashAttention.md](./深读-FlashAttention.md)：精读讲解（模式 A）——IO 复杂度分析、分块 softmax、重算策略、与近似注意力的区别
- [难点-FlashAttention.md](./难点-FlashAttention.md)：难点与解答（模式 F）

## 证据强度提示

- 高置信（原文可核）：论文身份与 arXiv 编号；BERT-large 训练加速 15% 的表述 [原文 p.1]。
- 低置信（我的推断）：把长序列任务的收益主要归给显存占用下降这一条。

> 本文件刻意**没有** `## 待核入口` 小节——warn 用例只触发 `W-NOTE-ENTRY`。
