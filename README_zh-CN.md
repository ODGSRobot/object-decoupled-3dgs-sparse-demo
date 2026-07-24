# 面向稀疏示教的对象解耦 3DGS 结构约束数据扩展

本仓库对应论文 **Object-Decoupled 3D Gaussian Splatting for
Structure-Constrained Data Expansion in Sparse-Demonstration Robot Learning**，
提供论文相关的核心实现、复现配置和 GitHub Pages 项目主页。

[项目主页](docs/index.html) · [复现说明](docs/REPRODUCIBILITY.md) ·
[私有数据接口说明](docs/DATA.md) · [English README](README.md)

## 方法范围

完整闭环包含三个部分：

1. 由少量真实示教训练初始策略，并在训练阶段加入时序一致性与速度平滑正则；
2. 将对象与背景解耦，使用刚体位姿范围和铰链参数构造可交互 3DGS 场景；
3. 在结构随机化场景中执行虚拟推理，经运动学、几何检查和人工复核后，
   仅将通过筛选的轨迹写回数据集并进行增量训练。

本文不提出新的 VLA 网络结构。训练正则不改变原模型结构、推理路径、
动作采样器和推理开销。当前结构范围仅包括刚体与铰链对象，不包括滑轨。

## 快速检查

```bash
python -m venv .venv
python -m pip install -e ".[dev,figures]"
python -m pytest
```

数据校验和绘图脚本仅接受显式指定的作者本地数据或独立采集数据路径。
公开仓库不包含逐试验机器人记录、虚拟推理日志、重建测量值或消融记录。

## 开源边界

仓库包含核心代码、配置、矢量论文图和压缩 GIF。记录级实验数据、原始实验
视频、模型权重、第三方完整源码、论文投稿文件、EndNote 库、PPT 工作文件
和修改过程文件不纳入公开仓库。依赖版本与许可见
[docs/UPSTREAMS.md](docs/UPSTREAMS.md)。
