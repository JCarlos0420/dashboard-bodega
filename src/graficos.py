"""
graficos.py
-----------
Paso 5 del dashboard de Bodega Nancy y Belen.

Funciones que construyen los graficos (Plotly) del dashboard:
    - grafico_indicador(): barras As-Is vs To-Be con linea de Estandar
    - grafico_impacto():   impacto economico anual antes vs despues por objetivo

El color de la barra To-Be es el color de su semaforo (verde/amarillo/rojo).
"""

import pandas as pd
import plotly.graph_objects as go

from semaforo import COLORES

GRIS = "#898781"      # barra As-Is
AZUL = "#2a78d6"      # barra "despues" en el grafico de impacto
TINTA = "#52514e"     # linea de estandar y textos secundarios


def _estilo_base(fig: go.Figure, titulo: str, altura: int = 330) -> go.Figure:
    fig.update_layout(
        title=dict(text=titulo, font=dict(size=15)),
        height=altura,
        margin=dict(l=10, r=10, t=60, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        font=dict(size=13),
    )
    fig.update_yaxes(gridcolor="rgba(128,128,128,0.2)", zeroline=False)
    return fig


def grafico_indicador(f: pd.Series) -> go.Figure:
    """Barras As-Is vs To-Be de UN indicador, con linea punteada del estandar."""
    as_is = f["as_is"] * 100
    to_be = f["to_be"] * 100
    estandar = f["estandar"] * 100
    color_to_be = COLORES[f["semaforo_to_be"]]["fuerte"]

    fig = go.Figure(
        go.Bar(
            x=["As-Is (antes)", "To-Be (después)"],
            y=[as_is, to_be],
            marker_color=[GRIS, color_to_be],
            text=[f"{as_is:.1f} %", f"{to_be:.1f} %"],
            textposition="outside",
            width=0.5,
            hovertemplate="%{x}: %{y:.1f} %<extra></extra>",
        )
    )

    fig.add_hline(
        y=estandar,
        line_dash="dash",
        line_color=TINTA,
        line_width=1.5,
        annotation_text=f"Estándar {estandar:.0f} %",
        annotation_position="top left",
        annotation_font_color=TINTA,
    )

    tope = max(as_is, to_be, estandar)
    fig.update_yaxes(range=[0, max(tope * 1.25, 10)], ticksuffix=" %")

    flecha = "↑ mayor es mejor" if f["sentido"] == "Mayor" else "↓ menor es mejor"
    titulo = (
        f"<b>{f['objetivo']}</b> · {f['nombre_corto']}"
        f"<br><span style='font-size:12px;color:{TINTA}'>{f['indicador']} ({flecha})</span>"
    )
    return _estilo_base(fig, titulo)


def grafico_impacto(resultados: pd.DataFrame) -> go.Figure:
    """Impacto economico anual (S/) antes vs despues, por objetivo especifico."""
    obj = resultados[resultados["codigo"] != "ERI"]
    etiquetas = obj["objetivo"] + "<br>" + obj["herramienta"].str.slice(0, 22)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Antes (As-Is)",
        x=etiquetas,
        y=obj["impacto_antes"],
        marker_color=GRIS,
        text=[f"S/ {v:,.0f}" for v in obj["impacto_antes"]],
        textposition="outside",
        hovertemplate="Antes: S/ %{y:,.2f}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Después (To-Be)",
        x=etiquetas,
        y=obj["impacto_despues"],
        marker_color=AZUL,
        text=[f"S/ {v:,.0f}" for v in obj["impacto_despues"]],
        textposition="outside",
        hovertemplate="Después: S/ %{y:,.2f}<extra></extra>",
    ))

    fig.update_layout(barmode="group", bargap=0.3)
    fig.update_yaxes(title_text="S/ al año", tickprefix="S/ ",
                     range=[0, obj["impacto_antes"].max() * 1.2])
    fig = _estilo_base(fig, "<b>Impacto económico anual por objetivo</b> (pérdidas en S/)", 420)
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


# ---------------------------------------------------------------------------
# PASO 6: SEMAFORIZACION
# ---------------------------------------------------------------------------
def grafico_semaforo(resultados: pd.DataFrame) -> go.Figure:
    """
    Tablero tipo semaforo: una fila por indicador y dos columnas (As-Is, To-Be).
    Cada circulo se pinta con su color y muestra el valor del indicador.
    """
    nombres = resultados["nombre_corto"].tolist()[::-1]   # ERI arriba
    filas = resultados.iloc[::-1]

    fig = go.Figure()
    for momento, x_pos, titulo in [("as_is", 0, "As-Is (antes)"),
                                   ("to_be", 1, "To-Be (después)")]:
        colores = [COLORES[c]["fuerte"] for c in filas[f"semaforo_{momento}"]]
        fig.add_trace(go.Scatter(
            x=[x_pos] * len(filas),
            y=nombres,
            mode="markers+text",
            marker=dict(size=34, color=colores, line=dict(width=2, color="white")),
            text=[f"{v * 100:.1f} %" for v in filas[momento]],
            textposition="middle right",
            textfont=dict(size=13),
            customdata=filas[f"semaforo_{momento}"],
            hovertemplate=f"{titulo}<br>%{{y}}: %{{text}} (%{{customdata}})<extra></extra>",
        ))

    # Columna de metas como referencia
    fig.add_trace(go.Scatter(
        x=[2] * len(filas),
        y=nombres,
        mode="text",
        text=[("≥ " if s == "Mayor" else "≤ ") + f"{m * 100:.0f} %"
              for s, m in zip(filas["sentido"], filas["meta"])],
        textfont=dict(size=13, color=TINTA),
        hoverinfo="skip",
    ))

    fig.update_xaxes(
        tickvals=[0, 1, 2],
        ticktext=["<b>As-Is (antes)</b>", "<b>To-Be (después)</b>", "<b>Meta</b>"],
        side="top", range=[-0.4, 2.5], showgrid=False, zeroline=False,
    )
    fig.update_yaxes(showgrid=False)
    return _estilo_base(fig, "", altura=420)


def grafico_conteo_semaforo(resumen: pd.DataFrame) -> go.Figure:
    """Barras apiladas: cuantos indicadores en verde/amarillo/rojo, antes y despues."""
    fig = go.Figure()
    for _, fila in resumen.iterrows():
        color = fila["color"]
        fig.add_trace(go.Bar(
            name=color,
            y=["As-Is (antes)", "To-Be (después)"],
            x=[fila["as_is"], fila["to_be"]],
            orientation="h",
            marker_color=COLORES[color]["fuerte"],
            text=[fila["as_is"] or "", fila["to_be"] or ""],
            textposition="inside",
            hovertemplate=f"{color}: %{{x}} indicadores<extra></extra>",
        ))
    fig.update_layout(barmode="stack")
    fig.update_xaxes(title_text="N.º de indicadores", dtick=1)
    fig = _estilo_base(fig, "<b>Indicadores por color</b>", altura=260)
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


# ---------------------------------------------------------------------------
# PASO 7: FLUJO DE CAJA
# ---------------------------------------------------------------------------
VERDE = COLORES["Verde"]["fuerte"]
ROJO = COLORES["Rojo"]["fuerte"]


def grafico_flujo(flujo: pd.DataFrame) -> go.Figure:
    """Flujo neto mensual (barras) y flujo descontado acumulado (linea)."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Flujo neto del mes",
        x=flujo["mes"],
        y=flujo["flujo_neto"],
        marker_color=[VERDE if v >= 0 else ROJO for v in flujo["flujo_neto"]],
        hovertemplate="Mes %{x}<br>Flujo neto: S/ %{y:,.2f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        name="Flujo descontado acumulado",
        x=flujo["mes"],
        y=flujo["descontado_acumulado"],
        mode="lines+markers",
        line=dict(color=AZUL, width=2.5),
        marker=dict(size=8),
        hovertemplate="Mes %{x}<br>Acumulado: S/ %{y:,.2f}<extra></extra>",
    ))
    fig.add_hline(y=0, line_color=TINTA, line_width=1)
    fig.update_xaxes(title_text="Mes", dtick=1)
    fig.update_yaxes(title_text="S/", tickprefix="S/ ")
    fig = _estilo_base(fig, "<b>Flujo neto mensual y flujo descontado acumulado</b>", 420)
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def grafico_costos(costos: pd.DataFrame) -> go.Figure:
    """Costos operativos anuales por objetivo (barras horizontales)."""
    df = costos.sort_values("monto")
    fig = go.Figure(go.Bar(
        x=df["monto"],
        y=df["concepto"].str.slice(0, 45),
        orientation="h",
        marker_color=AZUL,
        text=[f"S/ {v:,.2f}" for v in df["monto"]],
        textposition="outside",
        hovertemplate="%{y}<br>S/ %{x:,.2f} al año<extra></extra>",
    ))
    fig.update_xaxes(tickprefix="S/ ", range=[0, df["monto"].max() * 1.3])
    return _estilo_base(fig, "<b>Costos operativos anuales por objetivo</b>", 330)
