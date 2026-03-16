import numpy as np


def calculate_losses(mos, l_params, vin, vout, iout, fs, ta=25, rth_ext=1.0):
    # 系统常数
    d = vout / vin
    p_out = vout * iout
    v_cc, v_pl = 10, 2.6
    rg_ext, rg_int = 5, 1.6
    tf_ls = 11e-9
    n_turns = 10
    a_core_base = 50e-6
    fr_ac = 1.5
    k_st, b_st, c_st = 266.22, 2.103, 1.316

    l_vol, l_dcr, l_val = l_params
    tj, tl = ta, ta  # 初始温度

    # 热迭代 (30次)
    for _ in range(30):
        # 电阻温升修正
        r_now = mos['Rdson'] * (1 + 0.006 * (tj - 25))
        dcr_now = l_dcr * (1 + 0.0039 * (tl - 25))

        # 1. 导通损耗
        delta_il = (vin - vout) * d / (l_val * fs)
        p_cond = (iout ** 2 + (delta_il ** 2 / 12)) * r_now

        # 2. 开关损耗 (对齐 1/6 和 Qrr)
        i_gate = (v_cc - v_pl) / (rg_ext + rg_int)
        t_sw = mos['Qgd'] / i_gate
        p_sw_hs = (1 / 6) * vin * (iout - delta_il / 2) * t_sw * fs + (1 / 6) * vin * (
                    iout + delta_il / 2) * t_sw * fs + (vin * mos['Qrr'] * fs)
        p_sw_ls = (tf_ls ** 2 / (48 * mos['Coss'])) * (iout + delta_il / 2) ** 2 * fs

        # 3. 电感损耗
        p_wdg = (iout ** 2 * dcr_now) + ((delta_il / 3.46) ** 2 * dcr_now * fr_ac)

        # 动态磁芯截面积缩放
        a_core_dynamic = a_core_base * (l_vol / 1130) ** (2 / 3)
        delta_b = (vin * d * (1 - d)) / (fs * n_turns * a_core_dynamic)
        b_pk = delta_b / 2
        f_khz = fs / 1000
        vol_cm3 = 0.6 * l_vol / 1000
        p_core = (k_st * (b_pk ** b_st) * (f_khz ** c_st) * vol_cm3) * 1e-3 * 1.15 * 2.0

        # 热平衡更新
        tj_new = ta + (mos['Rthjc'] + rth_ext) * (p_cond + p_sw_hs + p_sw_ls)
        tl_new = ta + (p_wdg + p_core) * (150 / (l_vol ** (1 / 3)))

        if abs(tj_new - tj) < 0.1:
            break
        tj, tl = tj_new, tl_new

    eff = (p_out / (p_out + p_cond + p_sw_hs + p_sw_ls + p_wdg + p_core)) * 100
    density = p_out / ((l_vol + mos['Area'] * 5) / 1000)
    is_safe = (tj < 165 and tl < 145)

    return eff, density, is_safe