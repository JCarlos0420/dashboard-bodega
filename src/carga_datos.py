"""
carga_datos.py
--------------
Paso 2 del dashboard de Bodega Nancy y Belen.

Lee del Excel del proyecto SOLO las hojas de resultados:
    - "Resultados-Indicadores"  -> As-Is, To-Be, Estandar e impacto economico
    - "SEMAFORIZACIÓN"          -> parametros del semaforo (meta y limite rojo)
    - "Flujo Caja"              -> supuestos, inversion, costos, flujo mensual,
                                   VAN, TIR, B/C y periodo de recuperacion

y los devuelve como tablas limpias de pandas (DataFrame) para usarlas en el
dashboard (app.py).

Como probarlo (desde la terminal de VS Code, con el .venv activado):
    python src/carga_datos.py
"""

from pathlib import Path

import openpyxl
import pandas as pd

# ---------------------------------------------------------------------------
# 1. CONFIGURACION
#    Si mueves tablas dentro del Excel, solo cambia estos numeros.
# ---------------------------------------------------------------------------
CARPETA_PROYECTO = Path(__file__).resolve().parent.parent
RUTA_EXCEL = CARPETA_PROYECTO / "data" / "Esquema_Proyecto_Final.xlsx"

HOJA_RESULTADOS = "Resultados-Indicadores"
HOJA_SEMAFORO = "SEMAFORIZACIÓN"
HOJA_FLUJO = "Flujo Caja"

# Resultados-Indicadores: filas 7 (ERI) a 12 (IND.5), columnas C..M
FILAS_RESULTADOS = range(7, 13)
FILA_TOTAL_RESULTADOS = 13

# SEMAFORIZACIÓN: tabla de parametros, filas 7 a 12, columnas B..F
FILAS_SEMAFORO = range(7, 13)

# Flujo Caja
FILAS_SUPUESTOS = range(7, 14)     # B7:C13
FILAS_INVERSION = range(19, 25)    # B19:C24  (B25 = total)
FILA_INVERSION_TOTAL = 25
FILAS_COSTOS = range(31, 37)       # B31:C36  (B37 = total)
FILA_COSTO_TOTAL = 37
FILA_MESES = 43                    # B43:O43  (meses 0..12)
FILAS_FLUJO = range(44, 51)        # B44:O50
FILAS_INDICADORES = range(56, 63)  # B56:C62

# Datos que no estan en la hoja de resultados: a que objetivo y herramienta
# pertenece cada indicador (tomado de O.E 1 a O.E 5 y PLANTEAMIENTO).
OBJETIVOS = {
    "ERI": ("Problema principal", "Exactitud del registro de inventarios"),
    "IND.1": ("O.E 1", "Punto de reorden (ROP) y stock de seguridad"),
    "IND.2": ("O.E 2", "Conteo cíclico de inventarios"),
    "IND.3": ("O.E 3", "Kardex digital en Excel"),
    "IND.4": ("O.E 4", "Clasificación ABC"),
    "IND.5": ("O.E 5", "5S con control visual"),
}


# ---------------------------------------------------------------------------
# 2. FUNCIONES DE APOYO
# ---------------------------------------------------------------------------
def abrir_excel(ruta: Path = RUTA_EXCEL) -> openpyxl.Workbook:
    """Abre el Excel leyendo los VALORES calculados (no las formulas)."""
    if not ruta.exists():
        raise FileNotFoundError(
            f"No encuentro el Excel en: {ruta}\n"
            "Copia tu archivo a la carpeta 'data' con el nombre "
            "'Esquema_Proyecto_Final.xlsx'."
        )
    return openpyxl.load_workbook(ruta, data_only=True)


def valor(hoja, celda: str):
    """Lee una celda. Si una formula no tiene valor guardado, avisa."""
    v = hoja[celda].value
    if v is None:
        raise ValueError(
            f"La celda {hoja.title}!{celda} esta vacia. Si tiene una formula, "
            "abre el Excel en Microsoft Excel, guardalo y vuelve a intentar."
        )
    return v


def codigo_de(nombre_indicador: str) -> str:
    """'IND.1 – % de quiebres...' -> 'IND.1'   |   'ERI – ...' -> 'ERI'"""
    return nombre_indicador.split("–")[0].split(" ")[0].strip()


# ---------------------------------------------------------------------------
# 3. RESULTADOS: AS-IS vs TO-BE vs ESTANDAR
# ---------------------------------------------------------------------------
def cargar_resultados(wb) -> pd.DataFrame:
    h = wb[HOJA_RESULTADOS]
    filas = []
    for r in FILAS_RESULTADOS:
        nombre = valor(h, f"C{r}")
        cod = codigo_de(nombre)
        objetivo, herramienta = OBJETIVOS.get(cod, ("", ""))
        filas.append({
            "codigo": cod,
            "nombre_corto": valor(h, f"M{r}"),       # p. ej. 'IND.1 Quiebres'
            "objetivo": objetivo,
            "herramienta": herramienta,
            "indicador": nombre.split("–", 1)[-1].strip(),
            "sentido": valor(h, f"L{r}"),            # 'Mayor' o 'Menor' es mejor
            "as_is": float(valor(h, f"D{r}")),
            "to_be": float(valor(h, f"F{r}")),
            "estandar": float(valor(h, f"I{r}")),
            "impacto_antes": float(valor(h, f"E{r}")),
            "impacto_despues": float(valor(h, f"G{r}")),
            "variacion_texto": valor(h, f"H{r}"),
            "tipo_dato_as_is": valor(h, f"J{r}"),
            "tipo_dato_to_be": valor(h, f"K{r}"),
        })
    df = pd.DataFrame(filas)

    # Columnas calculadas utiles para los graficos
    df["mejora_pts"] = (df["to_be"] - df["as_is"]) * 100
    df["ahorro"] = df["impacto_antes"] - df["impacto_despues"]
    df["cumple_estandar"] = df.apply(
        lambda f: f["to_be"] >= f["estandar"] if f["sentido"] == "Mayor"
        else f["to_be"] <= f["estandar"],
        axis=1,
    )
    return df


def cargar_total_resultados(wb) -> dict:
    h = wb[HOJA_RESULTADOS]
    r = FILA_TOTAL_RESULTADOS
    antes = float(valor(h, f"E{r}"))
    despues = float(valor(h, f"G{r}"))
    return {
        "impacto_antes": antes,
        "impacto_despues": despues,
        "ahorro": antes - despues,
        "variacion_texto": valor(h, f"H{r}"),
    }


# ---------------------------------------------------------------------------
# 4. PARAMETROS DEL SEMAFORO
# ---------------------------------------------------------------------------
def cargar_parametros_semaforo(wb) -> pd.DataFrame:
    h = wb[HOJA_SEMAFORO]
    filas = []
    for r in FILAS_SEMAFORO:
        filas.append({
            "nombre_corto": valor(h, f"B{r}"),
            "sentido": valor(h, f"C{r}"),
            "linea_base": float(valor(h, f"D{r}")),
            "meta": float(valor(h, f"E{r}")),
            "limite_rojo": float(valor(h, f"F{r}")),
        })
    return pd.DataFrame(filas)


# ---------------------------------------------------------------------------
# 5. FLUJO DE CAJA
# ---------------------------------------------------------------------------
def _tabla_concepto_monto(h, filas, col_monto="C", col_fuente="E"):
    datos = []
    for r in filas:
        datos.append({
            "concepto": valor(h, f"B{r}"),
            "monto": h[f"{col_monto}{r}"].value,
            "fuente": h[f"{col_fuente}{r}"].value or "",
        })
    return pd.DataFrame(datos)


def cargar_flujo_caja(wb) -> dict:
    h = wb[HOJA_FLUJO]

    supuestos = _tabla_concepto_monto(h, FILAS_SUPUESTOS)
    inversion = _tabla_concepto_monto(h, FILAS_INVERSION)
    costos = _tabla_concepto_monto(h, FILAS_COSTOS)

    # Flujo mensual: columnas C (mes 0) a O (mes 12)
    columnas = [openpyxl.utils.get_column_letter(c) for c in range(3, 16)]
    meses = [int(valor(h, f"{c}{FILA_MESES}")) for c in columnas]
    nombres = {
        44: "ahorro",
        45: "costos_operativos",
        46: "inversion",
        47: "flujo_neto",
        48: "flujo_acumulado",
        49: "flujo_descontado",
        50: "descontado_acumulado",
    }
    flujo = pd.DataFrame({"mes": meses})
    for r in FILAS_FLUJO:
        flujo[nombres[r]] = [float(valor(h, f"{c}{r}")) for c in columnas]

    # Indicadores economicos (VAN, TIR, B/C, recuperacion...)
    ind = {valor(h, f"B{r}"): valor(h, f"C{r}") for r in FILAS_INDICADORES}
    indicadores = {
        "van": float(ind["VAN (valor actual neto)"]),
        "tir_mensual": float(ind["TIR mensual"]),
        "bc": float(ind["Relación beneficio / costo (B/C)"]),
        "recuperacion_mes": int(ind["Periodo de recuperación (mes)"]),
        "beneficio_neto_anio1": float(ind["Beneficio neto del año 1 (sin descontar)"]),
        "decision": ind["DECISIÓN"],
        "cok_anual": float(valor(h, "C7")),
        "cok_mensual": float(valor(h, "C8")),
        "inversion_total": float(valor(h, f"C{FILA_INVERSION_TOTAL}")),
        "costo_operativo_anual": float(valor(h, f"C{FILA_COSTO_TOTAL}")),
    }

    return {
        "supuestos": supuestos,
        "inversion": inversion,
        "costos": costos,
        "flujo": flujo,
        "indicadores": indicadores,
    }


# ---------------------------------------------------------------------------
# 6. FUNCION PRINCIPAL: carga todo de una sola vez
# ---------------------------------------------------------------------------
def cargar_todo(ruta: Path = RUTA_EXCEL) -> dict:
    wb = abrir_excel(ruta)
    resultados = cargar_resultados(wb)
    semaforo = cargar_parametros_semaforo(wb)

    # Une los limites del semaforo a cada indicador (por su nombre corto)
    resultados = resultados.merge(
        semaforo[["nombre_corto", "meta", "limite_rojo"]],
        on="nombre_corto",
        how="left",
    )
    return {
        "resultados": resultados,
        "total": cargar_total_resultados(wb),
        "semaforo_parametros": semaforo,
        "flujo_caja": cargar_flujo_caja(wb),
    }


# ---------------------------------------------------------------------------
# 7. PRUEBA RAPIDA: python src/carga_datos.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    pd.set_option("display.width", 160)
    pd.set_option("display.max_columns", 20)

    datos = cargar_todo()

    print("\n=== RESULTADOS (As-Is / To-Be / Estandar) ===")
    print(datos["resultados"][
        ["codigo", "objetivo", "sentido", "as_is", "to_be",
         "estandar", "limite_rojo", "cumple_estandar", "ahorro"]
    ].round(3).to_string(index=False))

    t = datos["total"]
    print(f"\nImpacto total: S/ {t['impacto_antes']:,.2f} -> "
          f"S/ {t['impacto_despues']:,.2f}  (ahorro S/ {t['ahorro']:,.2f})")

    fc = datos["flujo_caja"]
    print("\n=== FLUJO DE CAJA (S/) ===")
    print(fc["flujo"][["mes", "ahorro", "costos_operativos", "inversion",
                       "flujo_neto", "descontado_acumulado"]]
          .round(2).to_string(index=False))

    i = fc["indicadores"]
    print("\n=== INDICADORES ECONOMICOS ===")
    print(f"VAN: S/ {i['van']:,.2f} | TIR mensual: {i['tir_mensual']:.1%} | "
          f"B/C: {i['bc']:.2f} | Recuperacion: mes {i['recuperacion_mes']}")
    print(f"Inversion: S/ {i['inversion_total']:,.2f} | "
          f"Costo operativo anual: S/ {i['costo_operativo_anual']:,.2f}")
    print(f"Decision: {i['decision']}")
    print("\nOK: datos cargados correctamente.")
