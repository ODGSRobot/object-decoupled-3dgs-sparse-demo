# Pinned Upstream Systems

Large upstream systems are installed separately and are not vendored here.

| System | Paper configuration | Repository |
|---|---|---|
| NVIDIA Isaac GR00T | `n1.7-release`, Python 3.10, PyTorch 2.7.1, CUDA 12.8 | <https://github.com/NVIDIA/Isaac-GR00T> |
| NVIDIA 3DGRUT | commit `ffa1025ad7c13814527742273afb05ecc53925f3`, package 0.0.2 | <https://github.com/NVlabs/3dgrut> |
| Isaac Lab | extension 0.47.2 | <https://github.com/isaac-sim/IsaacLab> |
| LeIsaac | commit `099a4081b987628ae1009aded2da888314489a12`, v0.3.0 line | <https://github.com/LightwheelAI/LeIsaac> |

Before reproduction, verify that the commit URL resolves, read the upstream
license, and archive the final environment lockfile. The listed versions match
the current manuscript configuration; they are not statements that newer
versions are behaviorally identical.
