"""Model provenance labels. Every result carries one of these so that DEMO
(empirical, uncalibrated, illustrative) numbers are never mistaken for
physically validated predictions, and so that the origin of the etch RATES
(user experimental input / literature / demo) is always visible."""
from __future__ import annotations


DEMO = "DEMO"
CALIBRATED = "CALIBRATED"
EXPERIMENTAL = "EXPERIMENTAL_INPUT"
LITERATURE = "LITERATURE_BASED"
VIENNAPS_UNCAL = "VIENNAPS_UNCALIBRATED"
VIENNAPS_CAL = "VIENNAPS_CALIBRATED"
VIENNAPS_EXP = "VIENNAPS_EXPERIMENTAL_INPUT"
VIENNAPS_LIT = "VIENNAPS_LITERATURE_BASED"

TEXT = {
    DEMO: "DEMO 示範模型 - 經驗式、未校正，僅供示意 (DEMO MODEL - empirical, UNCALIBRATED, illustrative only. Not physical truth.)",
    CALIBRATED: "CALIBRATED 已校正 - 蝕刻率係數以使用者實驗數據擬合，僅在校正配方附近有效 "
                "(rate coefficients fitted to user experimental data; valid only near the calibrated recipe window).",
    EXPERIMENTAL: "EXPERIMENTAL INPUT 實驗輸入 - 蝕刻率來自使用者實驗值/選擇比；剖面形狀仍為示範模型 "
                  "(rates from user experimental input; profile shape model is still DEMO).",
    LITERATURE: "LITERATURE-BASED 文獻值 - 部分蝕刻率取自文獻（機台與條件不同），僅供參考 "
                "(some rates from literature; tool/conditions differ - rough guide only).",
    VIENNAPS_UNCAL: "VIENNAPS 水平集引擎 - 幾何為物理方法，但蝕刻率為未校正示範係數 "
                    "(VIENNAPS level-set geometry, UNCALIBRATED demo rates. Illustrative only.)",
    VIENNAPS_CAL: "VIENNAPS 水平集引擎 + 已校正蝕刻率 (VIENNAPS + CALIBRATED rate coefficients from user data).",
    VIENNAPS_EXP: "VIENNAPS 水平集引擎 + 實驗輸入蝕刻率 (VIENNAPS + rates from user EXPERIMENTAL input).",
    VIENNAPS_LIT: "VIENNAPS 水平集引擎 + 文獻蝕刻率（條件不同，僅供參考） (VIENNAPS + LITERATURE-based rates, rough guide).",
}

COLOR = {DEMO: "#c62828", CALIBRATED: "#2e7d32", EXPERIMENTAL: "#2e7d32", LITERATURE: "#6a1b9a",
         VIENNAPS_UNCAL: "#ef6c00", VIENNAPS_CAL: "#1565c0", VIENNAPS_EXP: "#1565c0", VIENNAPS_LIT: "#6a1b9a"}

SOURCE_ZH = {"experimental": "實驗值 (experimental)", "calibrated": "校正 (calibrated)",
             "literature": "文獻 (literature)", "preset": "預設選擇比 (preset)", "demo": "示範 (demo)",
             "none": "無資料 (no data)"}


def label_for(backend: str, calibrated: bool, provenance: dict | None = None) -> str:
    """provenance: {material: source} of the materials actually used (rate_sources categories)."""
    vp = backend == "viennaps"
    cats = set((provenance or {}).values())
    if provenance is None or cats & {"demo", "none"}:
        if vp:
            return VIENNAPS_CAL if calibrated else VIENNAPS_UNCAL
        return CALIBRATED if calibrated else DEMO
    if "literature" in cats:
        return VIENNAPS_LIT if vp else LITERATURE
    if "experimental" in cats:
        return VIENNAPS_EXP if vp else EXPERIMENTAL
    return VIENNAPS_CAL if vp else CALIBRATED     # calibrated (+ preset mask)


def is_calibrated(label: str) -> bool:
    return label in (CALIBRATED, VIENNAPS_CAL, EXPERIMENTAL, VIENNAPS_EXP)


def provenance_text(prov: dict) -> str:
    return "，".join(f"{k}={SOURCE_ZH.get(v, v).split(' ')[0]}" for k, v in prov.items())


def text(label: str) -> str:
    """Label description in the current UI language (zh: bilingual, en: English part only)."""
    from .. import i18n
    t = TEXT[label]
    if i18n.LANG == "en" and "(" in t:
        head = t.split(" ")[0]
        return head + " - " + t[t.index("(") + 1:t.rindex(")")]
    return t


def provenance_text_lang(prov: dict) -> str:
    from .. import i18n
    if i18n.LANG == "en":
        return ", ".join(f"{k}={v}" for k, v in prov.items())
    return provenance_text(prov)
