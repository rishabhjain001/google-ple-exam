"""
Physical Engineering Calculation Library
=========================================
Standard formulations for Structural, Civil, Electrical, and Mechanical tasks.
"""

import math
from typing import NamedTuple


# ---------------------------------------------------------------------------
# 1. Structural Engineering (ASCE 7 / AISC / ACI)
# ---------------------------------------------------------------------------

def beam_simply_supported_udl(w_plf: float, L_ft: float) -> dict[str, float]:
    """
    Simply supported beam under uniform distributed load (UDL).
    w: load in pounds per linear foot (plf)
    L: span in feet
    """
    V_max_lb = (w_plf * L_ft) / 2.0
    M_max_lb_ft = (w_plf * (L_ft ** 2)) / 8.0
    return {
        "V_max_kips": round(V_max_lb / 1000.0, 3),
        "M_max_kip_ft": round(M_max_lb_ft / 1000.0, 3),
    }


def dcr(demand: float, capacity: float) -> float:
    """Demand to capacity ratio (DCR). Code compliant if <= 1.00."""
    if capacity <= 0:
        return float("inf")
    return round(demand / capacity, 3)


# ---------------------------------------------------------------------------
# 2. Civil / Hydrology (Rational Method)
# ---------------------------------------------------------------------------

def rational_method_peak_flow(C: float, I_in_hr: float, A_acres: float) -> float:
    """
    Q = C * I * A (peak runoff in cubic feet per second, cfs)
    C: Runoff coefficient (0.0 to 1.0)
    I: Rainfall intensity (in/hr)
    A: Drainage area (acres)
    """
    return round(C * I_in_hr * A_acres, 3)


def manning_pipe_flow(n: float, D_ft: float, S_ft_per_ft: float) -> float:
    """
    Manning's equation for full circular gravity pipe flow (cfs).
    n: Manning roughness
    D: Diameter in feet
    S: Slope (ft/ft)
    """
    A = math.pi * (D_ft ** 2) / 4.0
    R = D_ft / 4.0
    Q = (1.486 / n) * A * (R ** (2.0 / 3.0)) * (S_ft_per_ft ** 0.5)
    return round(Q, 3)


# ---------------------------------------------------------------------------
# 3. Electrical (NEC NFPA 70)
# ---------------------------------------------------------------------------

def voltage_drop_single_phase(I_amps: float, R_ohms_per_kft: float, L_ft: float, V_source: float) -> dict[str, float]:
    """
    Single-phase 2-wire AC/DC voltage drop: VD = 2 * I * R * L / 1000
    """
    vd = (2.0 * I_amps * R_ohms_per_kft * L_ft) / 1000.0
    pct = (vd / V_source) * 100.0
    return {
        "voltage_drop_V": round(vd, 2),
        "percentage": round(pct, 2),
        "compliant_3pct": pct <= 3.0,
    }


def transformer_full_load_amps_3ph(kVA: float, V_line: float) -> float:
    """3-Phase Full Load Amperes (FLA): kVA * 1000 / (sqrt(3) * V_line)."""
    return round((kVA * 1000.0) / (math.sqrt(3) * V_line), 2)
