"""Reglas heurísticas estilo Charlotte para explicar patrones detectados."""

from __future__ import annotations

from typing import Any, Mapping


def _to_mapping(row: Any) -> Mapping[str, Any]:
    if isinstance(row, Mapping):
        return row
    if hasattr(row, "to_dict"):
        try:
            return row.to_dict()
        except Exception:  # pragma: no cover - defensivo
            pass
    if hasattr(row, "items"):
        return dict(row)
    raise ValueError("No se pudo interpretar la fila de características para reglas Charlotte")


def _safe_float(data: Mapping[str, Any], key: str, fallback_keys: tuple[str, ...] = ()) -> float:
    keys = (key,) + fallback_keys
    for candidate in keys:
        try:
            value = data.get(candidate)  # type: ignore[arg-type]
        except Exception:
            value = None
        if value is None:
            continue
        try:
            return float(value)
        except Exception:
            continue
    return 0.0


def weak_label_row(row: Any) -> str:
    """Devuelve una explicación textual basada en reglas simples estilo Charlotte."""

    data = _to_mapping(row)

    pct_low = _safe_float(data, "PCT_low", ("energy_low",))
    pct_mid = _safe_float(data, "PCT_mid", ("energy_mid",))
    pct_high = _safe_float(data, "PCT_hi", ("energy_high",))
    r2x = _safe_float(data, "R_2X_1X", ("r2x",))
    r3x = _safe_float(data, "R_3X_1X", ("r3x",))
    crest = _safe_float(data, "crest")
    kurtosis = _safe_float(data, "kurt_excess")
    snr_1x = _safe_float(data, "SNR_1X_dB", ("snr_1x_db",))
    rms = _safe_float(data, "RMS_g", ("rms_vel_mm_s",))

    rationale_parts: list[str] = []

    if pct_low > 0.55 and r2x < 0.5 and r3x < 0.4:
        rationale_parts.append(
            "Energía concentrada en baja frecuencia con armónicos contenidos: indicio de desbalance"
        )
    if r2x >= 0.6 or r3x >= 0.45:
        rationale_parts.append(
            "Armónicos 2X/3X elevados respecto a 1X, compatibles con desalineación"
        )
    if pct_high >= 0.35 or crest >= 5.0 or kurtosis >= 4.0:
        rationale_parts.append(
            "Alta energía en alta frecuencia y factores estadísticos grandes: posible defecto en rodamientos"
        )
    if snr_1x >= 12.0 and pct_mid >= 0.25:
        rationale_parts.append(
            "Dominancia pronunciada de 1X con energía media: verificar solturas o resonancias"
        )
    if not rationale_parts and rms >= 7.0:
        rationale_parts.append("Nivel RMS elevado: condición severa según norma ISO")

    if not rationale_parts:
        return "Sin reglas Charlotte activas para esta muestra."

    return " | ".join(rationale_parts)
