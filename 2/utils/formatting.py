# ...existing code...
from decimal import Decimal, InvalidOperation
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

_prefs = {
    "currency_symbol": "$",
    "currency_position": "before",
    "decimal_separator": ".",
    "thousands_separator": ",",
    "decimal_places": 2,
    "timezone": "UTC"
}

def set_preferences(prefs: dict):
    """
    Actualiza las preferencias internas a partir de dict prefs.
    """
    global _prefs
    if not isinstance(prefs, dict):
        return
    for k in list(_prefs.keys()):
        if k in prefs and prefs[k] is not None:
            _prefs[k] = prefs[k]

def format_amount(value) -> str:
    """
    Formatea un valor numérico según _prefs:
    - cantidad de decimales
    - separador decimal y de miles
    - símbolo de moneda y posición
    Devuelve string con símbolo incluido.
    """
    try:
        dec_places = int(_prefs.get("decimal_places", 2))
    except Exception:
        dec_places = 2

    try:
        d = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return str(value)

    q = Decimal(10) ** -dec_places
    try:
        d = d.quantize(q)
    except Exception:
        # fallback si falla cuantización
        pass

    fmt = f"{{:,.{dec_places}f}}"
    s = fmt.format(d)

    # prevenir colisiones al reemplazar
    s = s.replace(".", "<D>").replace(",", "<T>")
    dec_sep = _prefs.get("decimal_separator", ".") or "."
    thou_sep = _prefs.get("thousands_separator", ",") or ","
    s = s.replace("<D>", dec_sep).replace("<T>", thou_sep)

    sym = _prefs.get("currency_symbol", "") or ""
    pos = (_prefs.get("currency_position", "before") or "before").lower()
    if sym and pos == "before":
        return f"{sym}{s}"
    elif sym and pos == "after":
        return f"{s}{sym}"
    else:
        return s

def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Convierte dt a la zona horaria configurada (si zoneinfo está disponible)
    y formatea con strftime(fmt).
    """
    if not isinstance(dt, datetime):
        return str(dt)
    tzname = _prefs.get("timezone", "UTC") or "UTC"
    try:
        if ZoneInfo is not None:
            target_tz = ZoneInfo(tzname)
            if dt.tzinfo is None:
                from datetime import timezone
                dt = dt.replace(tzinfo=timezone.utc)
            dt = dt.astimezone(target_tz)
    except Exception:
        # si zoneinfo o timezone inválida, retornar dt sin conversión
        pass
    try:
        return dt.strftime(fmt)
    except Exception:
        return str(dt)
# ...existing code...