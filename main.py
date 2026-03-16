import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import PchipInterpolator
from solver import calculate_losses

# --- 1. 元器件数据库 ---
mos_lib = [
    {'name': 'ISC007', 'Rdson': 0.7e-3, 'Qgd': 21e-9, 'Qrr': 361e-9, 'Coss': 3300e-12, 'Rthjc': 0.58, 'Area': 30},
    {'name': 'BSC026', 'Rdson': 2.6e-3, 'Qgd': 16e-9, 'Qrr': 92e-9, 'Coss': 840e-12, 'Rthjc': 0.8, 'Area': 30},
    {'name': 'BSC040', 'Rdson': 4.0e-3, 'Qgd': 9.3e-9, 'Qrr': 43e-9, 'Coss': 500e-12, 'Rthjc': 1.2, 'Area': 30},
    {'name': 'BSC014', 'Rdson': 1.4e-3, 'Qgd': 16e-9, 'Qrr': 139e-9, 'Coss': 1500e-12, 'Rthjc': 0.8, 'Area': 30},
    {'name': 'ISC060', 'Rdson': 6.0e-3, 'Qgd': 2.9e-9, 'Qrr': 45e-9, 'Coss': 330e-12, 'Rthjc': 3.0, 'Area': 30}
]

l_real_vol = np.array([1130, 2462.4, 10648])
l_real_dcr = np.array([5.7e-3, 3.8e-3, 0.9e-3])
l_real_val = np.array([4.7e-6, 4.7e-6, 4.3e-6])

v_vol_sweep = np.linspace(l_real_vol.min(), l_real_vol.max(), 35)
v_dcr_interp = PchipInterpolator(l_real_vol, l_real_dcr)(v_vol_sweep)
v_val_interp = PchipInterpolator(l_real_vol, l_real_val)(v_vol_sweep)

# --- 2. 系统参数 ---
vin, vout, iout = 40, 12, 20
f_sweep = np.linspace(100e3, 500e3, 15)
results = []

# --- 3. 核心计算 ---
for mos in mos_lib:
    for i in range(len(v_vol_sweep)):
        l_params = (v_vol_sweep[i], v_dcr_interp[i], v_val_interp[i])
        for fs in f_sweep:
            eff, dens, safe = calculate_losses(mos, l_params, vin, vout, iout, fs)
            results.append([eff, dens, fs/1000, safe])

res = np.array(results)

# --- 4. 提取帕累托前沿 (对齐你的从右往左逻辑) ---
safe_res = res[res[:, 3] == 1]
# 按密度降序排列
safe_res = safe_res[safe_res[:, 1].argsort()[::-1]]

pareto_points = []
if len(safe_res) > 0:
    pareto_points.append(safe_res[0])
    current_max_eff = safe_res[0, 0]
    for p in safe_res[1:]:
        if p[0] > current_max_eff:
            pareto_points.append(p)
            current_max_eff = p[0]

pareto_points = np.array(pareto_points)
pareto_points = pareto_points[pareto_points[:, 1].argsort()] # 排序方便连线

# --- 5. 画图 ---
plt.figure(figsize=(10, 6))
unsafe = res[res[:, 3] == 0]
safe = res[res[:, 3] == 1]

plt.scatter(unsafe[:, 1], unsafe[:, 0], c='gray', alpha=0.3, s=15, label='Unsafe')
sc = plt.scatter(safe[:, 1], safe[:, 0], c=safe[:, 2], cmap='jet', s=35, label='Candidates')
plt.plot(pareto_points[:, 1], pareto_points[:, 0], 'r-s', linewidth=2, label='Pareto Front')

plt.colorbar(sc, label='Frequency (kHz)')
plt.xlabel('Power Density (W/cm^3)')
plt.ylabel('Efficiency (%)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.title(f'Pareto Front Python Version (Vin={vin}V, Iout={iout}A)')
plt.show()

