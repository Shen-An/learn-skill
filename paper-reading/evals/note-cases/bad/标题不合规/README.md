<!-- paper-reading: note-index -->

# Attention Is All You Need（Transformer）

论文：Attention Is All You Need（NeurIPS 2017，arXiv:1706.03762，Ashish Vaswani 等）

一句话结论：把序列建模的全部循环与卷积结构换成缩放点积自注意力加位置编码，使训练可以按时间步并行、长距离依赖的路径长度降到常数级，在 WMT14 英德上以更少的训练算力拿到 28.4 BLEU，代价是注意力对序列长度是平方复杂度、且推理时仍需自回归逐步解码。

## 文件

- [深读-Transformer.md](./深读-Transformer.md)：精读讲解（模式 A）——缩放点积注意力、多头、位置编码、训练与推理成本
- [导图-Transformer.md](./导图-Transformer.md)：思维导图的 Mermaid 可渲染形态（模式 E）

## 证据强度提示

- 高置信（原文可核）：论文身份与 arXiv 编号；WMT14 英德 28.4 BLEU 与训练成本表 [原文 p.8]。
- 低置信（我的推断）：把"路径长度变短"直接等同于"更容易学长距离依赖"。

## 待核入口

- 正文：arXiv:1706.03762
- 对照工作：ConvS2S 与 ByteNet 的路径长度对比
