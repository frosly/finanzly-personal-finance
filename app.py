# Finanzly - Finanzas personales
# ------------------------------------------------------------
# Instalación:
#   pip install streamlit pandas plotly
# Ejecución:
#   streamlit run app.py
#
# Los datos se guardan localmente en finanzly_datos.json.
# La fórmula del balance conserva la lógica original:
# ingresos + ingresos extra - gastos - aportes de ahorro + retiros.
# Los gastos fijos solo afectan el balance cuando se marcan como
# pagados en el mes. Los ingresos extra se contabilizan aparte.
# ------------------------------------------------------------

import json
import uuid
import calendar
from pathlib import Path
from datetime import date, datetime

import pandas as pd
import plotly.express as px
import streamlit as st

# =========================
# CONFIGURACIÓN GENERAL
# =========================

st.set_page_config(
    page_title="Finanzly | Finanzas personales",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

ARCHIVO_DATOS = Path("finanzly_datos.json")
MESES_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]
DIAS_ES = {
    "Lunes": 0, "Martes": 1, "Miércoles": 2, "Jueves": 3,
    "Viernes": 4, "Sábado": 5, "Domingo": 6
}
CATEGORIAS_GASTO = [
    "Ocio", "Comida", "Transporte", "Compras", "Otros",
    "Pagos y compromisos"
]
COLORES = {
    "Ingreso": "#42BFA5",
    "Ingreso extra": "#65A9D8",
    "Gasto fijo": "#EF718A",
    "Gasto": "#F5A34D",
    "Ahorro": "#4F80F5",
    "Retiro ahorro": "#9B8AFB",
}
COLUMNAS = [
    "ID", "Fecha", "Tipo", "Categoria", "Concepto", "Monto",
    "Horas", "Monto_hora", "Pagado"
]

# =========================
# ESTILOS
# =========================

st.markdown("""
<style>
.stApp { background-color: #F4F7FC; }
.block-container { padding-top: 1.6rem; max-width: 1500px; }
h1, h2, h3, h4 { color: #172B4D; }
p, label, .stMarkdown { color: #344563; }
div[data-testid="stMetric"] {
    background: #FFFFFF; padding: 17px 19px; border-radius: 16px;
    border: 1px solid #E5EAF2; box-shadow: 0 4px 15px rgba(23,43,77,.055);
}
div[data-testid="stMetric"] label { color: #62718A; }
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #172B4D; font-weight: 700;
}
.finanzly-card {
    background: white; border: 1px solid #E5EAF2; border-radius: 18px;
    padding: 18px 21px; box-shadow: 0 5px 18px rgba(23,43,77,.055);
    margin-bottom: 10px;
}
.finanzly-muted { color: #718096; font-size: .92rem; }
.finanzly-positive { color: #16845B; font-weight: 700; }
.finanzly-negative { color: #C0394B; font-weight: 700; }
.stButton button, .stFormSubmitButton button {
    border-radius: 10px; font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# =========================
# PERSISTENCIA Y ESTADO
# =========================

def dataframe_vacio():
    return pd.DataFrame(columns=COLUMNAS)

def cargar_datos():
    """Carga los datos locales; si el archivo no existe, inicia vacío."""
    if ARCHIVO_DATOS.exists():
        try:
            with ARCHIVO_DATOS.open("r", encoding="utf-8") as archivo:
                datos = json.load(archivo)
            movimientos = pd.DataFrame(datos.get("movimientos", []))
            fijos = datos.get("gastos_fijos", [])
            perfil = datos.get("perfil", {})
            if movimientos.empty:
                movimientos = dataframe_vacio()
            else:
                for columna in COLUMNAS:
                    if columna not in movimientos.columns:
                        movimientos[columna] = None
                movimientos = movimientos[COLUMNAS]
            return perfil, movimientos, fijos
        except (json.JSONDecodeError, OSError, ValueError):
            st.warning("No se pudo leer el archivo local. Se iniciará una sesión nueva.")
    return {}, dataframe_vacio(), []

def guardar_datos():
    """Guarda perfil, movimientos y gastos recurrentes en un JSON local."""
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

if "perfil" not in st.session_state:
    perfil, movimientos, fijos = cargar_datos()
    st.session_state.perfil = perfil
    st.session_state.movimientos = movimientos
    st.session_state.gastos_fijos = fijos

if "movimientos" not in st.session_state:
    st.session_state.movimientos = dataframe_vacio()
if "gastos_fijos" not in st.session_state:
    st.session_state.gastos_fijos = []

# Normalizar tipos tras cargar JSON
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

# =========================
# FUNCIONES AUXILIARES
# =========================

def dinero(valor):
    return f"${float(valor):,.2f}"

def mes_actual_texto():
    hoy = date.today()
    return f"{MESES_ES[hoy.month - 1].capitalize()} de {hoy.year}"

def ocurrencias_dias_mes(dias_seleccionados, anio=None, mes=None):
    """Cuenta cuántas veces aparece cada día elegido en el mes indicado."""
    hoy = date.today()
    anio = anio or hoy.year
    mes = mes or hoy.month
    total_dias = calendar.monthrange(anio, mes)[1]
    elegidos = {DIAS_ES[d] for d in dias_seleccionados if d in DIAS_ES}
    return sum(
        1 for numero in range(1, total_dias + 1)
        if date(anio, mes, numero).weekday() in elegidos
    )

def agregar_movimiento(tipo, categoria, concepto, monto, fecha_mov,
                       horas=None, monto_hora=None, pagado=True):
    nuevo = {
        "ID": str(uuid.uuid4()),
        "Fecha": pd.Timestamp(fecha_mov),
        "Tipo": tipo,
        "Categoria": categoria,
        "Concepto": concepto.strip(),
        "Monto": float(monto),
        "Horas": horas,
        "Monto_hora": monto_hora,
        "Pagado": bool(pagado),
    }
    st.session_state.movimientos = pd.concat(
        [st.session_state.movimientos, pd.DataFrame([nuevo])],
        ignore_index=True,
    )
    guardar_datos()

def movimientos_mes():
    df = st.session_state.movimientos.copy()
    if df.empty:
        return df
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    hoy = date.today()
    return df[
        (df["Fecha"].dt.month == hoy.month) &
        (df["Fecha"].dt.year == hoy.year)
    ].copy()

def calcular_resumen():
    """Calcula el resumen del mes sin mezclar el ahorro con los gastos."""
    df = movimientos_mes()
    if df.empty:
        df = dataframe_vacio()

    ingresos = df.loc[df["Tipo"] == "Ingreso", "Monto"].sum()
    extras = df.loc[df["Tipo"] == "Ingreso extra", "Monto"].sum()
    gastos_variables = df.loc[df["Tipo"] == "Gasto", "Monto"].sum()
    gastos_fijos_pagados = df.loc[
        (df["Tipo"] == "Gasto fijo") & (df["Pagado"] == True), "Monto"
    ].sum()
    aportes = df.loc[df["Tipo"] == "Ahorro", "Monto"].sum()
    retiros = df.loc[df["Tipo"] == "Retiro ahorro", "Monto"].sum()

    gastos_totales = gastos_variables + gastos_fijos_pagados
    ahorro_neto_mes = aportes - retiros
    balance = ingresos + extras - gastos_totales - aportes + retiros
    return {
        "ingresos": float(ingresos),
        "extras": float(extras),
        "gastos_variables": float(gastos_variables),
        "gastos_fijos": float(gastos_fijos_pagados),
        "gastos": float(gastos_totales),
        "aportes": float(aportes),
        "retiros": float(retiros),
        "ahorro_neto": float(ahorro_neto_mes),
        "balance": float(balance),
    }

def total_ahorro_historico():
    df = st.session_state.movimientos
    if df.empty:
        return 0.0
    aportes = df.loc[df["Tipo"] == "Ahorro", "Monto"].sum()
    retiros = df.loc[df["Tipo"] == "Retiro ahorro", "Monto"].sum()
    return float(aportes - retiros)

def perfil_estimado():
    perfil = st.session_state.perfil
    if not perfil:
        return 0, 0
    dias = ocurrencias_dias_mes(perfil.get("dias_cobro", []))
    ingreso = float(perfil.get("monto_por_dia", 0)) * dias
    if perfil.get("tipo_ahorro") == "Monto fijo":
        ahorro = float(perfil.get("ahorro_objetivo", 0))
    else:
        ahorro = ingreso * float(perfil.get("ahorro_porcentaje", 0)) / 100
    return ingreso, ahorro

def mes_clave_actual():
    hoy = date.today()
    return f"{hoy.year}-{hoy.month:02d}"

# =========================
# ENCABEZADO Y NAVEGACIÓN
# =========================

perfil = st.session_state.perfil
nombre = perfil.get("nombre", "").strip() if perfil else ""
st.title("💰 Finanzly")
st.caption("Tu dinero, organizado inteligentemente.")

if perfil:
    estimado, ahorro_estimado = perfil_estimado()
    st.markdown(
        f"""<div class="finanzly-card">
        <b>Perfil de {nombre}</b> &nbsp;·&nbsp; Cobro por día:
        <b>{dinero(perfil.get('monto_por_dia', 0))}</b>
        &nbsp;·&nbsp; Días seleccionados: <b>{', '.join(perfil.get('dias_cobro', []))}</b>
        &nbsp;·&nbsp; Ingreso mensual estimado: <b>{dinero(estimado)}</b>
        </div>""",
        unsafe_allow_html=True,
    )

pestana_perfil, pestana_dashboard, pestana_movimientos, pestana_historial = st.tabs(
    ["👤 Mi perfil", "📊 Dashboard", "➕ Movimientos", "📚 Historial"]
)

# =========================
# PESTAÑA: PERFIL
# =========================

with pestana_perfil:
    st.subheader("Configura tu perfil de cobro")
    st.caption(
        "Finanzly utiliza días de la semana (por ejemplo, lunes y viernes). "
        "Así cuenta automáticamente cuántas veces cae cada día en el mes actual."
    )

    dias_default = perfil.get("dias_cobro", ["Viernes"]) if perfil else ["Viernes"]
    opciones_dias = list(DIAS_ES.keys())

    with st.form("form_perfil"):
        nombre_nuevo = st.text_input(
            "Nombre", value=perfil.get("nombre", "") if perfil else "",
            help="Se utilizará para personalizar el saludo del dashboard."
        )
        dias_nuevos = st.multiselect(
            "¿Qué días recibes tu pago?",
            opciones_dias,
            default=[d for d in dias_default if d in opciones_dias],
            help="Selecciona todos los días de la semana en los que normalmente cobras."
        )
        monto_dia = st.number_input(
            "¿Cuánto cobras por cada día de trabajo? ($)",
            min_value=0.0, value=float(perfil.get("monto_por_dia", 0)) if perfil else 0.0,
            step=5.0, help="Importe que recibes por cada día de cobro seleccionado."
        )
        tipo_ahorro = st.radio(
            "¿Cómo deseas establecer tu ahorro mensual?",
            ["Porcentaje", "Monto fijo"],
            horizontal=True,
            index=0 if not perfil or perfil.get("tipo_ahorro", "Porcentaje") == "Porcentaje" else 1,
            help="Puedes definir una parte porcentual de tu ingreso estimado o una cantidad fija."
        )
        if tipo_ahorro == "Porcentaje":
            ahorro_porcentaje = st.number_input(
                "Porcentaje que deseas ahorrar (%)",
                min_value=0.0, max_value=100.0,
                value=float(perfil.get("ahorro_porcentaje", 10)) if perfil else 10.0,
                step=1.0, help="Porcentaje aplicado al ingreso mensual estimado."
            )
            ahorro_objetivo = 0.0
        else:
            ahorro_objetivo = st.number_input(
                "Monto de ahorro mensual ($)", min_value=0.0,
                value=float(perfil.get("ahorro_objetivo", 0)) if perfil else 0.0,
                step=5.0, help="Cantidad fija que te gustaría separar cada mes."
            )
            ahorro_porcentaje = 0.0

        guardar_perfil = st.form_submit_button(
            "Guardar mi perfil", use_container_width=True
        )

        if guardar_perfil:
            if not nombre_nuevo.strip():
                st.error("Escribe tu nombre para guardar el perfil.")
            elif not dias_nuevos:
                st.error("Selecciona al menos un día de cobro.")
            elif monto_dia <= 0:
                st.error("El monto por día debe ser mayor que cero.")
            else:
                st.session_state.perfil = {
                    "nombre": nombre_nuevo.strip(),
                    "dias_cobro": dias_nuevos,
                    "monto_por_dia": float(monto_dia),
                    "tipo_ahorro": tipo_ahorro,
                    "ahorro_porcentaje": float(ahorro_porcentaje),
                    "ahorro_objetivo": float(ahorro_objetivo),
                }
                guardar_datos()
                st.success("Perfil guardado correctamente.")
                st.rerun()

    if st.session_state.perfil:
        estimado, ahorro_estimado = perfil_estimado()
        dias = ocurrencias_dias_mes(st.session_state.perfil["dias_cobro"])
        a, b, c = st.columns(3)
        a.metric("Días de cobro este mes", dias)
        b.metric("Ingreso mensual estimado", dinero(estimado))
        c.metric("Ahorro mensual estimado", dinero(ahorro_estimado))

    st.divider()
    st.subheader("Mis gastos fijos recurrentes")
    st.caption(
        "Registra aquí compromisos mensuales. Después podrás marcarlos como pagados "
        "para que se contabilicen en el balance del mes."
    )

    with st.form("nuevo_gasto_fijo"):
        cf1, cf2 = st.columns(2)
        with cf1:
            fijo_concepto = st.text_input(
                "Nombre del gasto fijo", placeholder="Ej. Renta, internet, transporte"
            )
            fijo_categoria = st.selectbox(
                "Categoría del gasto fijo",
                ["Vivienda", "Servicios", "Transporte", "Educación", "Otros"]
            )
        with cf2:
            fijo_monto = st.number_input(
                "Monto mensual ($)", min_value=0.0, step=5.0,
                help="Importe que debes pagar cada mes."
            )
        crear_fijo = st.form_submit_button("Agregar gasto fijo")
        if crear_fijo:
            if not fijo_concepto.strip():
                st.error("Escribe el nombre del gasto fijo.")
            elif fijo_monto <= 0:
                st.error("El monto debe ser mayor que cero.")
            else:
                st.session_state.gastos_fijos.append({
                    "id": str(uuid.uuid4()),
                    "concepto": fijo_concepto.strip(),
                    "categoria": fijo_categoria,
                    "monto": float(fijo_monto),
                })
                guardar_datos()
                st.success("Gasto fijo agregado.")
                st.rerun()

    if st.session_state.gastos_fijos:
        for fijo in st.session_state.gastos_fijos:
            ya_pagado = not movimientos_mes().empty and (
                (movimientos_mes()["Tipo"] == "Gasto fijo") &
                (movimientos_mes()["Concepto"] == fijo["concepto"]) &
                (movimientos_mes()["Categoria"] == fijo["categoria"])
            ).any()
            col_info, col_estado, col_accion = st.columns([4, 2, 2])
            col_info.write(
                f"**{fijo['concepto']}** · {fijo['categoria']} · {dinero(fijo['monto'])}"
            )
            col_estado.write("🟢 Pagado este mes" if ya_pagado else "🟠 Pendiente")
            if not ya_pagado:
                if col_accion.button("Marcar pagado", key=f"pagar_{fijo['id']}"):
                    agregar_movimiento(
                        "Gasto fijo", fijo["categoria"], fijo["concepto"],
                        fijo["monto"], date.today(), pagado=True
                    )
                    st.success("Gasto fijo marcado como pagado.")
                    st.rerun()
            else:
                if col_accion.button("Quitar gasto", key=f"quitar_{fijo['id']}"):
                    st.session_state.gastos_fijos = [
                        x for x in st.session_state.gastos_fijos if x["id"] != fijo["id"]
                    ]
                    guardar_datos()
                    st.rerun()
    else:
        st.info("Todavía no has agregado gastos fijos.")

# =========================
# PESTAÑA: DASHBOARD
# =========================

with pestana_dashboard:
    if not st.session_state.perfil:
        st.info("Primero completa y guarda tu perfil en la pestaña «Mi perfil».")
    else:
        resumen = calcular_resumen()
        estimado, ahorro_estimado = perfil_estimado()
        st.subheader(f"¡Hola, {st.session_state.perfil['nombre']}! 👋")
        st.caption(f"Este es tu resumen financiero de {mes_actual_texto()}.")

        m1, m2, m3 = st.columns(3)
        m1.metric("Ingreso percibido", dinero(resumen["ingresos"]))
        m2.metric("Gastos fijos pagados", dinero(resumen["gastos_fijos"]))
        m3.metric("Gastos variables", dinero(resumen["gastos_variables"]))
        m4, m5, m6 = st.columns(3)
        m4.metric("Ahorro neto del mes", dinero(resumen["ahorro_neto"]))
        m5.metric("Ingreso extra", dinero(resumen["extras"]))
        m6.metric("Balance disponible", dinero(resumen["balance"]))

        st.markdown("#### Progreso de ingresos del mes")
        porcentaje = min(resumen["ingresos"] / estimado, 1.0) if estimado > 0 else 0.0
        st.progress(porcentaje)
        st.caption(
            f"{dinero(resumen['ingresos'])} percibidos de {dinero(estimado)} estimados "
            f"({porcentaje * 100:.1f} %)."
        )

        if resumen["gastos"] > resumen["ingresos"] + resumen["extras"]:
            st.error("Atención: tus gastos del mes superan los ingresos percibidos y extras.")
        elif resumen["balance"] >= 0:
            st.success("Tu balance está en positivo. ¡Sigue organizando tus finanzas!")
        else:
            st.error("Tu balance disponible está por debajo de cero.")

        st.divider()
        st.subheader("Análisis financiero del mes")
        izquierda, derecha = st.columns(2)

        with izquierda:
            st.markdown("#### ¿En qué se distribuyó tu dinero?")
            gastado = resumen["gastos"]
            ahorrado = max(resumen["ahorro_neto"], 0)
            disponible = max(
                resumen["ingresos"] + resumen["extras"] - gastado - ahorrado, 0
            )
            valores = [
                ("Gastos", gastado),
                ("Ahorro neto", ahorrado),
                ("Disponible", disponible),
            ]
            donut_df = pd.DataFrame(valores, columns=["Destino", "Monto"])
            donut_df = donut_df[donut_df["Monto"] > 0]
            if not donut_df.empty:
                fig = px.pie(
                    donut_df, names="Destino", values="Monto", hole=0.62,
                    color="Destino",
                    color_discrete_map={
                        "Gastos": "#EF718A",
                        "Ahorro neto": "#4F80F5",
                        "Disponible": "#42BFA5",
                    },
                )
                fig.update_traces(
                    textposition="inside", textinfo="label+percent",
                    hovertemplate="%{label}: $%{value:,.2f}<extra></extra>"
                )
                fig.update_layout(
                    showlegend=True, margin=dict(t=15, b=15, l=5, r=5),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Todavía no hay ingresos, gastos ni ahorros para mostrar.")

        with derecha:
            st.markdown("#### Ingresos, gastos y ahorros por mes")
            todo = st.session_state.movimientos.copy()
            if not todo.empty:
                todo["Fecha"] = pd.to_datetime(todo["Fecha"], errors="coerce")
                todo["Mes"] = todo["Fecha"].dt.strftime("%Y-%m")
                agrupado = todo.groupby(["Mes", "Tipo"])["Monto"].sum().reset_index()
                agrupado = agrupado[
                    agrupado["Tipo"].isin(["Ingreso", "Ingreso extra", "Gasto", "Gasto fijo", "Ahorro"])
                ]
                if not agrupado.empty:
                    fig2 = px.bar(
                        agrupado, x="Mes", y="Monto", color="Tipo",
                        barmode="group", color_discrete_map=COLORES,
                        labels={"Mes": "Mes", "Monto": "Monto ($)", "Tipo": "Movimiento"}
                    )
                    fig2.update_layout(
                        margin=dict(t=15, b=15, l=5, r=5),
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info("Aún no hay movimientos para comparar.")
            else:
                st.info("Registra movimientos para visualizar la gráfica.")

        st.markdown("#### Evolución del balance durante el mes")
        df_mes = movimientos_mes()
        if not df_mes.empty:
            df_mes["Fecha"] = pd.to_datetime(df_mes["Fecha"], errors="coerce")
            df_mes = df_mes.sort_values("Fecha")
            df_mes["Impacto"] = df_mes.apply(
                lambda fila:
                    fila["Monto"] if fila["Tipo"] in ["Ingreso", "Ingreso extra", "Retiro ahorro"]
                    else -fila["Monto"] if fila["Tipo"] in ["Gasto", "Gasto fijo", "Ahorro"]
                    else 0,
                axis=1,
            )
            df_mes["Balance"] = df_mes["Impacto"].cumsum()
            evolucion = df_mes.groupby(df_mes["Fecha"].dt.date)["Balance"].last().reset_index()
            evolucion.columns = ["Día", "Balance"]
            fig3 = px.line(
                evolucion, x="Día", y="Balance", markers=True,
                labels={"Día": "Día", "Balance": "Balance ($)"}
            )
            fig3.update_traces(line=dict(color="#4F80F5", width=3))
            fig3.update_layout(
                margin=dict(t=15, b=15, l=5, r=5),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("La evolución aparecerá cuando registres movimientos.")

# =========================
# PESTAÑA: MOVIMIENTOS
# =========================

with pestana_movimientos:
    st.subheader("Registrar un movimiento")
    st.caption("Registra tus cobros, gastos, aportes de ahorro, retiros e ingresos extra.")

    tipo_mov = st.selectbox(
        "Tipo de movimiento",
        ["Ingreso", "Ingreso extra", "Gasto", "Ahorro", "Retiro ahorro"],
        key="tipo_movimiento"
    )

    with st.form("form_movimiento"):
        col_a, col_b = st.columns(2)
        with col_a:
            concepto = st.text_input(
                "Concepto", placeholder="Ej. Pago semanal, compra de alimentos",
                help="Describe brevemente el movimiento."
            )
            fecha_mov = st.date_input(
                "Fecha del movimiento", value=date.today(),
                help="Para ingresos, se muestran como guía los días de cobro definidos en tu perfil."
            )
            if tipo_mov == "Ingreso":
                categoria = st.selectbox(
                    "Categoría", ["Salario", "Pago habitual", "Comisiones", "Otros"]
                )
            elif tipo_mov == "Ingreso extra":
                categoria = st.selectbox(
                    "Tipo de ingreso extra", ["Horas extra", "Trabajo adicional", "Comisiones", "Otros"]
                )
            elif tipo_mov == "Gasto":
                categoria = st.selectbox("Categoría de gasto", CATEGORIAS_GASTO)
            else:
                categoria = "Ahorro" if tipo_mov == "Ahorro" else "Retiro de ahorro"

        with col_b:
            horas = None
            monto_hora = None
            if tipo_mov == "Ingreso extra":
                horas_op = st.number_input(
                    "Horas (opcional)", min_value=0.0, step=0.5,
                    help="Cantidad de horas trabajadas para este ingreso extra."
                )
                tarifa_op = st.number_input(
                    "Monto por hora ($, opcional)", min_value=0.0, step=1.0,
                    help="Si introduces horas y tarifa, Finanzly calcula el total automáticamente."
                )
                monto_manual = st.number_input(
                    "Monto total ($)", min_value=0.0, step=5.0,
                    help="Si indicas horas y tarifa, este campo se reemplaza por el cálculo."
                )
                if horas_op > 0 and tarifa_op > 0:
                    monto = horas_op * tarifa_op
                    st.info(f"Total calculado: **{dinero(monto)}**")
                    horas, monto_hora = float(horas_op), float(tarifa_op)
                else:
                    monto = monto_manual
                    horas = float(horas_op) if horas_op > 0 else None
                    monto_hora = float(tarifa_op) if tarifa_op > 0 else None
            else:
                monto = st.number_input(
                    "Monto ($)", min_value=0.0, step=5.0,
                    help="Introduce una cantidad mayor que cero."
                )

        enviar = st.form_submit_button("Guardar movimiento", use_container_width=True)

        if enviar:
            if not concepto.strip():
                st.error("Debes escribir el concepto del movimiento.")
            elif monto <= 0:
                st.error("El monto debe ser mayor que cero.")
            else:
                resumen = calcular_resumen()
                if tipo_mov == "Retiro ahorro" and monto > total_ahorro_historico():
                    st.error("No puedes retirar más dinero del que tienes ahorrado.")
                elif tipo_mov == "Ahorro" and monto > resumen["balance"]:
                    st.error("No puedes ahorrar más que tu balance disponible.")
                else:
                    agregar_movimiento(
                        tipo_mov, categoria, concepto, monto, fecha_mov,
                        horas=horas, monto_hora=monto_hora, pagado=True
                    )
                    st.success("Movimiento registrado correctamente.")
                    st.rerun()

    if st.session_state.perfil:
        dias = st.session_state.perfil.get("dias_cobro", [])
        st.info(
            "Días de cobro configurados: " + ", ".join(dias) +
            ". Úsalos como referencia al registrar tus ingresos."
        )

# =========================
# PESTAÑA: HISTORIAL
# =========================

with pestana_historial:
    st.subheader("Historial de movimientos")
    df_hist = st.session_state.movimientos.copy()

    if df_hist.empty:
        st.info("Todavía no tienes movimientos registrados.")
    else:
        df_hist["Fecha"] = pd.to_datetime(df_hist["Fecha"], errors="coerce")
        f1, f2, f3 = st.columns(3)
        tipos_disponibles = ["Todos"] + sorted(df_hist["Tipo"].dropna().unique().tolist())
        filtro_tipo = f1.selectbox("Filtrar por tipo", tipos_disponibles)
        categorias_disponibles = ["Todas"] + sorted(
            df_hist["Categoria"].dropna().unique().tolist()
        )
        filtro_categoria = f2.selectbox("Filtrar por categoría", categorias_disponibles)
        filtro_mes = f3.selectbox(
            "Filtrar por mes",
            ["Todos"] + sorted(
                df_hist["Fecha"].dropna().dt.strftime("%Y-%m").unique().tolist(),
                reverse=True
            )
        )

        filtrado = df_hist.copy()
        if filtro_tipo != "Todos":
            filtrado = filtrado[filtrado["Tipo"] == filtro_tipo]
        if filtro_categoria != "Todas":
            filtrado = filtrado[filtrado["Categoria"] == filtro_categoria]
        if filtro_mes != "Todos":
            filtrado = filtrado[filtrado["Fecha"].dt.strftime("%Y-%m") == filtro_mes]

        st.dataframe(
            filtrado.sort_values("Fecha", ascending=False),
            use_container_width=True, hide_index=True,
            column_config={
                "Monto": st.column_config.NumberColumn("Monto", format="$%.2f"),
                "Monto_hora": st.column_config.NumberColumn("Monto por hora", format="$%.2f"),
                "Fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
                "Pagado": st.column_config.CheckboxColumn("Pagado"),
            },
        )
        st.caption(f"{len(filtrado)} movimiento(s) encontrados.")

        st.markdown("#### Eliminar un movimiento")
        opciones = {
            f"{pd.to_datetime(fila['Fecha']).strftime('%d/%m/%Y')} · {fila['Tipo']} · "
            f"{fila['Concepto']} · {dinero(fila['Monto'])} · {fila['ID'][:8]}": fila["ID"]
            for _, fila in filtrado.iterrows()
        }
        if opciones:
            seleccion = st.selectbox("Selecciona el movimiento que deseas eliminar", list(opciones))
            confirmar = st.checkbox(
                "Confirmo que deseo eliminar este movimiento.",
                help="La eliminación no se puede deshacer."
            )
            if st.button("Eliminar movimiento", type="secondary", disabled=not confirmar):
                identificador = opciones[seleccion]
                st.session_state.movimientos = st.session_state.movimientos[
                    st.session_state.movimientos["ID"] != identificador
                ].reset_index(drop=True)
                guardar_datos()
                st.success("Movimiento eliminado.")
                st.rerun()

# =========================
# PIE DE PÁGINA
# =========================

st.divider()
st.caption(
    "Finanzly · Tus datos se guardan en finanzly_datos.json en la misma carpeta "
    "donde ejecutas la aplicación. Haz una copia de seguridad de ese archivo."
)
