import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import PchipInterpolator
from solver import calculate_losses  # 确保 solver.py 在同级目录

# --- 1. 页面配置 ---
st.set_page_config(page_title="Buck Pareto Optimizer", layout="wide")
st.title("⚡ Buck Converter Pareto Frontier Optimizer")
st.markdown("该工具集成了电热耦合模型与多种元器件数据库，支持实时帕累托寻优。")

# --- 2. 侧边栏：核心参数输入 ---
st.sidebar.header("System Settings")
vin = st.sidebar.slider("Input Voltage (V)", 20, 60, 40)
vout = st.sidebar.slider("Output Voltage (V)", 5, 30, 12)
iout = st.sidebar.slider("Load Current (A)", 1, 30, 20)
rth_ext = st.sidebar.select_slider("Cooling Condition (Rth_ext)", options=[0.5, 1.0, 2.0, 5.0], value=1.0)

# --- 3. 元器件数据库 ---
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

# --- 4. 寻优计算逻辑 ---
if st.sidebar.button("🚀 Start Pareto Analysis"):
    with st.spinner('Calculating thermal equilibrium...'):
        v_vol_sweep = np.linspace(l_real_vol.min(), l_real_vol.max(), 35)
        v_dcr_interp = PchipInterpolator(l_real_vol, l_real_dcr)(v_vol_sweep)
        v_val_interp = PchipInterpolator(l_real_vol, l_real_val)(v_vol_sweep)

        f_sweep = np.linspace(100e3, 500e3, 15)
        all_results = []

        for mos in mos_lib:
            for i in range(len(v_vol_sweep)):
                l_params = (v_vol_sweep[i], v_dcr_interp[i], v_val_interp[i])
                for fs in f_sweep:
                    eff, dens, safe = calculate_losses(mos, l_params, vin, vout, iout, fs, rth_ext=rth_ext)
                    all_results.append([eff, dens, fs / 1000, safe])

        res = np.array(all_results)
        safe_res = res[res[:, 3] == 1]

        # --- 5. 绘图与展示 (根据导师意见修改部分) ---
        fig, ax = plt.subplots(figsize=(10, 6))

        # 绘制过热点
        unsafe = res[res[:, 3] == 0]
        if len(unsafe) > 0:
            ax.scatter(unsafe[:, 1], unsafe[:, 0], c='lightgray', s=15, alpha=0.3, label='Thermal Unsafe')

        # 绘制安全点与帕累托前沿
        if len(safe_res) > 0:
            sc = ax.scatter(safe_res[:, 1], safe_res[:, 0], c=safe_res[:, 2], cmap='jet', s=40,
                            label='Optimal Candidates')
            cbar = plt.colorbar(sc, ax=ax)
            cbar.set_label('Switching Frequency (kHz)', fontweight='bold')

            # 提取帕累托点
            safe_sorted = safe_res[safe_res[:, 1].argsort()[::-1]]
            pareto_pts = [safe_sorted[0]]
            curr_max_eff = safe_sorted[0, 0]
            for p in safe_sorted[1:]:
                if p[0] > curr_max_eff:
                    pareto_pts.append(p)
                    curr_max_eff = p[0]

            pareto_pts = np.array(pareto_pts)
            pareto_pts = pareto_pts[pareto_pts[:, 1].argsort()]
            ax.plot(pareto_pts[:, 1], pareto_pts[:, 0], 'r-s', linewidth=2, markersize=6, label='Pareto Front')

            # --- 核心修改：坐标轴标注与样式 ---
            ax.set_xlabel(r'Power Density ($W/cm^3$)', fontsize=12, fontweight='bold')
            ax.set_ylabel('Efficiency (%)', fontsize=12, fontweight='bold')
            ax.set_title(f'Efficiency vs. Power Density Pareto Frontier (Iout={iout}A)', fontsize=14, fontweight='bold')

            # 开启网格线（学术图表必备）
            ax.grid(True, which='both', linestyle='--', alpha=0.5)

            # 设置图例位置
            ax.legend(loc='lower left', frameon=True, shadow=True)

            st.pyplot(fig)
            st.success(f"Successfully found {len(safe_res)} thermal-safe design candidates!")
        else:
            # 即使全红也要标出坐标轴
            ax.set_xlabel(r'Power Density ($W/cm^3$)', fontweight='bold')
            ax.set_ylabel('Efficiency (%)', fontweight='bold')
            ax.grid(True, linestyle='--', alpha=0.5)
            st.pyplot(fig)
            st.error("❌ Thermal Limit Exceeded: All points are unsafe under current cooling conditions.")
else:
    st.info("👈 Adjust parameters and click the button to visualize the Pareto Frontier.")