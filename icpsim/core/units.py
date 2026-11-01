"""Unit helpers. Internal geometry is stored in nm; everything user-facing is micrometers (um)."""
NM_PER_UM = 1000.0


def nm_to_um(v):
    return v / NM_PER_UM


def um_to_nm(v):
    return v * NM_PER_UM


def rate_nm_s_to_um_min(v):
    return v * 60.0 / NM_PER_UM


def fmt_um(v_nm, dec=3):
    return f"{v_nm / NM_PER_UM:.{dec}f} um"
