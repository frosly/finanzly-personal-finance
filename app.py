
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

st.set_page_config(
    page_title="Finanzly | Finanzas personales",
    page_icon="💰",
    layout="wide"
)

# -------------------------
# DISEÑO
# -------------------------

st.markdown("""
<style>
.stApp {
    background-color: #F4F7FC;
}
.block-container {
    padding-top: 2rem;
    max-width: 1450px;
}
h1, h2, h3 {
    color: #172B4D;
}
div[data-testid="stMetric"] {
    background: white;
    padding: 20px;
    border-radius: 15px;
    border: 1px solid #E5EAF2;
}
</style>
""", unsafe_allow_html=True)

# -------------------------
# DATOS INICIALES
# -------------------------

if "movimientos" not in st.session_state:
    st.session_state.movimientos = pd.DataFrame(
        columns=[
            "Fecha", "Tipo", "Categoria",
            "Concepto", "Monto"
        ]
    )

df = st.session_state.movimientos.copy()

# -------------------------
# CALCULOS FINANCIEROS
# -------------------------

ingresos = df.loc[
    df["Tipo"] == "Ingreso", "Monto"
].sum()

gastos = df.loc[
    df["Tipo"] == "Gasto", "Monto"
].sum()

ahorros_ingresados = df.loc[
    df["Tipo"] == "Ahorro", "Monto"
].sum()

retiros = df.loc[
    df["Tipo"] == "Retiro ahorro", "Monto"
].sum()

ahorro_actual = ahorros_ingresados - retiros

balance = ingresos - gastos - ahorros_ingresados + retiros

# -------------------------
# ENCABEZADO
# -------------------------

st.title("💰 Finanzly")
st.caption("Tu dinero, organizado inteligentemente.")

st.divider()

# -------------------------
# INDICADORES
# -------------------------

c1, c2, c3, c4 = st.columns(4)

c1.metric("Balance disponible", f"${balance:,.2f}")
c2.metric("Ingresos", f"${ingresos:,.2f}")
c3.metric("Gastos", f"${gastos:,.2f}")
c4.metric("Ahorro acumulado", f"${ahorro_actual:,.2f}")

st.divider()

# -------------------------
# REGISTRAR MOVIMIENTOS
# -------------------------

st.subheader("Registrar movimiento")

with st.form("nuevo_movimiento"):

    col1, col2 = st.columns(2)

    with col1:
        tipo = st.selectbox(
            "Tipo de movimiento",
            [
                "Ingreso",
                "Gasto",
                "Ahorro",
                "Retiro ahorro"
            ]
        )

        concepto = st.text_input(
            "Nombre del movimiento",
            placeholder="Ej. Salario, alquiler..."
        )

        fecha = st.date_input(
            "Fecha",
            value=date.today()
        )

    with col2:

        if tipo == "Ingreso":
            categoria = st.selectbox(
                "Categoría",
                ["Salario", "Trabajo extra", "Comisiones", "Otros"]
            )

        elif tipo == "Gasto":
            categoria = st.selectbox(
                "Categoría",
                [
                    "Gastos fijos",
                    "Pagos y compromisos",
                    "Ocio",
                    "Comida",
                    "Transporte",
                    "Compras",
                    "Otros"
                ]
            )

        else:
            categoria = "Ahorro"

        monto = st.number_input(
            "Monto ($)",
            min_value=0.01,
            step=10.0
        )

    guardar = st.form_submit_button(
        "Guardar movimiento",
        use_container_width=True
    )

    if guardar:

        if concepto.strip():

            if tipo == "Retiro ahorro" and monto > ahorro_actual:
                st.error("No tienes suficiente dinero ahorrado.")

            elif tipo == "Ahorro" and monto > balance:
                st.error("No tienes suficiente balance disponible.")

            else:
                nuevo = pd.DataFrame([{
                    "Fecha": pd.Timestamp(fecha),
                    "Tipo": tipo,
                    "Categoria": categoria,
                    "Concepto": concepto,
                    "Monto": monto
                }])

                st.session_state.movimientos = pd.concat(
                    [st.session_state.movimientos, nuevo],
                    ignore_index=True
                )

                st.success("Movimiento registrado correctamente.")
                st.rerun()

        else:
            st.warning("Debes escribir el nombre del movimiento.")

st.divider()

# -------------------------
# GRAFICAS
# -------------------------

st.subheader("Análisis financiero")

df = st.session_state.movimientos.copy()

col1, col2 = st.columns(2)

with col1:

    st.markdown("#### Distribución de gastos")

    gastos_df = df[df["Tipo"] == "Gasto"]

    if not gastos_df.empty:

        resumen = gastos_df.groupby(
            "Categoria"
        )["Monto"].sum().reset_index()

        fig = px.pie(
            resumen,
            names="Categoria",
            values="Monto",
            hole=0.62,
            color_discrete_sequence=[
                "#4F80F5",
                "#9B8AFB",
                "#F5A34D",
                "#42BFA5",
                "#EF718A",
                "#65A9D8"
            ]
        )

        fig.update_layout(
            showlegend=True,
            margin=dict(t=20, b=20, l=10, r=10)
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("Registra gastos para visualizar la gráfica.")

with col2:

    st.markdown("#### Ingresos, gastos y ahorros")

    if not df.empty:

        df["Fecha"] = pd.to_datetime(df["Fecha"])

        df["Mes"] = df["Fecha"].dt.to_period(
            "M"
        ).astype(str)

        df["Ingreso"] = df["Monto"].where(
            df["Tipo"] == "Ingreso", 0
        )

        df["Gasto"] = df["Monto"].where(
            df["Tipo"] == "Gasto", 0
        )

        df["Ahorro"] = df["Monto"].where(
            df["Tipo"] == "Ahorro", 0
        )

        mensual = df.groupby("Mes")[
            ["Ingreso", "Gasto", "Ahorro"]
        ].sum().reset_index()

        fig2 = px.bar(
            mensual,
            x="Mes",
            y=["Ingreso", "Gasto", "Ahorro"],
            barmode="group",
            color_discrete_map={
                "Ingreso": "#42BFA5",
                "Gasto": "#EF718A",
                "Ahorro": "#4F80F5"
            }
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

    else:
        st.info("Registra movimientos para visualizar los resultados.")

st.divider()

# -------------------------
# HISTORIAL
# -------------------------

st.subheader("Historial de movimientos")

if not df.empty:

    historial = df.sort_values(
        "Fecha", ascending=False
    )

    st.dataframe(
        historial,
        use_container_width=True,
        hide_index=True
    )

else:
    st.info("Todavía no tienes movimientos registrados.")
