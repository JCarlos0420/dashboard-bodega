# Dashboard de resultados – Bodega Nancy y Belén

Dashboard en Python (Streamlit + Plotly) con los resultados de la propuesta de
mejora de la gestión operativa de Bodega Nancy y Belén (Carabayllo, Lima, 2026).
Curso: Gestión Estratégica de Operaciones.

## Contenido

| Página | Qué muestra | Hoja del Excel |
|---|---|---|
| 1. Resumen | ERI antes/después, VAN, B/C, TIR, recuperación y tabla de los 5 objetivos | Resultados-Indicadores, Flujo Caja |
| 2. As-Is vs To-Be vs Estándar | Gráfico por indicador e impacto económico anual | Resultados-Indicadores |
| 3. Semaforización | Tablero de colores, conteo antes/después y reglas | SEMAFORIZACIÓN |
| 4. Flujo de caja | Flujo mensual, acumulado descontado, costos e inversión | Flujo Caja |

## Estructura

```
dashboard_bodega/
├── .streamlit/config.toml   tema visual
├── data/Esquema_Proyecto_Final.xlsx
├── src/
│   ├── carga_datos.py       lee las hojas de resultados del Excel
│   ├── semaforo.py          reglas Verde / Amarillo / Rojo
│   └── graficos.py          gráficos Plotly
├── app.py                   dashboard (4 páginas)
└── requirements.txt
```

## Cómo ejecutarlo

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
python -m pip install -r requirements.txt
streamlit run app.py
```

Si se modifica el Excel: guardarlo en Microsoft Excel y pulsar
"Recargar datos del Excel" en el menú lateral del dashboard.

## Indicadores

| Código | Objetivo | Herramienta | As-Is | To-Be | Estándar |
|---|---|---|---|---|---|
| ERI | Problema principal | Exactitud del registro de inventarios | 72.6 % | 95.0 % | 95 % |
| IND.1 | O.E 1 | Punto de reorden y stock de seguridad | 50.0 % | 5.0 % | 5 % |
| IND.2 | O.E 2 | Conteo cíclico | 0.0 % | 75.0 % | 95 % |
| IND.3 | O.E 3 | Kardex digital en Excel | 0.0 % | 90.0 % | 95 % |
| IND.4 | O.E 4 | Clasificación ABC | 0.0 % | 100.0 % | 100 % |
| IND.5 | O.E 5 | 5S con control visual | 40.0 % | 9.7 % | 10 % |

Evaluación económica (12 meses): VAN S/ 714.49 · B/C 1.43 · TIR mensual 41.6 % ·
recuperación en el mes 3 → propuesta VIABLE.
