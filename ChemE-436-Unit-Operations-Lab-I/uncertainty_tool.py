
"""
uncertainty_tool.py
General-purpose uncertainty propagation with SymPy.
Usage:
    from uncertainty_tool import propagate, variables
    vars = variables({
        "m": (5.0, 0.005),       # value, standard uncertainty
        "t": (10.0, 0.02),
        "rho": (998.2, 0.5),
    })
    res = propagate("Q = (m/rho)/t", vars, k=2.0)
    print(res["Q"]["value"], res["Q"]["u_c"], res["Q"]["U"])
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple, Optional
import sympy as sp
import numpy as np

@dataclass
class Var:
    name: str
    value: float
    u: float

def variables(d: Dict[str, Tuple[float, float]]):
    return {k: Var(k, float(v[0]), float(v[1])) for k, v in d.items()}

def propagate(model: str, varmap: Dict[str, Var], k: float = 2.0, corr: Optional[np.ndarray] = None):
    """
    model: either 'Y = expression' or just 'expression' (result will be named 'Y' if not provided).
    varmap: dict of Var objects with .value and .u
    k: coverage factor for expanded uncertainty
    corr: optional correlation matrix (NxN, order must match sorted(varmap.keys()))
    Returns: dict of {result_name: {"value": float, "u_c": float, "U": float, "partials": dict}}
    """
    # Parse model
    if "=" in model:
        name, expr_str = [s.strip() for s in model.split("=", 1)]
        result_name = name
    else:
        expr_str = model.strip()
        result_name = "Y"
    # Build sympy symbols
    syms = {n: sp.Symbol(n) for n in varmap.keys()}
    expr = sp.sympify(expr_str, locals=syms)
    # Substitute values
    subs = {syms[n]: varmap[n].value for n in varmap}
    value = float(expr.evalf(subs=subs))
    # Partials
    partials = {n: sp.diff(expr, syms[n]) for n in varmap}
    partial_vals = {n: float(partials[n].evalf(subs=subs)) for n in varmap}
    # Combined uncertainty (with optional correlation)
    names = list(sorted(varmap.keys()))
    # Build gradient vector in sorted order
    grad = np.array([partial_vals[n] for n in names], dtype=float)
    u_vec = np.array([varmap[n].u for n in names], dtype=float)
    if corr is None:
        # uncorrelated
        uc2 = np.sum((grad * u_vec) ** 2)
    else:
        # with correlation matrix
        C = np.outer(u_vec, u_vec) * corr
        uc2 = grad @ C @ grad
    u_c = float(np.sqrt(uc2))
    U = k * u_c
    return {
        result_name: {
            "value": value,
            "u_c": u_c,
            "U": U,
            "partials": partial_vals,
        }
    }

if __name__ == "__main__":
    # Demo: Q and H for a pump test
    vs = variables({
        "m_bucket": (5.0, 0.005),
        "delta_t" : (10.0, 0.02),
        "rho"     : (998.2, 0.5),
        "g"       : (9.80665, 0.0),
        "P_suction": (101325.0, 300.0),
        "P_discharge": (150000.0, 300.0),
        "z"       : (0.50, 0.005),
        "D_pipe"  : (0.026, 0.0005),
    })
    out = {}
    out.update(propagate("Q = (m_bucket/rho)/delta_t", vs, k=2.0))
    Q = out["Q"]["value"]
    vs["Q"] = Var("Q", Q, out["Q"]["u_c"])
    out.update(propagate("v = 4*Q/(pi*D_pipe**2)", vs, k=2.0))
    v = out["v"]["value"]
    vs["v"] = Var("v", v, out["v"]["u_c"])
    out.update(propagate("delta_p = P_discharge - P_suction", vs, k=2.0))
    out.update(propagate("H = delta_p/(rho*g) + v**2/(2*g) + z", vs, k=2.0))
    out.update(propagate("P_h = rho*g*Q*H", vs, k=2.0))
    for kname, res in out.items():
        print(f"{kname:7s} = {res['value']:.6g}  u_c={res['u_c']:.3g}  U(k=2)={res['U']:.3g}")
