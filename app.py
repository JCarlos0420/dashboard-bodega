"""
app.py
------
Dashboard de Bodega Nancy y Belen.

Pagina 1: RESUMEN (tarjetas KPI)                    -> Paso 4
Pagina 2: AS-IS vs TO-BE vs ESTANDAR (graficos)      -> Paso 5
Pagina 3: SEMAFORIZACION                             -> Paso 6
Pagina 4: FLUJO DE CAJA (VAN, TIR, B/C)              -> Paso 7

Como ejecutarlo (desde la carpeta dashboard_bodega, con el .venv activo):
    streamlit run app.py
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Permite importar los modulos que estan dentro de la carpeta src/
sys.path.append(str(Path(__file__).resolve().parent / "src"))

from carga_datos import cargar_todo  # noqa: E402
from semaforo import COLORES, aplicar_semaforo, resumen_semaforo  # noqa: E402
from graficos import (  # noqa: E402
    grafico_conteo_semaforo,
    grafico_costos,
    grafico_flujo,
    grafico_impacto,
    grafico_indicador,
    grafico_semaforo,
)
from semaforo import INTERPRETACION  # noqa: E402


# ---------------------------------------------------------------------------
# 1. CONFIGURACION DE LA PAGINA
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard – Bodega Nancy y Belén",
    page_icon="📊",
    layout="wide",
)


# ---------------------------------------------------------------------------
# 2. CARGA DE DATOS (se guarda en cache para que el dashboard sea rapido)
# ---------------------------------------------------------------------------
@st.cache_data
def obtener_datos():
    datos = cargar_todo()
    datos["resultados"] = aplicar_semaforo(datos["resultados"])
    return datos


# ---------------------------------------------------------------------------
# 3. FUNCIONES DE FORMATO
# ---------------------------------------------------------------------------
def pct(x: float, decimales: int = 1) -> str:
    return f"{x * 100:.{decimales}f} %"


def soles(x: float) -> str:
    signo = "-" if x < 0 else ""
    return f"{signo}S/ {abs(x):,.2f}"


def etiqueta_semaforo(color: str) -> str:
    return f"{COLORES[color]['icono']} {color}"


# ---------------------------------------------------------------------------
# 4. PAGINA 1: RESUMEN
# ---------------------------------------------------------------------------
def pagina_resumen(datos: dict) -> None:
    res = datos["resultados"]
    eco = datos["flujo_caja"]["indicadores"]
    total = datos["total"]
    eri = res[res["codigo"] == "ERI"].iloc[0]

    st.subheader("Problema principal: exactitud del registro de inventarios (ERI)")

    c1, c2, c3 = st.columns(3)
    with c1:
        with st.container(border=True):
            st.metric("ERI antes (As-Is)", pct(eri["as_is"]))
            st.caption(f"{etiqueta_semaforo(eri['semaforo_as_is'])} · {eri['tipo_dato_as_is']}")
    with c2:
        with st.container(border=True):
            st.metric(
                "ERI después (To-Be)",
                pct(eri["to_be"]),
                delta=f"{eri['mejora_pts']:+.1f} pts",
            )
            st.caption(f"{etiqueta_semaforo(eri['semaforo_to_be'])} · {eri['tipo_dato_to_be']}")
    with c3:
        with st.container(border=True):
            st.metric("Estándar (meta)", pct(eri["estandar"], 0))
            st.caption("Referencia: Brooks y Wilson (2012)")

    st.subheader("Evaluación económica de la propuesta (12 meses)")

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        with st.container(border=True):
            st.metric("VAN", soles(eco["van"]))
            st.caption("Viable si VAN > 0")
    with k2:
        with st.container(border=True):
            st.metric("Beneficio / Costo", f"{eco['bc']:.2f}")
            st.caption("Viable si B/C > 1")
    with k3:
        with st.container(border=True):
            st.metric("TIR mensual", pct(eco["tir_mensual"]))
            st.caption(f"COK mensual: {pct(eco['cok_mensual'], 2)}")
    with k4:
        with st.container(border=True):
            st.metric("Recuperación", f"Mes {eco['recuperacion_mes']}")
            st.caption("Flujo descontado acumulado > 0")

    m1, m2, m3 = st.columns(3)
    with m1:
        with st.container(border=True):
            st.metric(
                "Ahorro anual por menores pérdidas",
                soles(total["ahorro"]),
                delta=f"Impacto {soles(total['impacto_antes'])} → {soles(total['impacto_despues'])}",
                delta_color="off",
            )
    with m2:
        with st.container(border=True):
            st.metric("Inversión inicial", soles(eco["inversion_total"]))
    with m3:
        with st.container(border=True):
            st.metric("Costo operativo anual", soles(eco["costo_operativo_anual"]))

    st.success(eco["decision"], icon="✅")

    # --- Tabla resumen de los 5 objetivos ---------------------------------
    st.subheader("Resumen de los 5 objetivos específicos")

    objetivos = res[res["codigo"] != "ERI"]
    tabla = pd.DataFrame({
        "Objetivo": objetivos["objetivo"],
        "Herramienta": objetivos["herramienta"],
        "Indicador": objetivos["indicador"],
        "As-Is": objetivos["as_is"].map(pct),
        "To-Be": objetivos["to_be"].map(pct),
        "Estándar": objetivos["estandar"].map(lambda x: pct(x, 0)),
        "Semáforo To-Be": objetivos["semaforo_to_be"].map(etiqueta_semaforo),
        "Tipo de dato To-Be": objetivos["tipo_dato_to_be"],
    })
    st.dataframe(tabla, hide_index=True)

    # Conteo del semaforo (antes vs despues)
    r = resumen_semaforo(res)
    s1, s2 = st.columns(2)
    with s1:
        st.markdown("**Semáforo As-Is (antes)**  \n" + "  ·  ".join(
            f"{COLORES[c]['icono']} {n}" for c, n in zip(r["color"], r["as_is"])))
    with s2:
        st.markdown("**Semáforo To-Be (después)**  \n" + "  ·  ".join(
            f"{COLORES[c]['icono']} {n}" for c, n in zip(r["color"], r["to_be"])))


# ---------------------------------------------------------------------------
# 4b. PAGINA 2: AS-IS vs TO-BE vs ESTANDAR  (Paso 5)
# ---------------------------------------------------------------------------
def pagina_comparacion(datos: dict) -> None:
    res = datos["resultados"]

    st.subheader("Situación actual (As-Is) vs propuesta (To-Be) vs estándar")
    st.caption(
        "Barra gris = antes de la propuesta. Barra de color = después, pintada "
        "con su semáforo. Línea punteada = estándar o meta del indicador."
    )

    # Graficos en una cuadricula de 3 columnas (6 indicadores = 2 filas)
    columnas = st.columns(3)
    for i, (_, f) in enumerate(res.iterrows()):
        with columnas[i % 3]:
            with st.container(border=True):
                st.plotly_chart(grafico_indicador(f), key=f"graf_{f['codigo']}")
                nota = f"{etiqueta_semaforo(f['semaforo_to_be'])} · {f['tipo_dato_to_be']}"
                if f["brecha_to_be_pts"] > 0:
                    nota += f" · faltan {f['brecha_to_be_pts']:.1f} pts para la meta"
                st.caption(nota)

    # Grafico de impacto economico
    st.subheader("Impacto económico anual: antes vs después")
    with st.container(border=True):
        st.plotly_chart(grafico_impacto(res), key="graf_impacto")
    total = datos["total"]
    st.caption(
        f"Pérdida anual total: {soles(total['impacto_antes'])} → "
        f"{soles(total['impacto_despues'])} (variación {total['variacion_texto']}). "
        "Supuesto del equipo: el impacto del problema se reparte en partes "
        "iguales entre los 5 objetivos."
    )

    # Tabla de detalle
    with st.expander("Ver tabla de detalle"):
        detalle = pd.DataFrame({
            "Indicador": res["nombre_corto"],
            "Sentido": res["sentido"] + " es mejor",
            "As-Is": res["as_is"].map(pct),
            "To-Be": res["to_be"].map(pct),
            "Estándar": res["estandar"].map(lambda x: pct(x, 0)),
            "Mejora (pts)": res["mejora_pts"].round(1),
            "Variación": res["variacion_texto"],
            "Dato As-Is": res["tipo_dato_as_is"],
            "Dato To-Be": res["tipo_dato_to_be"],
        })
        st.dataframe(detalle, hide_index=True)


# ---------------------------------------------------------------------------
# 4c. PAGINA 3: SEMAFORIZACION  (Paso 6)
# ---------------------------------------------------------------------------
def pagina_semaforo(datos: dict) -> None:
    res = datos["resultados"]
    resumen = resumen_semaforo(res)

    st.subheader("Semaforización de indicadores")

    # Tarjetas con el conteo To-Be
    c1, c2, c3 = st.columns(3)
    for col, color in zip([c1, c2, c3], ["Verde", "Amarillo", "Rojo"]):
        fila = resumen[resumen["color"] == color].iloc[0]
        with col:
            with st.container(border=True):
                st.metric(
                    f"{COLORES[color]['icono']} {color} (To-Be)",
                    int(fila["to_be"]),
                    delta=f"{int(fila['to_be'] - fila['as_is']):+d} vs As-Is",
                    delta_color="normal" if color == "Verde" else "inverse",
                )
                st.caption(INTERPRETACION[color])

    izq, der = st.columns([3, 2])
    with izq:
        with st.container(border=True):
            st.plotly_chart(grafico_semaforo(res), key="graf_semaforo")
    with der:
        with st.container(border=True):
            st.plotly_chart(grafico_conteo_semaforo(resumen), key="graf_conteo")
        st.markdown("**Indicadores que no llegan a verde:**")
        pendientes = res[res["semaforo_to_be"] != "Verde"]
        if pendientes.empty:
            st.write("Todos los indicadores cumplen su meta. ✅")
        for _, f in pendientes.iterrows():
            st.markdown(
                f"- {COLORES[f['semaforo_to_be']]['icono']} **{f['nombre_corto']}**: "
                f"{pct(f['to_be'])} frente a la meta de {pct(f['meta'], 0)} "
                f"(faltan {f['brecha_to_be_pts']:.1f} pts). Dato: {f['tipo_dato_to_be']}."
            )

    # Reglas del semaforo (las mismas de la hoja SEMAFORIZACIÓN)
    with st.expander("Ver reglas del semáforo (parámetros definidos por la empresa)"):
        reglas = []
        for _, f in res.iterrows():
            m, r = pct(f["meta"], 0), pct(f["limite_rojo"], 0)
            if f["sentido"] == "Mayor":
                verde, amarillo, rojo = f">= {m}", f">= {r} y < {m}", f"< {r}"
            else:
                verde, amarillo, rojo = f"<= {m}", f"> {m} y <= {r}", f"> {r}"
            reglas.append({
                "Indicador": f["nombre_corto"],
                "Sentido": f["sentido"] + " es mejor",
                "🟢 Verde": verde,
                "🟡 Amarillo": amarillo,
                "🔴 Rojo": rojo,
            })
        st.dataframe(pd.DataFrame(reglas), hide_index=True)


# ---------------------------------------------------------------------------
# 4d. PAGINA 4: FLUJO DE CAJA  (Paso 7)
# ---------------------------------------------------------------------------
def pagina_flujo(datos: dict) -> None:
    fc = datos["flujo_caja"]
    eco = fc["indicadores"]
    flujo = fc["flujo"]

    st.subheader("Flujo de caja de la propuesta (12 meses)")

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        with st.container(border=True):
            st.metric("VAN", soles(eco["van"]))
    with k2:
        with st.container(border=True):
            st.metric("TIR mensual", pct(eco["tir_mensual"]))
    with k3:
        with st.container(border=True):
            st.metric("B/C", f"{eco['bc']:.2f}")
    with k4:
        with st.container(border=True):
            st.metric("Recuperación", f"Mes {eco['recuperacion_mes']}")

    with st.container(border=True):
        st.plotly_chart(grafico_flujo(flujo), key="graf_flujo")
    st.caption(
        f"El mes 0 es la inversión ({soles(eco['inversion_total'])}). En el mes 1 el "
        "ahorro llega al 50 % porque las herramientas se están implementando. "
        f"La línea azul cruza el cero en el mes {eco['recuperacion_mes']}: ahí se "
        "recupera la inversión."
    )

    izq, der = st.columns(2)
    with izq:
        with st.container(border=True):
            st.plotly_chart(grafico_costos(fc["costos"]), key="graf_costos")
    with der:
        st.markdown("**Inversión inicial (mes 0)**")
        inv = fc["inversion"].copy()
        inv["monto"] = inv["monto"].map(soles)
        st.dataframe(inv[["concepto", "monto"]].rename(
            columns={"concepto": "Concepto", "monto": "Monto"}), hide_index=True)
        st.markdown(f"**Total inversión:** {soles(eco['inversion_total'])}  \n"
                    f"**Costo operativo anual:** {soles(eco['costo_operativo_anual'])}  \n"
                    f"**COK anual:** {pct(eco['cok_anual'], 0)}")

    st.success(eco["decision"], icon="✅")

    with st.expander("Ver flujo de caja mes a mes"):
        tabla = flujo.rename(columns={
            "mes": "Mes",
            "ahorro": "(+) Ahorro",
            "costos_operativos": "(−) Costos operativos",
            "inversion": "(−) Inversión",
            "flujo_neto": "Flujo neto",
            "flujo_acumulado": "Acumulado",
            "flujo_descontado": "Descontado",
            "descontado_acumulado": "Descontado acumulado",
        }).set_index("Mes").T.round(2)
        st.dataframe(tabla)

    with st.expander("Ver supuestos del flujo de caja"):
        sup = fc["supuestos"].rename(
            columns={"concepto": "Concepto", "monto": "Valor", "fuente": "Fuente / supuesto"})
        sup["Valor"] = sup["Valor"].map(
            lambda v: (f"{v:,.0f}" if float(v).is_integer() else f"{v:,.4f}")
            if isinstance(v, (int, float)) else str(v))
        st.dataframe(sup, hide_index=True)


# ---------------------------------------------------------------------------
# 5. ESTRUCTURA GENERAL: titulo + menu lateral
# ---------------------------------------------------------------------------
def main() -> None:
    st.title("📊 Dashboard de resultados – Bodega Nancy y Belén")
    st.caption(
        "Propuesta de mejora de la gestión operativa · Gestión Estratégica de "
        "Operaciones · Lima, 2026"
    )

    try:
        datos = obtener_datos()
    except Exception as error:  # muestra el error en pantalla, sin romper la app
        st.error(f"No se pudieron cargar los datos del Excel:\n\n{error}")
        st.stop()

    with st.sidebar:
        st.header("Navegación")
        pagina = st.radio(
            "Ir a:",
            [
                "1. Resumen",
                "2. As-Is vs To-Be vs Estándar",
                "3. Semaforización",
                "4. Flujo de caja",
            ],
        )
        st.divider()
        if st.button("🔄 Recargar datos del Excel"):
            st.cache_data.clear()
            st.rerun()
        st.caption("Fuente: Esquema_Proyecto_Final.xlsx")

    if pagina.startswith("1"):
        pagina_resumen(datos)
    elif pagina.startswith("2"):
        pagina_comparacion(datos)
    elif pagina.startswith("3"):
        pagina_semaforo(datos)
    else:
        pagina_flujo(datos)


main()
