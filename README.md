# 40V/20A Buck Converter Pareto Optimization Tool

**Author:** Pan Tianqi (NTU MSc Power Engineering)  
**Status:** Engineering Ready / Research Grade

---

## 1. 核心理论模型 (Detailed Mathematical Modeling)

本项目通过精确的物理方程对 Buck 变换器的损耗进行了拆解，重点修正了高频大电流（40V/20A）工况下的模型偏差。

### A. MOSFET 损耗：上下管非对称建模
由于 Buck 变换器的同步整流特性，上管 (HS) 与下管 (LS) 的开关行为截然不同，模型对此进行了精准区分：

* **上管 (High-Side MOSFET):** 处于硬开关状态。
    * **开关损耗 ($1/6$ 线性积分模型):** 计入电压电流交叉重叠损耗及反向恢复损耗 ($Q_{rr}$)。
    $$P_{sw,HS} = \left( \frac{1}{6} V_{in} I_{out} t_{sw} + V_{in} Q_{rr} \right) f_s$$
* **下管 (Low-Side MOSFET):** 处于同步整流状态，具有准零电压开启 (ZVS) 特性。
    * **谐振开关损耗 ($1/48$ 模型):** 针对下管输出电容 $C_{oss}$ 在死区时间内与回路杂散电感的谐振项进行建模：
        $$P_{sw,LS} = \left( \frac{t_{f}^2}{48 \cdot C_{oss}} \right) I_{peak}^2 f_s$$
    * **导通损耗:** 计入温度补偿后的 $R_{ds(on)}$ 导通损耗。

### B. 功率电感损耗：磁芯损耗修正
针对一体成型电感，本项目对经典的 Steinmetz 公式进行了三项关键物理修正，解决了常规建模中温度评估过高的问题：

1.  **磁感应强度修正 ($B_{pk}$):** 严格执行 $B_{pk} = \frac{1}{2} \Delta B$。由于 Steinmetz 系数基于磁极峰值标定，该修正避免了约 4.3 倍的计算误差。
2.  **有效体积修正 ($k_{fill}$):** 引入填充系数 $k_{fill} = 0.6$，区分封装体积 ($V_{pkg}$) 与有效磁芯体积 ($V_e$)，剔除铜线绕组占据的非磁性空间。
    $$V_e = V_{pkg} \cdot k_{fill}$$
3.  **损耗密度单位对齐:** 严格执行 $mW/cm^3$ 到 $W$ 的 $10^{-3}$ 量级换算：
    $$P_{core} = \left( k \cdot f_{kHz}^{c} \cdot B_{pk}^{b} \right) \cdot V_e \cdot 10^{-3}$$

---

## 2. 工程结构 (Project Structure)

```text
.
├── solver.py          # 物理底层：封装损耗方程、电热耦合迭代逻辑
├── main.py            # 调度中心：执行参数扫描、帕累托前沿提取与可视化
├── README.md          # 说明文档：包含数学模型与使用手册
└── requirements.txt   # 环境清单：numpy, scipy, matplotlib