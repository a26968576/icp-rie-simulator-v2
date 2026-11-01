"""UI strings: Traditional Chinese (default, "中文 (English)") with optional English-only mode.

    from icpsim.i18n import tr, set_language
    tr("run")          -> "開始模擬 (Run Simulation)"   (zh)   /  "Run Simulation"  (en)
    tr("hdr_thick")    -> table headers use a line break: "厚度\\n(Thickness µm)"

Add a key here, never hard-code UI text in widgets.
"""
from __future__ import annotations

LANG = "zh"

# key: (中文, English)   -> zh mode shows "中文 (English)", en mode shows "English"
S = {
    # main window / toolbar
    "app_title": ("ICP-RIE 蝕刻模擬器 V2", "ICP-RIE Simulator V2"),
    "tab_process": ("製程", "Process"),
    "tab_materials": ("材料與蝕刻率", "Materials & Rates"),
    "tab_advanced": ("進階", "Advanced"),
    "grp_mask": ("①  光罩與材料", "Mask & Materials"),
    "grp_gas": ("②  氣體種類與流量", "Gas Species & Flows"),
    "grp_recipe": ("③  主要配方", "Main Recipe"),
    "grp_sources": ("蝕刻率來源", "Rate Sources"),
    "grp_backend": ("模型引擎與延伸 (ARDE / 負載)", "Model Backend & Extensions (ARDE / Loading)"),
    "grp_calib": ("校正 (實驗深度 vs 時間)", "Calibration (Depth vs Time)"),
    "grp_matlib": ("材料庫", "Material Library"),
    "grp_userrates": ("實驗蝕刻率 / 選擇比", "Experimental Rates / Selectivity"),
    "grp_litdb": ("文獻資料庫", "Literature Database"),
    "grp_matrix": ("選擇比矩陣", "Selectivity Matrix"),
    "run": ("開始模擬", "Run Simulation"),
    "run_tip": ("執行蝕刻模擬 (F5)", "Run the etch simulation (F5)"),
    "reset": ("重設", "Reset"),
    "reset_tip": ("清除結果並重新載入目前設定", "Clear the result"),
    "presets": ("預設配方", "Presets"),
    "preset_sio2": ("GaN / Cl2-BCl3，SiO2 光罩", "GaN / Cl2-BCl3 with SiO2 mask"),
    "preset_pr": ("GaN / Cl2-BCl3，光阻光罩", "GaN / Cl2-BCl3 with photoresist mask"),
    "open": ("開啟", "Open"), "open_tip": ("開啟專案 (JSON)", "Open project (JSON)"),
    "save": ("儲存", "Save"), "save_tip": ("儲存專案 (JSON)", "Save project (JSON)"),
    "stop": ("停止", "Stop"), "stop_tip": ("停止時間軸播放", "Stop timeline playback"),
    "compare": ("前/後比較", "Before/After"),
    "compare_tip": ("切換 蝕刻前 | 蝕刻後 並排比較", "Toggle side-by-side BEFORE | AFTER"),
    "export_png": ("匯出 PNG", "Export PNG"), "export_csv": ("匯出 CSV", "Export CSV"),
    "export_json": ("匯出 JSON", "Export JSON"),
    "export_png_tip": ("匯出圖形為 PNG", "Export figure as PNG"),
    "export_csv_tip": ("匯出剖面座標 (µm) 為 CSV", "Export profile points (µm) as CSV"),
    "export_json_tip": ("匯出專案/配方 JSON (µm)", "Export project / recipe as JSON (µm)"),
    "lang": ("English", "中文"), "lang_tip": ("切換介面語言 (Switch UI language)", "切換介面語言 (Switch UI language)"),
    "overlay": ("在蝕刻後疊加蝕刻前輪廓", "Overlay BEFORE outline on AFTER"),
    "running": ("模擬中…", "running..."), "failed": ("失敗", "failed"),
    "final_depths": ("最終深度", "final depths"),
    "sim_failed": ("模擬失敗", "Simulation failed"),
    "settings_changed": ("設定已變更，請重新模擬。", "settings changed since last run; re-run to update."),
    "rates_label": ("蝕刻率來源", "Rate sources"),
    # mask panel
    "mask_material": ("光罩材料", "Mask Material"),
    "mask_thickness": ("光罩厚度", "Mask Thickness"),
    "domain_width": ("模擬寬度", "Domain Width"),
    "mask_sel": ("預設選擇比 目標:光罩", "Preset Sel. target:mask"),
    "mask_sel_tip": ("僅在光罩材料沒有實驗值或文獻值時使用。選擇比 S = R_目標 / R_光罩",
                     "Used only when the mask material has no experimental or literature rate. S = R_target / R_mask"),
    "openings": ("開口 / 線寬 CD (µm)", "Openings / CD (µm)"),
    "hdr_center": ("中心位置\n(Center µm)", "Center (µm)"),
    "hdr_cd": ("線寬\n(CD µm)", "CD (µm)"),
    "layers": ("膜層堆疊，上 → 下（光罩下方）", "Layer stack, TOP → BOTTOM (under the mask)"),
    "hdr_material": ("材料\n(Material)", "Material"),
    "hdr_thick": ("厚度\n(Thickness µm)", "Thickness (µm)"),
    # gas / recipe
    "gas_title": ("配方步驟 #{n} — 總流量 {tot:g} sccm", "Recipe step #{n} — total {tot:g} sccm"),
    "gas_note": ("DEMO 化學只用 Cl2/BCl3 比例；實驗/文獻資料依氣體組合比對",
                 "DEMO chemistry uses Cl2/BCl3 fractions; data are matched by gas combination"),
    "hdr_gas": ("氣體\n(Gas)", "Gas"), "hdr_flow": ("流量\n(Flow sccm)", "Flow (sccm)"),
    "quick_add_tip": ("快速加入氣體 {g}", "Quick-add {g}"),
    "hdr_step": ("步驟\n(Step)", "Step"), "hdr_icp": ("ICP 功率 (W)\n(ICP Power)", "ICP Power (W)"),
    "hdr_bias": ("偏壓功率 (W)\n(RF Bias)", "RF Bias (W)"), "hdr_p": ("壓力 (mTorr)\n(Pressure)", "Pressure (mTorr)"),
    "hdr_t": ("溫度 (°C)\n(Temp)", "Temp (°C)"), "hdr_time": ("時間 (s)\n(Time)", "Time (s)"),
    "total_time": ("總時間 {t:g} s", "total {t:g} s"),
    "add_row": ("新增一列", "Add row"), "remove_row": ("刪除選取列", "Remove selected row"),
    # materials / rates
    "matlib_note": ("可新增任意材料（如 光阻1、PDMS、膠材）。離子/化學因子可留空：蝕刻率由實驗值或文獻值提供。",
                    "Add any material (e.g. resist1, PDMS, glue). Ion/chem factors may be left blank: rates then come from experimental or literature data."),
    "hdr_name": ("名稱\n(Name)", "Name"), "hdr_color": ("顏色\n(Color)", "Color"),
    "hdr_ion": ("離子因子\n(Ion Factor)", "Ion Factor"), "hdr_chem": ("化學因子\n(Chem Factor)", "Chem Factor"),
    "hdr_ismask": ("光罩\n(Mask 1/0)", "Mask (1/0)"), "hdr_note": ("備註\n(Note)", "Note"),
    "add_material": ("新增材料", "Add Material"),
    "lib_load": ("載入材料庫", "Load Library"), "lib_save": ("儲存材料庫", "Save Library"),
    "lib_tip": ("材料庫 JSON 包含材料與實驗蝕刻率/選擇比", "Library JSON = materials + experimental rates/selectivities"),
    "userrates_note": ("每列一筆實驗值，依氣體化學綁定（* = 所有配方）。若同時有實驗值與文獻值，以實驗值優先。",
                       "One experimental value per row, bound to a gas chemistry (* = any recipe). User data override literature."),
    "hdr_kind": ("類型\n(Type)", "Type"), "hdr_value": ("數值\n(Value)", "Value"), "hdr_unit": ("單位\n(Unit)", "Unit"),
    "hdr_ref": ("參考(光罩)材料\n(Reference)", "Reference (mask)"),
    "hdr_chemistry": ("氣體化學\n(Chemistry)", "Chemistry"),
    "kind_rate": ("蝕刻率", "rate"), "kind_sel": ("選擇比", "selectivity"),
    "sel_formula": ("選擇比 S = R_目標 / R_光罩　(Selectivity = target rate / mask rate)",
                    "Selectivity S = R_target / R_mask"),
    "sel_example": ("例：光阻 30 Å/s、PDMS 100 Å/s → S(PDMS:光阻) = 100 / 30 = 3.33",
                    "e.g. resist 30 Å/s, PDMS 100 Å/s → S(PDMS:resist) = 100 / 30 = 3.33"),
    "calc": ("選擇比計算", "Selectivity Calculator"),
    "calc_target": ("目標蝕刻率", "Target rate"), "calc_mask": ("光罩蝕刻率", "Mask rate"),
    "hdr_rate_um": ("蝕刻率\n(µm/min)", "Rate (µm/min)"), "hdr_rate_as": ("蝕刻率\n(Å/s)", "Rate (Å/s)"),
    "hdr_source": ("來源\n(Source)", "Source"), "hdr_detail": ("計算方式\n(Detail)", "Detail"),
    "refresh": ("更新", "Refresh"), "refresh_tip": ("依目前配方第 1 步重新解析蝕刻率來源", "Resolve rate sources for recipe step 1"),
    "show_matrix": ("選擇比矩陣", "Selectivity Matrix"),
    "matrix_note": ("列 = 目標 (被蝕刻)，欄 = 光罩；數值 = R_列 / R_欄　化學：{chem}　（列出使用中材料及有蝕刻率的材料）",
                    "Row = target, column = mask; value = R_row / R_col   chemistry: {chem}"),
    "no_warn": ("無警告", "No warnings"),
    "sources_note": ("優先順序：實驗值 > 校正 > 文獻 > 預設選擇比/示範。文獻值不隨功率/壓力變化。",
                     "Priority: experimental > calibrated > literature > preset/demo. Literature values do not follow power/pressure."),
    "use_lit": ("無實驗值時使用文獻資料庫", "Use literature DB when no experimental data"),
    # literature panel
    "lit_note": ("所有數值皆摘自所列文獻（作者、標題、年份、DOI/URL）；機台與條件與您的不同，僅供參考。預設只啟用 ICP 機台資料。",
                 "All values transcribed from the cited sources; tools/conditions differ from yours. Only ICP-tool entries are enabled by default."),
    "hdr_on": ("啟用\n(On)", "On"), "hdr_id": ("編號\n(ID)", "ID"),
    "hdr_target": ("材料/目標\n(Material)", "Material/Target"), "hdr_mask": ("光罩\n(Mask)", "Mask"),
    "hdr_gases": ("氣體\n(Gases)", "Gases"), "hdr_tool": ("機台\n(Tool)", "Tool"),
    "hdr_authors": ("作者\n(Authors)", "Authors"), "hdr_title": ("標題\n(Title)", "Title"),
    "hdr_year": ("年份\n(Year)", "Year"), "hdr_doi": ("DOI / URL", "DOI / URL"),
    "hdr_cond": ("條件\n(Conditions)", "Conditions"),
    "lit_save": ("儲存文獻庫", "Save DB"), "lit_reload": ("還原內建文獻庫", "Restore Built-in DB"),
    "lit_saved": ("已儲存：{p}", "Saved: {p}"), "lit_problems": ("資料問題：", "Problems:"),
    # settings
    "backend": ("模型引擎", "Backend"), "be_demo": ("DEMO 格點模型（示意）", "DEMO cell model (illustrative)"),
    "be_vps": ("ViennaPS 水平集", "ViennaPS level-set"), "not_installed": ("未安裝 → 改用 DEMO", "NOT INSTALLED -> falls back"),
    "grid": ("格點大小", "Grid Size"), "frames": ("儲存影格數", "Stored Frames"),
    "spread": ("離子角度分佈 (度)", "Ion Angular Spread (deg)"),
    "arde_on": ("啟用 ARDE（深寬比相依蝕刻）", "Enable ARDE (aspect-ratio-dependent etch)"),
    "arde_alpha": ("ARDE 係數 α", "ARDE alpha"), "loading_on": ("啟用巨觀負載效應", "Enable macro-loading"),
    "loading_beta": ("負載係數 β", "Loading beta"), "openfrac": ("晶圓開口面積比", "Wafer Open-Area Fraction"),
    "vps_status": ("ViennaPS 狀態", "ViennaPS status"), "available": ("可用", "available"), "unavailable": ("不可用", "unavailable"),
    # calibration
    "cal_note": ("CSV 欄位：time_s, depth_um [, cd_um]（見 examples/gan_experiment_example.csv）",
                 "CSV columns: time_s, depth_um [, cd_um] (see examples/gan_experiment_example.csv)"),
    "cal_step": ("配方步驟 #", "Recipe step #"), "cal_load": ("載入 CSV 並擬合…", "Load CSV and fit..."),
    "cal_apply": ("套用校正（結果標示為 CALIBRATED）", "Apply calibration (results become CALIBRATED)"),
    "cal_reset": ("還原 DEMO 係數", "Reset to DEMO coefficients"),
    # timeline
    "play_tip": ("播放 / 暫停 剖面演變", "Play / pause profile evolution"),
    "first_tip": ("第一影格（蝕刻前）", "First frame (before)"), "last_tip": ("最後影格（蝕刻後）", "Last frame (after)"),
    "frame": ("影格", "frame"),
    "placeholder": ("按  ▶ 開始模擬 (Run Simulation)", "Press  ▶ Run Simulation"),
    "before": ("蝕刻前 (BEFORE)", "BEFORE"), "after": ("蝕刻後 (AFTER)", "AFTER"), "depth": ("深度", "depth"),
}


def set_language(lang: str):
    global LANG
    LANG = "en" if lang == "en" else "zh"


def tr(key: str, **kw) -> str:
    zh, en = S[key]
    if LANG == "en":
        txt = en.replace(" (", "\n(") if key.startswith("hdr_") else en
    elif "\n" in zh or zh == en or key in ("lang",) or key.endswith("note") or key.endswith("_example"):
        txt = zh
    elif any(ord(c) > 0x2E80 for c in zh) and not zh.endswith(")"):
        txt = f"{zh} ({en})"
    else:
        txt = zh
    return txt.format(**kw) if kw else txt


def zh_only(key: str) -> str:
    return S[key][0]
