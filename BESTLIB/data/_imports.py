"""
Helpers para importaciones opcionales compartidas (pandas, numpy).
"""
from __future__ import annotations

HAS_PANDAS = False
HAS_NUMPY = False
pd = None
np = None


def ensure_pandas():
    """Carga pandas una sola vez de forma segura."""
    global pd, HAS_PANDAS
    if pd is not None:
        return pd
    try:
        import pandas as _pd  # type: ignore
    except Exception:
        HAS_PANDAS = False
        pd = None
        return None
    HAS_PANDAS = True
    pd = _pd
    return pd


def ensure_numpy():
    """Carga numpy una sola vez de forma segura."""
    global np, HAS_NUMPY
    if np is not None:
        return np
    try:
        import numpy as _np  # type: ignore
    except Exception:
        HAS_NUMPY = False
        np = None
        return None
    HAS_NUMPY = True
    np = _np
    return np

