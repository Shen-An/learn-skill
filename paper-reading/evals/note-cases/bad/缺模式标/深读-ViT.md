# ViT 精读讲解

> fixture 桩文件：bad/缺模式标 只校验同目录的 `README.md`，本文件只用于让链接指向真实文件。

patch 嵌入 = 卷积核大小与步长都取 16 的卷积层，之后接标准 Transformer 编码器 [原文 p.3]。
