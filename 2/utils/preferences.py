import os
import json
from typing import Dict, Optional

DEFAULTS: Dict = {
    "currency_symbol": "$",
    "currency_position": "before",
    "decimal_separator": ".",
    "thousands_separator": ",",
    "decimal_places": 2,
    "timezone": "UTC",
    "appearance": "System"
}

PREFS_FILE = os.path.join("data", "preferences.json")


def load(path: Optional[str] = None) -> Dict:
    """
    Carga preferencias desde JSON y completa con DEFAULTS.
    """
    p = path or PREFS_FILE
    try:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in DEFAULTS.items():
                    data.setdefault(k, v)
                return data
    except Exception:
        pass
    return DEFAULTS.copy()


def save(prefs: Dict, path: Optional[str] = None) -> None:
    """
    Persiste prefs en disco (JSON).
    """
    p = path or PREFS_FILE
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(prefs, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def apply(prefs: Dict, persist: bool = False, path: Optional[str] = None) -> None:
    """
    Aplica las prefs al módulo utils.formatting (importado localmente para evitar import circular).
    """
    try:
        # import local para evitar import circular
        from . import formatting
        formatting.set_preferences(prefs)
    except Exception:
        pass
    if persist:
        try:
            save(prefs, path)
        except Exception:
            pass