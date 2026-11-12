"""
semaforo.py
-----------
Paso 3 del dashboard de Bodega Nancy y Belen.

Asigna Verde / Amarillo / Rojo a cada indicador, en el As-Is (antes) y en el
To-Be (despues), con las MISMAS reglas de la hoja "SEMAFORIZACIÓN":

  Sentido "Mayor" (mas alto es mejor):  ERI, IND.2, IND.3, IND.4
      Verde    : valor >= meta
      Amarillo : limite_rojo <= valor < meta
      Rojo     : valor < limite_rojo

  Sentido "Menor" (mas bajo es mejor):  IND.1, IND.5
      Verde    : valor <= meta
      Amarillo : meta < valor <= limite_rojo
      Rojo     : valor > limite_rojo

Como probarlo:
    python src/semaforo.py
"""

import pandas as pd

# Colores para los graficos del dashboard (texto, color de fondo suave, color fuerte)
COLORES = {
    "Verde":    {"fuerte": "#0ca30c", "suave": "#e3f5e3", "icono": "🟢"},
    "Amarillo": {"fuerte": "#fab219", "suave": "#fff4d6", "icono": "🟡"},
    "Rojo":     {"fuerte": "#d03b3b", "suave": "#fbe3e3", "icono": "🔴"},
}

# Mensajes de interpretacion (los mismos de tu hoja SEMAFORIZACIÓN)
INTERPRETACION = {
    "Verde": "Cumple: alcanza o supera la meta.",
    "Amarillo": "En riesgo: cerca de la meta. Seguimiento.",
    "Rojo": "Crítico: lejos de la meta. Acción inmediata.",
}

ORDEN = ["Verde", "Amarillo", "Rojo"]

# Margen pequeño para evitar errores de redondeo (p. ej. 0.95 vs 0.9500000001)
TOLERANCIA = 1e-9


def clasificar(valor: float, sentido: str, meta: float, limite_rojo: float) -> str:
    """Devuelve 'Verde', 'Amarillo' o 'Rojo' para un valor."""
    if sentido == "Mayor":
        if valor >= meta - TOLERANCIA:
            return "Verde"
        if valor >= limite_rojo - TOLERANCIA:
            return "Amarillo"
        return "Rojo"

    if sentido == "Menor":
        if valor <= meta + TOLERANCIA:
            return "Verde"
        if valor <= limite_rojo + TOLERANCIA:
            return "Amarillo"
        return "Rojo"

    raise ValueError(f"Sentido desconocido: {sentido!r} (debe ser 'Mayor' o 'Menor')")


def brecha_a_meta(valor: float, sentido: str, meta: float) -> float:
    """
    Puntos porcentuales que faltan para llegar a la meta.
    0 = ya cumple. Siempre positivo o cero.
    """
    if sentido == "Mayor":
        falta = meta - valor
    else:
        falta = valor - meta
    return max(falta, 0.0) * 100


def aplicar_semaforo(resultados: pd.DataFrame) -> pd.DataFrame:
    """
    Recibe la tabla 'resultados' de carga_datos.cargar_todo() y le agrega:
        semaforo_as_is, semaforo_to_be, brecha_as_is_pts, brecha_to_be_pts,
        interpretacion_to_be
    """
    df = resultados.copy()
    for momento in ["as_is", "to_be"]:
        df[f"semaforo_{momento}"] = df.apply(
            lambda f: clasificar(f[momento], f["sentido"], f["meta"], f["limite_rojo"]),
            axis=1,
        )
        df[f"brecha_{momento}_pts"] = df.apply(
            lambda f: brecha_a_meta(f[momento], f["sentido"], f["meta"]),
            axis=1,
        )
    df["interpretacion_to_be"] = df["semaforo_to_be"].map(INTERPRETACION)
    return df


def resumen_semaforo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cuenta cuantos indicadores hay en cada color, antes y despues.
    Equivale al 'Resumen del semáforo' de tu hoja (B29:E32).
    """
    resumen = pd.DataFrame({
        "color": ORDEN,
        "as_is": [int((df["semaforo_as_is"] == c).sum()) for c in ORDEN],
        "to_be": [int((df["semaforo_to_be"] == c).sum()) for c in ORDEN],
    })
    return resumen


# ---------------------------------------------------------------------------
# PRUEBA RAPIDA: python src/semaforo.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from carga_datos import cargar_todo

    pd.set_option("display.width", 160)

    datos = cargar_todo()
    df = aplicar_semaforo(datos["resultados"])

    print("\n=== SEMAFORO POR INDICADOR ===")
    for _, f in df.iterrows():
        print(
            f"{f['nombre_corto']:<22} "
            f"As-Is {f['as_is']*100:6.1f}% {COLORES[f['semaforo_as_is']]['icono']} {f['semaforo_as_is']:<8} -> "
            f"To-Be {f['to_be']*100:6.1f}% {COLORES[f['semaforo_to_be']]['icono']} {f['semaforo_to_be']:<8} "
            f"(meta {f['meta']*100:.0f}%, faltan {f['brecha_to_be_pts']:.1f} pts)"
        )

    print("\n=== RESUMEN DEL SEMAFORO ===")
    print(resumen_semaforo(df).to_string(index=False))

    # Control: debe coincidir con tu hoja SEMAFORIZACIÓN (As-Is 0/0/6, To-Be 4/1/1)
    r = resumen_semaforo(df)
    esperado_as_is, esperado_to_be = [0, 0, 6], [4, 1, 1]
    if r["as_is"].tolist() == esperado_as_is and r["to_be"].tolist() == esperado_to_be:
        print("\nOK: el semaforo coincide con la hoja SEMAFORIZACIÓN del Excel.")
    else:
        print("\nATENCION: el resultado no coincide con la hoja del Excel. Revisa metas y limites.")
