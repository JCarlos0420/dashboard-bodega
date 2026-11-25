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

# IMPORTANTE: las tablas se BUSCAN por su texto (columna B o C), no por un
# numero de fila fijo. Asi el codigo sigue funcionando aunque agregues o
# quites filas en el Excel. Solo no cambies estos textos:
TXT_ERI = "ERI"                                   # Resultados-Indicadores, col. C
TXT_SUPUESTOS_INI = "Tasa de descuento anual (COK)"
TXT_SUPUESTOS_FIN = "Días de atención al año"
TXT_INVERSION_INI = "2. Inversión inicial"
TXT_INVERSION_TOTAL = "INVERSIÓN TOTAL"
TXT_COSTOS_INI = "3. Costos operativos"
TXT_COSTO_TOTAL = "COSTO OPERATIVO TOTAL ANUAL"
TXT_MESES = "Concepto / Mes"
TXT_RESUMEN_SEMAFORO = "Resumen del semáforo"

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


def buscar_fila(hoja, texto: str, columna: str = "B", desde: int = 1) -> int:
    """Devuelve la primera fila (desde 'desde') cuya celda empieza con 'texto'."""
    for r in range(desde, hoja.max_row + 1):
        v = hoja[f"{columna}{r}"].value
        if isinstance(v, str) and v.strip().startswith(texto):
            return r
    raise ValueError(
        f"No encontre el texto '{texto}' en la columna {columna} de la hoja "
        f"'{hoja.title}'. Revisa que ese titulo siga escrito igual en el Excel."
    )


def codigo_de(nombre_indicador: str) -> str:
    """'IND.1 – % de quiebres...' -> 'IND.1'   |   'ERI – ...' -> 'ERI'"""
    return nombre_indicador.split("–")[0].split(" ")[0].strip()


# ---------------------------------------------------------------------------
# 3. RESULTADOS: AS-IS vs TO-BE vs ESTANDAR
# ---------------------------------------------------------------------------
def cargar_resultados(wb) -> pd.DataFrame:
    h = wb[HOJA_RESULTADOS]
    fila_eri = buscar_fila(h, TXT_ERI, columna="C")
    filas = []
    for r in range(fila_eri, fila_eri + 6):          # ERI + IND.1 ... IND.5
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
    r = buscar_fila(h, TXT_ERI, columna="C") + 6     # fila "Total de la propuesta"
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
    fila_eri = buscar_fila(h, "ERI")
    filas = []
    for r in range(fila_eri, fila_eri + 6):
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
    """Lee concepto / monto / fuente. Ignora las filas vacias."""
    datos = []
    for r in filas:
        concepto = h[f"B{r}"].value
        if concepto is None or str(concepto).strip() == "":
            continue                       # fila vacia: se salta
        datos.append({
            "concepto": str(concepto).strip(),
            "monto": h[f"{col_monto}{r}"].value,
            "fuente": h[f"{col_fuente}{r}"].value or "",
        })
    return pd.DataFrame(datos)


def _inicio_tabla(h, texto_seccion: str) -> int:
    """Primera fila de datos: la que sigue al encabezado 'Concepto' de la seccion."""
    sec = buscar_fila(h, texto_seccion)
    return buscar_fila(h, "Concepto", desde=sec) + 1


def cargar_flujo_caja(wb) -> dict:
    h = wb[HOJA_FLUJO]

    # Supuestos: desde "Tasa de descuento anual" hasta "Dias de atencion"
    r1 = buscar_fila(h, TXT_SUPUESTOS_INI)
    r2 = buscar_fila(h, TXT_SUPUESTOS_FIN, desde=r1)   # tabla de la seccion 1
    supuestos = _tabla_concepto_monto(h, range(r1, r2 + 1))

    # Inversion: filas entre el encabezado de la seccion 2 y "INVERSION TOTAL"
    ini = _inicio_tabla(h, TXT_INVERSION_INI)
    fila_inv_total = buscar_fila(h, TXT_INVERSION_TOTAL, desde=ini)
    inversion = _tabla_concepto_monto(h, range(ini, fila_inv_total))

    # Costos operativos: entre la seccion 3 y "COSTO OPERATIVO TOTAL ANUAL"
    ini = _inicio_tabla(h, TXT_COSTOS_INI)
    fila_costo_total = buscar_fila(h, TXT_COSTO_TOTAL, desde=ini)
    costos = _tabla_concepto_monto(h, range(ini, fila_costo_total))

    # Los montos de inversion y costos deben ser numeros (texto o vacio -> 0)
    for tabla in (inversion, costos):
        tabla["monto"] = pd.to_numeric(tabla["monto"], errors="coerce").fillna(0.0)

    # Flujo mensual: fila "Concepto / Mes" y las 7 filas siguientes
    fila_meses = buscar_fila(h, TXT_MESES)
    columnas = [openpyxl.utils.get_column_letter(c) for c in range(3, 16)]  # C..O
    meses = [int(valor(h, f"{c}{fila_meses}")) for c in columnas]
    nombres = [
        "ahorro",
        "costos_operativos",
        "inversion",
        "flujo_neto",
        "flujo_acumulado",
        "flujo_descontado",
        "descontado_acumulado",
    ]
    flujo = pd.DataFrame({"mes": meses})
    for i, nombre in enumerate(nombres, start=1):
        flujo[nombre] = [float(valor(h, f"{c}{fila_meses + i}")) for c in columnas]

    # Indicadores economicos: se buscan por su nombre en la columna B
    def ind(texto):
        return valor(h, f"C{buscar_fila(h, texto)}")

    indicadores = {
        "van": float(ind("VAN (valor actual neto)")),
        "tir_mensual": float(ind("TIR mensual")),
        "bc": float(ind("Relación beneficio / costo (B/C)")),
        "recuperacion_mes": int(ind("Periodo de recuperación (mes)")),
        "beneficio_neto_anio1": float(ind("Beneficio neto del año 1")),
        "decision": ind("DECISIÓN"),
        "cok_anual": float(ind(TXT_SUPUESTOS_INI)),
        "cok_mensual": float(ind("Tasa de descuento mensual")),
        "inversion_total": float(valor(h, f"C{fila_inv_total}")),
        "costo_operativo_anual": float(valor(h, f"C{fila_costo_total}")),
    }

    return {
        "supuestos": supuestos,
        "inversion": inversion,
        "costos": costos,
        "flujo": flujo,
        "indicadores": indicadores,
    }


def cargar_resumen_semaforo_excel(wb) -> dict:
    """Lee el 'Resumen del semaforo' de la hoja (Verde/Amarillo/Rojo)."""
    h = wb[HOJA_SEMAFORO]
    r = buscar_fila(h, TXT_RESUMEN_SEMAFORO)
    resumen = {}
    for fila in range(r + 1, r + 6):
        color = h[f"B{fila}"].value
        if color in ("Verde", "Amarillo", "Rojo"):
            resumen[color] = (int(h[f"D{fila}"].value or 0), int(h[f"E{fila}"].value or 0))
    return resumen


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
        "semaforo_resumen_excel": cargar_resumen_semaforo_excel(wb),
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
