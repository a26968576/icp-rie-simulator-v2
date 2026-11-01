"""Macro-loading effect (DEMO, empirical): etch rate drops when more wafer area is open,
because reactant (Cl) supply is shared.  factor = (1 + beta*f_ref) / (1 + beta*f_open)."""


def loading_factor(open_fraction: float, beta: float = 0.3, ref_fraction: float = 0.2) -> float:
    if not 0.0 <= open_fraction <= 1.0:
        raise ValueError("open_fraction must be within [0, 1]")
    return (1.0 + beta * ref_fraction) / (1.0 + beta * open_fraction)
