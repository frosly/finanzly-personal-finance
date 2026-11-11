# Finanzly | Finanzas personales
# ============================================================
# INSTALACIÓN:
#   pip install streamlit pandas plotly
#
# EJECUCIÓN:
#   streamlit run app.py
#
# Los datos se guardan en finanzly_datos.json, junto a este archivo.
#
# Fórmula de balance conservada respecto a la aplicación original:
# ingresos - gastos - aportes de ahorro + retiros de ahorro.
# Se incorpora el ingreso extra como ingreso y los gastos fijos pagados
# como gastos. Los gastos fijos pendientes no descuentan el balance.
# ============================================================

import json
import uuid
import calendar
from pathlib import Path
from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ============================================================
# 1. CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="Finanzly | Finanzas personales",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

ARCHIVO_DATOS = Path(__file__).with_name("finanzly_datos.json")

MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]
DIAS_SEMANA = {
    "Lunes": 0, "Martes": 1, "Miércoles": 2, "Jueves": 3,
    "Viernes": 4, "Sábado": 5, "Domingo": 6
}
CATEGORIAS_GASTO = [
    "Ocio", "Comida", "Transporte", "Compras", "Otros",
    "Pagos y compromisos"
]
COLORES = {
    "Ingreso": "#1764F5",
    "Ingreso extra": "#16BBD6",
    "Gasto": "#F05B70",
    "Gasto fijo": "#F5A623",
    "Ahorro": "#16B99A",
    "Retiro ahorro": "#8B7CF6",
}
COLUMNAS = [
    "ID", "Fecha", "Tipo", "Categoria", "Concepto",
    "Monto", "Horas", "Monto_hora", "Pagado", "Referencia"
]

# ============================================================
# 2. DISEÑO CSS — ESTILO DE LA REFERENCIA
# ============================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');

:root {
    --fondo: #F3F6FB;
    --azul: #155EEF;
    --azul-oscuro: #172B4D;
    --texto: #27364B;
    --suave: #7B8798;
    --borde: #E9EEF5;
    --blanco: #FFFFFF;
}
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: var(--fondo); color: var(--texto); }
.block-container {
    max-width: 1580px;
    padding: 1.2rem 2.1rem 2.6rem;
}
header[data-testid="stHeader"] { background: transparent; }
h1, h2, h3, h4 { color: var(--azul-oscuro); letter-spacing: -.035em; }
p, label { color: var(--texto); }
#MainMenu, footer { visibility: hidden; }

.brand-wrap { display:flex; align-items:center; gap:10px; padding:2px 0 5px; }
.brand-mark {
    width:36px; height:36px; border-radius:12px; display:flex;
    align-items:center; justify-content:center; color:white; font-size:21px;
    font-weight:800; background:linear-gradient(145deg,#145BFA,#12BFE4);
    box-shadow:0 5px 12px rgba(21,94,239,.18);
}
.brand-name { color:#15243B; font-size:1.55rem; font-weight:800; letter-spacing:-.065em; }
.page-heading { color:#172B4D; font-size:1.55rem; font-weight:800; letter-spacing:-.045em; }
.page-subtitle { color:#7B8798; font-size:.91rem; margin-top:2px; }
.panel {
    background:#fff; border:1px solid var(--borde); border-radius:19px;
    padding:19px 21px; box-shadow:0 5px 22px rgba(27,48,79,.045);
    margin-bottom:14px;
}
.panel-title { color:#172B4D; font-weight:750; font-size:1.08rem; }
.panel-subtitle { color:#8793A5; font-size:.79rem; margin-top:3px; }
.metric-label { color:#738096; font-size:.82rem; font-weight:600; }
.metric-value { color:#172B4D; font-size:2rem; font-weight:800; letter-spacing:-.055em; margin-top:8px; }
.metric-note { color:#8A95A5; font-size:.73rem; margin-top:6px; }
.metric-dot {
    width:36px; height:36px; display:flex; align-items:center; justify-content:center;
    border-radius:50%; background:#202124; color:white; font-size:17px;
}
.insight-panel {
    background:linear-gradient(118deg,#1648E8 0%,#087CEB 58%,#12BFE2 100%);
    color:#fff; border-radius:19px; padding:21px 22px; min-height:190px;
    box-shadow:0 9px 23px rgba(21,94,239,.17);
}
.insight-title { font-size:1.05rem; font-weight:800; color:#fff; }
.insight-copy { color:#F0F7FF; font-size:.87rem; line-height:1.5; margin-top:14px; }
.soft-pill {
    display:inline-block; background:#EEF4FF; color:#155EEF; border-radius:30px;
    padding:5px 10px; font-size:.73rem; font-weight:700;
}
.status-good { color:#0A9B69; font-weight:700; }
.status-bad { color:#E04456; font-weight:700; }
div[data-testid="stMetric"] {
    background:#fff; border:1px solid var(--borde); border-radius:18px;
    padding:17px 18px; box-shadow:0 5px 20px rgba(27,48,79,.045);
    min-height:116px;
}
div[data-testid="stMetric"] label { color:#758197; font-size:.82rem; font-weight:600; }
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color:#172B4D; font-size:1.75rem; font-weight:800; letter-spacing:-.04em;
}
div[data-testid="stMetric"] [data-testid="stMetricDelta"] { font-size:.75rem; }
.stProgress > div > div > div > div { background:#1764F5; }
div.stButton > button, div.stFormSubmitButton > button {
    border-radius:11px; font-weight:700; min-height:2.55rem;
}
div.stButton > button[kind="primary"], div.stFormSubmitButton > button[kind="primary"] {
    background:#155EEF; border-color:#155EEF;
}
div[role="radiogroup"] { gap:.35rem; }
div[role="radiogroup"] label {
    background:white; border:1px solid #E5EAF2; padding:7px 13px;
    border-radius:11px;
}
[data-testid="stDataFrame"] { border:1px solid #E8EDF5; border-radius:13px; overflow:hidden; }
hr { border-color:#E7ECF4; }
@media(max-width:900px) {
    .block-container { padding: .8rem .8rem 2rem; }
    .metric-value { font-size:1.55rem; }
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# 3. PERSISTENCIA Y ESTADO
# ============================================================

def dataframe_vacio():
    return pd.DataFrame(columns=COLUMNAS)


def cargar_datos():
    if ARCHIVO_DATOS.exists():
        try:
            with ARCHIVO_DATOS.open("r", encoding="utf-8") as archivo:
                datos = json.load(archivo)
            movimientos = pd.DataFrame(datos.get("movimientos", []))
            if movimientos.empty:
                movimientos = dataframe_vacio()
            else:
                for columna in COLUMNAS:
                    if columna not in movimientos.columns:
                        movimientos[columna] = None
                movimientos = movimientos[COLUMNAS]
            return datos.get("perfil", {}), movimientos, datos.get("gastos_fijos", [])
        except (OSError, ValueError, json.JSONDecodeError):
            st.warning("No se pudo leer el archivo de datos. Se iniciará una sesión vacía.")
    return {}, dataframe_vacio(), []


if "perfil" not in st.session_state:
    perfil_cargado, movimientos_cargados, fijos_cargados = cargar_datos()
    st.session_state.perfil = perfil_cargado
    st.session_state.movimientos = movimientos_cargados
    st.session_state.gastos_fijos = fijos_cargados

if "movimientos" not in st.session_state:
    st.session_state.movimientos = dataframe_vacio()
if "gastos_fijos" not in st.session_state:
    st.session_state.gastos_fijos = []

# Normalizar tipos al recuperar el archivo JSON.
if not st.session_state.movimientos.empty:
    st.session_state.movimientos["Fecha"] = pd.to_datetime(
        st.session_state.movimientos["Fecha"], errors="coerce"
    )
    st.session_state.movimientos["Monto"] = pd.to_numeric(
        st.session_state.movimientos["Monto"], errors="coerce"
    ).fillna(0)
    st.session_state.movimientos["Pagado"] = (
        st.session_state.movimientos["Pagado"].fillna(False).astype(bool)
    )


def guardar_datos():
    movimientos = st.session_state.movimientos.copy()
    if not movimientos.empty:
        movimientos["Fecha"] = pd.to_datetime(
            movimientos["Fecha"], errors="coerce"
        ).dt.strftime("%Y-%m-%d")
    datos = {
        "perfil": st.session_state.perfil,
        "movimientos": movimientos.where(pd.notna(movimientos), None).to_dict("records"),
        "gastos_fijos": st.session_state.gastos_fijos,
    }
    with ARCHIVO_DATOS.open("w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)


# ============================================================
# 4. FUNCIONES FINANCIERAS
# ============================================================

def moneda(valor):
    return f"${float(valor):,.2f}"


def mes_actual():
    hoy = date.today()
    return f"{MESES[hoy.month - 1].capitalize()} {hoy.year}"


def contar_dias_cobro(dias, anio=None, mes=None):
    hoy = date.today()
    anio = anio or hoy.year
    mes = mes or hoy.month
    seleccionados = {DIAS_SEMANA[d] for d in dias if d in DIAS_SEMANA}
    ultimo_dia = calendar.monthrange(anio, mes)[1]
    return sum(
        date(anio, mes, numero).weekday() in seleccionados
        for numero in range(1, ultimo_dia + 1)
    )


def estimacion_perfil():
    perfil = st.session_state.perfil
    if not perfil:
        return 0.0, 0.0, 0
    cantidad_dias = contar_dias_cobro(perfil.get("dias_cobro", []))
    ingreso = float(perfil.get("monto_por_dia", 0)) * cantidad_dias
    if perfil.get("tipo_ahorro") == "Monto fijo":
        ahorro = float(perfil.get("ahorro_objetivo", 0))
    else:
        ahorro = ingreso * float(perfil.get("ahorro_porcentaje", 0)) / 100
    return ingreso, ahorro, cantidad_dias


def movimientos_del_mes():
    df = st.session_state.movimientos.copy()
    if df.empty:
        return df
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    hoy = date.today()
    return df[
        (df["Fecha"].dt.month == hoy.month) &
        (df["Fecha"].dt.year == hoy.year)
    ].copy()


def resumen_financiero():
    df = movimientos_del_mes()
    if df.empty:
        df = dataframe_vacio()

    def total(tipo):
        return float(df.loc[df["Tipo"] == tipo, "Monto"].sum())

    ingresos = total("Ingreso")
    extras = total("Ingreso extra")
    gastos_variables = total("Gasto")
    gastos_fijos = float(
        df.loc[(df["Tipo"] == "Gasto fijo") & df["Pagado"].eq(True), "Monto"].sum()
    )
    aportes = total("Ahorro")
    retiros = total("Retiro ahorro")
    gastos_totales = gastos_variables + gastos_fijos

    # Balance original: ingresos - gastos - aportes + retiros.
    # Se suma ingreso extra y se incluyen los gastos fijos ya pagados.
    balance = ingresos + extras - gastos_totales - aportes + retiros

    return {
        "ingresos": ingresos,
        "extras": extras,
        "gastos_fijos": gastos_fijos,
        "gastos_variables": gastos_variables,
        "gastos": gastos_totales,
        "aportes": aportes,
        "retiros": retiros,
        "ahorro_mes": aportes - retiros,
        "balance": balance,
        "ingreso_total": ingresos + extras,
    }


def ahorro_acumulado():
    df = st.session_state.movimientos
    if df.empty:
        return 0.0
    aportes = df.loc[df["Tipo"] == "Ahorro", "Monto"].sum()
    retiros = df.loc[df["Tipo"] == "Retiro ahorro", "Monto"].sum()
    return float(aportes - retiros)


def registrar_movimiento(tipo, categoria, concepto, monto, fecha_mov,
                         horas=None, monto_hora=None, referencia=None):
    nuevo = {
        "ID": str(uuid.uuid4()),
        "Fecha": pd.Timestamp(fecha_mov),
        "Tipo": tipo,
        "Categoria": categoria,
        "Concepto": concepto.strip(),
        "Monto": float(monto),
        "Horas": horas,
        "Monto_hora": monto_hora,
        "Pagado": True,
        "Referencia": referencia,
    }
    st.session_state.movimientos = pd.concat(
        [st.session_state.movimientos, pd.DataFrame([nuevo])],
        ignore_index=True,
    )
    guardar_datos()


# ============================================================
# 5. CABECERA Y NAVEGACIÓN SUPERIOR
# ============================================================

cabecera_izq, cabecera_der = st.columns([1.05, 5.2], vertical_alignment="center")
with cabecera_izq:
    st.markdown(
        '<div class="brand-wrap"><div class="brand-mark">◆</div>'
        '<div class="brand-name">Finanzly</div></div>',
        unsafe_allow_html=True,
    )
with cabecera_der:
    seccion = st.radio(
        "Secciones",
        ["Dashboard", "Mi perfil", "Movimientos", "Historial"],
        horizontal=True,
        label_visibility="collapsed",
        key="seccion_activa",
    )

st.markdown("---")

# Perfil compacto siempre visible, cuando ya existe.
perfil = st.session_state.perfil
if perfil:
    ingreso_estimado, ahorro_estimado, dias_estimados = estimacion_perfil()
    st.markdown(
        f'<div style="display:flex;justify-content:space-between;gap:12px;'
        f'flex-wrap:wrap;color:#7B8798;font-size:.79rem;margin:0 0 15px;">'
        f'<span><b style="color:#26364B;">Perfil:</b> {perfil["nombre"]} '
        f'&nbsp;·&nbsp; Cobro {moneda(perfil.get("monto_por_dia", 0))} por día</span>'
        f'<span><b style="color:#26364B;">Ingreso estimado:</b> {moneda(ingreso_estimado)} '
        f'&nbsp;·&nbsp; {dias_estimados} días de cobro en {mes_actual()}</span></div>',
        unsafe_allow_html=True,
    )

# ============================================================
# 6. DASHBOARD
# ============================================================

if seccion == "Dashboard":
    if not st.session_state.perfil:
        st.markdown('<div class="page-heading">Dashboard Overview</div>', unsafe_allow_html=True)
        st.markdown('<div class="page-subtitle">Tu salud financiera, de un vistazo.</div>', unsafe_allow_html=True)
        st.info("Para comenzar, configura tu perfil de cobro y tu objetivo de ahorro.")
        if st.button("Configurar mi perfil", type="primary"):
            st.session_state.seccion_activa = "Mi perfil"
            st.rerun()
    else:
        r = resumen_financiero()
        ingreso_estimado, ahorro_estimado, dias_estimados = estimacion_perfil()

        titulo_izq, titulo_der = st.columns([3, 2], vertical_alignment="center")
        with titulo_izq:
            st.markdown(
                f'<div class="page-heading">¡Hola, {perfil["nombre"]}! 👋</div>'
                f'<div class="page-subtitle">Tu salud financiera de un vistazo · {mes_actual()}</div>',
                unsafe_allow_html=True,
            )
        with titulo_der:
            st.markdown(
                f'<div style="text-align:right;color:#8793A5;font-size:.8rem;">'
                f'Perfil de cobro activo · {dias_estimados} días estimados</div>',
                unsafe_allow_html=True,
            )

        st.write("")
        # Tarjetas superiores: cuatro indicadores como en la referencia.
        m1, m2, m3, m4 = st.columns([1, 1, 1, 1.05])
        m1.metric("◉  Balance disponible", moneda(r["balance"]))
        m2.metric("↙  Ingreso percibido", moneda(r["ingreso_total"]))
        m3.metric("↗  Gastos del mes", moneda(r["gastos"]))
        m4.metric("⇧  Ahorro acumulado", moneda(ahorro_acumulado()))

        # Resumen adicional en una franja compacta.
        e1, e2, e3 = st.columns(3)
        with e1:
            st.markdown(
                f'<div class="panel" style="padding:13px 17px;">'
                f'<div class="metric-label">Gastos fijos pagados</div>'
                f'<div style="font-size:1.25rem;font-weight:800;color:#172B4D;">{moneda(r["gastos_fijos"])}</div></div>',
                unsafe_allow_html=True,
            )
        with e2:
            st.markdown(
                f'<div class="panel" style="padding:13px 17px;">'
                f'<div class="metric-label">Gastos variables</div>'
                f'<div style="font-size:1.25rem;font-weight:800;color:#172B4D;">{moneda(r["gastos_variables"])}</div></div>',
                unsafe_allow_html=True,
            )
        with e3:
            st.markdown(
                f'<div class="panel" style="padding:13px 17px;">'
                f'<div class="metric-label">Ingresos extra</div>'
                f'<div style="font-size:1.25rem;font-weight:800;color:#172B4D;">{moneda(r["extras"])}</div></div>',
                unsafe_allow_html=True,
            )

        # Progreso del ingreso y estado del presupuesto.
        prog_col, estado_col = st.columns([1.35, 1], gap="medium")
        with prog_col:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">Progreso de ingresos del mes</div>', unsafe_allow_html=True)
            progreso = min(r["ingresos"] / ingreso_estimado, 1.0) if ingreso_estimado > 0 else 0
            st.progress(progreso)
            st.caption(
                f"{moneda(r['ingresos'])} percibidos de {moneda(ingreso_estimado)} estimados "
                f"({progreso * 100:.1f} %)."
            )
            st.caption(f"Objetivo de ahorro estimado: {moneda(ahorro_estimado)}")
            st.markdown('</div>', unsafe_allow_html=True)
        with estado_col:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">Estado financiero</div>', unsafe_allow_html=True)
            if r["gastos"] > r["ingreso_total"]:
                st.error("Tus gastos superan los ingresos registrados.")
            elif r["balance"] < 0:
                st.warning("Tu balance disponible está por debajo de cero.")
            else:
                st.success("Tu balance está en positivo. ¡Buen trabajo!")
            st.markdown('</div>', unsafe_allow_html=True)

        # Área de gráficos y análisis.
        izquierda, derecha = st.columns([1.55, 1], gap="large")

        with izquierda:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">Flujo de caja mensual</div>', unsafe_allow_html=True)
            st.markdown('<div class="panel-subtitle">Comparación de ingresos y gastos registrados</div>', unsafe_allow_html=True)

            todo = st.session_state.movimientos.copy()
            if not todo.empty:
                todo["Fecha"] = pd.to_datetime(todo["Fecha"], errors="coerce")
                todo["Mes"] = todo["Fecha"].dt.strftime("%Y-%m")
                todo["Ingresos"] = todo.apply(
                    lambda fila: fila["Monto"] if fila["Tipo"] in ["Ingreso", "Ingreso extra"] else 0,
                    axis=1,
                )
                todo["Gastos"] = todo.apply(
                    lambda fila: fila["Monto"] if fila["Tipo"] in ["Gasto", "Gasto fijo"] else 0,
                    axis=1,
                )
                mensual = todo.groupby("Mes")[["Ingresos", "Gastos"]].sum().reset_index().tail(6)
                fig_flujo = go.Figure()
                fig_flujo.add_trace(go.Scatter(
                    x=mensual["Mes"], y=mensual["Ingresos"],
                    mode="lines+markers", name="Ingresos",
                    line=dict(color="#1764F5", width=3, shape="spline"),
                    fill="tozeroy", fillcolor="rgba(23,100,245,.06)",
                ))
                fig_flujo.add_trace(go.Scatter(
                    x=mensual["Mes"], y=mensual["Gastos"],
                    mode="lines+markers", name="Gastos",
                    line=dict(color="#16C7D8", width=3, shape="spline"),
                ))
                fig_flujo.update_layout(
                    height=265, margin=dict(l=5, r=5, t=12, b=5),
                    legend=dict(orientation="h", y=1.12, x=0),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=False, title=""),
                    yaxis=dict(gridcolor="#EDF1F7", title="", tickprefix="$"),
                    font=dict(color="#7B8798", size=11),
                    hovermode="x unified",
                )
                st.plotly_chart(fig_flujo, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Registra tus primeros movimientos para visualizar el flujo de caja.")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">Ingresos, gastos y ahorros</div>', unsafe_allow_html=True)
            if not todo.empty:
                graf = todo[todo["Tipo"].isin(
                    ["Ingreso", "Ingreso extra", "Gasto", "Gasto fijo", "Ahorro"]
                )].copy()
                graf["Mes"] = graf["Fecha"].dt.strftime("%Y-%m")
                graf = graf.groupby(["Mes", "Tipo"], as_index=False)["Monto"].sum()
                fig_barras = px.bar(
                    graf, x="Mes", y="Monto", color="Tipo", barmode="group",
                    color_discrete_map=COLORES,
                    labels={"Mes": "Mes", "Monto": "Monto ($)", "Tipo": "Movimiento"},
                )
                fig_barras.update_layout(
                    height=245, margin=dict(l=5, r=5, t=8, b=5),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#EDF1F7", title=""),
                    legend=dict(orientation="h", y=1.12, x=0),
                )
                st.plotly_chart(fig_barras, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Aún no hay movimientos para comparar.")
            st.markdown('</div>', unsafe_allow_html=True)

        with derecha:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">Distribución de gastos y ahorro</div>', unsafe_allow_html=True)
            st.markdown('<div class="panel-subtitle">Cómo se distribuye el dinero del mes</div>', unsafe_allow_html=True)

            valores = [
                ("Gastos", r["gastos"]),
                ("Ahorro neto", max(r["ahorro_mes"], 0)),
            ]
            dona_df = pd.DataFrame(valores, columns=["Destino", "Monto"])
            dona_df = dona_df[dona_df["Monto"] > 0]
            if not dona_df.empty:
                fig_dona = px.pie(
                    dona_df, names="Destino", values="Monto", hole=.68,
                    color="Destino",
                    color_discrete_map={"Gastos": "#155EEF", "Ahorro neto": "#12BBD6"},
                )
                fig_dona.update_traces(
                    textposition="inside", textinfo="percent",
                    hovertemplate="%{label}: $%{value:,.2f}<extra></extra>",
                )
                fig_dona.update_layout(
                    height=265, margin=dict(l=4, r=4, t=5, b=4),
                    showlegend=True, legend=dict(font=dict(size=10)),
                    paper_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig_dona, use_container_width=True, config={"displayModeBar": False})
                st.caption(f"Total gastado y ahorrado: **{moneda(r['gastos'] + max(r['ahorro_mes'], 0))}**")
            else:
                st.info("Aún no hay gastos ni ahorros registrados este mes.")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown(
                '<div class="insight-panel">'
                '<div class="insight-title">✦ Finanzly · Consejo financiero</div>'
                '<div class="insight-copy"><b>Tu dinero, bajo control.</b><br>'
                'Registra tus movimientos a medida que ocurren y revisa tu progreso '
                'para mantener tus gastos dentro de tus ingresos y avanzar hacia tu ahorro.</div>'
                '</div>',
                unsafe_allow_html=True,
            )

            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">Evolución del balance</div>', unsafe_allow_html=True)
            dmes = movimientos_del_mes()
            if not dmes.empty:
                dmes = dmes.sort_values("Fecha")
                impactos = []
                for _, fila in dmes.iterrows():
                    if fila["Tipo"] in ["Ingreso", "Ingreso extra", "Retiro ahorro"]:
                        impactos.append(float(fila["Monto"]))
                    elif fila["Tipo"] in ["Gasto", "Gasto fijo", "Ahorro"]:
                        impactos.append(-float(fila["Monto"]))
                    else:
                        impactos.append(0.0)
                dmes["Impacto"] = impactos
                dmes["Balance"] = dmes["Impacto"].cumsum()
                evolucion = dmes.groupby(dmes["Fecha"].dt.date)["Balance"].last().reset_index()
                evolucion.columns = ["Día", "Balance"]
                fig_linea = px.line(
                    evolucion, x="Día", y="Balance", markers=True,
                    labels={"Día": "", "Balance": "Balance ($)"},
                )
                fig_linea.update_traces(line=dict(color="#1764F5", width=3), marker=dict(size=7))
                fig_linea.update_layout(
                    height=210, margin=dict(l=4, r=4, t=8, b=4),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    yaxis=dict(gridcolor="#EDF1F7", title=""),
                )
                st.plotly_chart(fig_linea, use_container_width=True, config={"displayModeBar": False})
            else:
                st.caption("La evolución aparecerá al registrar movimientos.")
            st.markdown('</div>', unsafe_allow_html=True)

        # Tabla inferior estilo "Latest Transactions".
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Últimos movimientos</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel-subtitle">Tus transacciones más recientes</div>', unsafe_allow_html=True)
        recientes = st.session_state.movimientos.copy()
        if not recientes.empty:
            recientes["Fecha"] = pd.to_datetime(recientes["Fecha"], errors="coerce")
            recientes = recientes.sort_values("Fecha", ascending=False).head(6)
            tabla = recientes[["Concepto", "Monto", "Categoria", "Fecha", "Tipo"]].copy()
            tabla["Fecha"] = tabla["Fecha"].dt.strftime("%d/%m/%Y")
            st.dataframe(
                tabla, use_container_width=True, hide_index=True,
                column_config={
                    "Monto": st.column_config.NumberColumn("Monto", format="$%.2f"),
                    "Fecha": st.column_config.TextColumn("Fecha"),
                },
            )
        else:
            st.info("Todavía no tienes movimientos registrados.")
        st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# 7. MI PERFIL
# ============================================================

elif seccion == "Mi perfil":
    p = st.session_state.perfil
    st.markdown('<div class="page-heading">Mi perfil</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Configura tus ingresos habituales y tu objetivo de ahorro.</div>', unsafe_allow_html=True)

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Datos personales y perfil de cobro</div>', unsafe_allow_html=True)
    st.caption(
        "Selecciona días de la semana. Finanzly calcula cuántas veces aparece cada día "
        "en el mes actual y estima tu ingreso mensual."
    )
    with st.form("formulario_perfil"):
        nombre = st.text_input("Nombre", value=p.get("nombre", ""))
        dias = st.multiselect(
            "Días habituales de cobro",
            list(DIAS_SEMANA.keys()),
            default=[d for d in p.get("dias_cobro", ["Viernes"]) if d in DIAS_SEMANA],
            help="Selecciona uno o varios días de la semana en los que recibes tu pago.",
        )
        monto_dia = st.number_input(
            "¿Cuánto cobras por cada día de trabajo? ($)",
            min_value=0.0, value=float(p.get("monto_por_dia", 0)),
            step=5.0, help="Importe que recibes por cada día seleccionado.",
        )
        tipo_ahorro = st.radio(
            "¿Cómo deseas calcular tu ahorro mensual?",
            ["Porcentaje", "Monto fijo"], horizontal=True,
            index=0 if p.get("tipo_ahorro", "Porcentaje") == "Porcentaje" else 1,
        )
        if tipo_ahorro == "Porcentaje":
            porcentaje = st.number_input(
                "Porcentaje que deseas ahorrar (%)",
                min_value=0.0, max_value=100.0,
                value=float(p.get("ahorro_porcentaje", 10)), step=1.0,
                help="Se calcula sobre el ingreso mensual estimado.",
            )
            ahorro_fijo = 0.0
        else:
            ahorro_fijo = st.number_input(
                "Monto de ahorro mensual ($)", min_value=0.0,
                value=float(p.get("ahorro_objetivo", 0)), step=5.0,
                help="Cantidad fija que deseas ahorrar cada mes.",
            )
            porcentaje = 0.0

        guardar_perfil = st.form_submit_button(
            "Guardar mi perfil", type="primary", use_container_width=True
        )
        if guardar_perfil:
            if not nombre.strip():
                st.error("Debes escribir tu nombre.")
            elif not dias:
                st.error("Selecciona al menos un día de cobro.")
            elif monto_dia <= 0:
                st.error("El monto por día debe ser mayor que cero.")
            else:
                st.session_state.perfil = {
                    "nombre": nombre.strip(),
                    "dias_cobro": dias,
                    "monto_por_dia": float(monto_dia),
                    "tipo_ahorro": tipo_ahorro,
                    "ahorro_porcentaje": float(porcentaje),
                    "ahorro_objetivo": float(ahorro_fijo),
                }
                guardar_datos()
                st.success("Perfil guardado correctamente.")
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.perfil:
        ingreso_est, ahorro_est, cantidad_dias = estimacion_perfil()
        a, b, c = st.columns(3)
        a.metric("Días de cobro este mes", cantidad_dias)
        b.metric("Ingreso mensual estimado", moneda(ingreso_est))
        c.metric("Ahorro mensual estimado", moneda(ahorro_est))

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Gastos fijos recurrentes</div>', unsafe_allow_html=True)
    st.caption("Registra renta, servicios, transporte y otros compromisos mensuales.")
    with st.form("form_gasto_fijo"):
        c1, c2, c3 = st.columns([2, 1.2, 1])
        concepto_fijo = c1.text_input("Concepto", placeholder="Ej. Alquiler, internet, transporte")
        categoria_fija = c2.selectbox(
            "Categoría", ["Vivienda", "Servicios", "Transporte", "Educación", "Otros"]
        )
        monto_fijo = c3.number_input("Monto mensual ($)", min_value=0.0, step=5.0)
        agregar_fijo = st.form_submit_button("Agregar gasto fijo")
        if agregar_fijo:
            if not concepto_fijo.strip():
                st.error("Escribe el concepto del gasto fijo.")
            elif monto_fijo <= 0:
                st.error("El monto debe ser mayor que cero.")
            else:
                st.session_state.gastos_fijos.append({
                    "id": str(uuid.uuid4()),
                    "concepto": concepto_fijo.strip(),
                    "categoria": categoria_fija,
                    "monto": float(monto_fijo),
                })
                guardar_datos()
                st.success("Gasto fijo agregado.")
                st.rerun()

    if st.session_state.gastos_fijos:
        for fijo in st.session_state.gastos_fijos:
            dfm = movimientos_del_mes()
            pagado = (
                not dfm.empty and
                (dfm["Tipo"].eq("Gasto fijo") & dfm["Referencia"].eq(fijo["id"])).any()
            )
            x, y, z = st.columns([3, 1.2, 1])
            x.write(f"**{fijo['concepto']}** · {fijo['categoria']} · {moneda(fijo['monto'])}")
            y.write("🟢 Pagado este mes" if pagado else "🟠 Pendiente")
            if not pagado:
                if z.button("Marcar pagado", key=f"pagar_{fijo['id']}"):
                    registrar_movimiento(
                        "Gasto fijo", fijo["categoria"], fijo["concepto"],
                        fijo["monto"], date.today(), referencia=fijo["id"],
                    )
                    st.success("Gasto fijo marcado como pagado.")
                    st.rerun()
            else:
                if z.button("Eliminar", key=f"eliminar_fijo_{fijo['id']}"):
                    st.session_state.gastos_fijos = [
                        item for item in st.session_state.gastos_fijos
                        if item["id"] != fijo["id"]
                    ]
                    guardar_datos()
                    st.rerun()
    else:
        st.info("Todavía no has registrado gastos fijos.")
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# 8. MOVIMIENTOS
# ============================================================

elif seccion == "Movimientos":
    st.markdown('<div class="page-heading">Movimientos</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Registra tus ingresos, gastos, ahorros y entradas adicionales.</div>', unsafe_allow_html=True)

    tipo = st.selectbox(
        "Tipo de movimiento",
        ["Ingreso", "Ingreso extra", "Gasto", "Ahorro", "Retiro ahorro"],
        key="tipo_movimiento",
    )

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    with st.form("form_movimiento"):
        col_a, col_b = st.columns(2)
        with col_a:
            concepto = st.text_input(
                "Nombre o concepto",
                placeholder="Ej. Salario, compra de alimentos, horas extra",
                help="Describe brevemente el movimiento.",
            )
            fecha_mov = st.date_input("Fecha", value=date.today())
            if tipo == "Ingreso":
                categoria = st.selectbox(
                    "Categoría", ["Salario", "Trabajo habitual", "Comisiones", "Otros"]
                )
            elif tipo == "Ingreso extra":
                categoria = st.selectbox(
                    "Categoría", ["Horas extra", "Trabajo adicional", "Comisiones", "Otros"]
                )
            elif tipo == "Gasto":
                # Se conservan las categorías originales.
                categoria = st.selectbox("Categoría", CATEGORIAS_GASTO)
            else:
                categoria = "Ahorro" if tipo == "Ahorro" else "Retiro ahorro"

        with col_b:
            horas = None
            tarifa = None
            if tipo == "Ingreso extra":
                horas_in = st.number_input(
                    "Horas trabajadas (opcional)", min_value=0.0, step=0.5,
                    help="Cantidad de horas asociadas al ingreso extra.",
                )
                tarifa_in = st.number_input(
                    "Monto por hora ($, opcional)", min_value=0.0, step=1.0,
                    help="Si completas horas y tarifa, el total se calcula automáticamente.",
                )
                monto_manual = st.number_input(
                    "Monto total ($)", min_value=0.0, step=5.0,
                    help="Se utiliza cuando no introduces horas y tarifa.",
                )
                monto = horas_in * tarifa_in if horas_in > 0 and tarifa_in > 0 else monto_manual
                horas = float(horas_in) if horas_in > 0 else None
                tarifa = float(tarifa_in) if tarifa_in > 0 else None
                if horas_in > 0 and tarifa_in > 0:
                    st.info(f"Importe calculado: **{moneda(monto)}**")
            else:
                monto = st.number_input(
                    "Monto ($)", min_value=0.0, step=5.0,
                    help="El importe debe ser mayor que cero.",
                )

        guardar_movimiento = st.form_submit_button(
            "Guardar movimiento", type="primary", use_container_width=True
        )
        if guardar_movimiento:
            if not concepto.strip():
                st.error("Debes escribir el concepto del movimiento.")
            elif monto <= 0:
                st.error("El monto debe ser mayor que cero.")
            else:
                resumen = resumen_financiero()
                if tipo == "Retiro ahorro" and monto > ahorro_acumulado():
                    st.error("No puedes retirar más dinero del que tienes ahorrado.")
                elif tipo == "Ahorro" and monto > resumen["balance"]:
                    st.error("No puedes ahorrar más que tu balance disponible.")
                else:
                    registrar_movimiento(
                        tipo, categoria, concepto, monto, fecha_mov,
                        horas=horas, monto_hora=tarifa,
                    )
                    st.success("Movimiento registrado correctamente.")
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    if tipo == "Ingreso" and st.session_state.perfil:
        dias = st.session_state.perfil.get("dias_cobro", [])
        st.info(
            "Días habituales de cobro configurados: " + ", ".join(dias) +
            ". Utilízalos como guía al registrar la fecha del ingreso."
        )

# ============================================================
# 9. HISTORIAL
# ============================================================

elif seccion == "Historial":
    st.markdown('<div class="page-heading">Historial de movimientos</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Consulta, filtra y administra todos tus registros.</div>', unsafe_allow_html=True)

    historial = st.session_state.movimientos.copy()
    if historial.empty:
        st.info("Todavía no tienes movimientos registrados.")
    else:
        historial["Fecha"] = pd.to_datetime(historial["Fecha"], errors="coerce")
        f1, f2, f3 = st.columns(3)
        opciones_tipo = ["Todos"] + sorted(historial["Tipo"].dropna().unique().tolist())
        opciones_categoria = ["Todas"] + sorted(historial["Categoria"].dropna().unique().tolist())
        opciones_mes = ["Todos"] + sorted(
            historial["Fecha"].dropna().dt.strftime("%Y-%m").unique().tolist(),
            reverse=True,
        )
        filtro_tipo = f1.selectbox("Filtrar por tipo", opciones_tipo)
        filtro_categoria = f2.selectbox("Filtrar por categoría", opciones_categoria)
        filtro_mes = f3.selectbox("Filtrar por mes", opciones_mes)

        filtrado = historial.copy()
        if filtro_tipo != "Todos":
            filtrado = filtrado[filtrado["Tipo"] == filtro_tipo]
        if filtro_categoria != "Todas":
            filtrado = filtrado[filtrado["Categoria"] == filtro_categoria]
        if filtro_mes != "Todos":
            filtrado = filtrado[filtrado["Fecha"].dt.strftime("%Y-%m") == filtro_mes]

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Todos los movimientos</div>', unsafe_allow_html=True)
        st.dataframe(
            filtrado.sort_values("Fecha", ascending=False),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
                "Monto": st.column_config.NumberColumn("Monto", format="$%.2f"),
                "Monto_hora": st.column_config.NumberColumn("Monto por hora", format="$%.2f"),
                "Pagado": st.column_config.CheckboxColumn("Pagado"),
            },
        )
        st.caption(f"{len(filtrado)} movimiento(s) encontrados.")
        st.markdown('</div>', unsafe_allow_html=True)

        if not filtrado.empty:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">Eliminar un movimiento</div>', unsafe_allow_html=True)
            opciones_eliminar = {
                f"{pd.to_datetime(fila['Fecha']).strftime('%d/%m/%Y')} · "
                f"{fila['Tipo']} · {fila['Concepto']} · {moneda(fila['Monto'])}": fila["ID"]
                for _, fila in filtrado.iterrows()
            }
            etiqueta = st.selectbox("Selecciona el movimiento", list(opciones_eliminar.keys()))
            confirmar = st.checkbox("Confirmo que deseo eliminar este movimiento.")
            if st.button("Eliminar movimiento", disabled=not confirmar):
                id_eliminar = opciones_eliminar[etiqueta]
                st.session_state.movimientos = st.session_state.movimientos[
                    st.session_state.movimientos["ID"] != id_eliminar
                ].reset_index(drop=True)
                guardar_datos()
                st.success("Movimiento eliminado correctamente.")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# 10. PIE DE PÁGINA
# ============================================================

st.markdown("---")
st.caption(
    "Finanzly · Finanzas personales · Tus datos se guardan localmente en "
    "finanzly_datos.json. Conserva ese archivo para mantener tu información."
)
