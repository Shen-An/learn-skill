<!-- paper-reading: note-index -->

# ResNet 论文笔记索引

论文：Deep Residual Learning for Image Recognition（CVPR 2016，arXiv:1512.03385，Kaiming He 等）

一句话结论：把"让网络直接学目标映射"改成"学残差映射加恒等短路"，使极深网络不再随深度退化，152 层在 ImageNet 上把 top-5 错误率压到 3.57% 并拿下当年冠军，代价是短路分支带来的显存占用与通道数翻倍时的对齐处理，且论文未解释为什么恒等映射比直接拟合更容易优化。

## 文件

- [深读-ResNet.md](./深读-ResNet.md)：精读讲解（模式 A）——退化问题、残差块、瓶颈结构、与 Highway/VGG 的对比
- [导图-ResNet.md](./导图-ResNet.md)：思维导图的 Mermaid 可渲染形态（模式 E）

## 证据强度提示

- 高置信（原文可核）：论文身份与 arXiv 编号；152 层 top-5 错误率 3.57% 的表格 [原文 p.6]。
- 低置信（我的推断）：把退化问题归因为优化难度而非表达能力不足。

## 待核入口

- 正文：arXiv:1512.03385
- 对照工作：Highway Networks 的门控短路
