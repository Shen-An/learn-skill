<!-- paper-reading: note-index -->

# ViT 论文笔记索引

论文：An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale（ICLR 2021，arXiv:2010.11929，Alexey Dosovitskiy 等）

一句话结论：把图像切成 16×16 的 patch 当成词元直接喂给标准 Transformer，去掉卷积先验后只在足够大的数据上预训练才能超过 CNN，证明"归纳偏置"可以让位给数据规模，代价是中小数据集上明显不如 ResNet、且注意力对高分辨率输入的平方成本限制了稠密预测任务。

## 文件

- [深读-ViT.md](./深读-ViT.md)：精读讲解（模式 A）——patch 嵌入、位置编码、混合架构、数据规模消融
- [导图-ViT.md](./导图-ViT.md)：思维导图的 Mermaid 可渲染形态

## 证据强度提示

- 高置信（原文可核）：论文身份与 arXiv 编号；JFT-300M 预训练后的 ImageNet 准确率对比表 [原文 p.5]。
- 低置信（我的推断）：把"数据规模决定成败"视为对卷积先验必要性的否定。

## 待核入口

- 正文：arXiv:2010.11929
- 对照工作：BiT 与 Noisy Student 的迁移成绩
