"""Model provenance labels. Every result carries one of these so that DEMO
(empirical, uncalibrated, illustrative) numbers are never mistaken for
physically validated predictions."""

DEMO = "DEMO"
CALIBRATED = "CALIBRATED"
VIENNAPS_UNCAL = "VIENNAPS_UNCALIBRATED"
VIENNAPS_CAL = "VIENNAPS_CALIBRATED"

TEXT = {
    DEMO: "DEMO MODEL - empirical, UNCALIBRATED, illustrative only. Not physical truth.",
    CALIBRATED: "CALIBRATED - demo profile model with rate coefficients fitted to user experimental data "
                "(valid only near the calibrated recipe window).",
    VIENNAPS_UNCAL: "VIENNAPS level-set engine - geometry physics-based, but etch RATES are UNCALIBRATED demo "
                    "coefficients. Illustrative only.",
    VIENNAPS_CAL: "VIENNAPS level-set engine + CALIBRATED rate coefficients from user experimental data.",
}

COLOR = {DEMO: "#c62828", CALIBRATED: "#2e7d32", VIENNAPS_UNCAL: "#ef6c00", VIENNAPS_CAL: "#1565c0"}


def label_for(backend: str, calibrated: bool) -> str:
    if backend == "viennaps":
        return VIENNAPS_CAL if calibrated else VIENNAPS_UNCAL
    return CALIBRATED if calibrated else DEMO


def is_calibrated(label: str) -> bool:
    return label in (CALIBRATED, VIENNAPS_CAL)
