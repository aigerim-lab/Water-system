"""Plotly figure JSON with plain arrays (no binary bdata) for browser charts."""

from __future__ import annotations

import base64
import json
from typing import Any

import numpy as np
import plotly.graph_objects as go

_ARRAY_KEYS = ("x", "y", "z", "text", "lat", "lon", "locations", "values", "customdata")

_DTYPE_MAP = {
    "f8": np.float64,
    "f4": np.float32,
    "i4": np.int32,
    "i2": np.int16,
    "u1": np.uint8,
}


def _plain_array(val: Any) -> Any:
    if isinstance(val, list):
        return val
    if isinstance(val, dict) and "bdata" in val and "dtype" in val:
        dtype = _DTYPE_MAP.get(val["dtype"], np.float64)
        raw = base64.b64decode(val["bdata"])
        return np.frombuffer(raw, dtype=dtype).tolist()
    return val


def _plainify_trace(trace: dict) -> dict:
    out = dict(trace)
    for key in _ARRAY_KEYS:
        if key in out:
            out[key] = _plain_array(out[key])
    return out


def figure_to_plain_dict(fig: go.Figure) -> dict:
    """Serialize figure for React/Plotly with decodable numeric arrays."""
    payload = json.loads(fig.to_json())
    data = payload.get("data") or []
    payload["data"] = [_plainify_trace(t) for t in data]
    layout = payload.get("layout") or {}
    layout.pop("template", None)
    payload["layout"] = layout
    return payload
