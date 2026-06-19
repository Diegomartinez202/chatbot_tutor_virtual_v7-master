import json
import os
import pandas as pd
import streamlit as st
import altair as alt

DATA_FILE = os.path.join(os.path.dirname(__file__), "../data/encuestas.json")

st.set_page_config(page_title="Panel de Satisfacción", layout="wide")

st.title("📊 Panel de Encuestas de Satisfacción")

def cargar_encuestas():
    if not os.path.exists(DATA_FILE):
        st.warning("⚠️ No se encontró el archivo de encuestas.")
        return pd.DataFrame()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data)

df = cargar_encuestas()

if df.empty:
    st.stop()

col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Distribución de satisfacción")
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x="nivel_satisfaccion:N",
            y="count():Q",
            color="nivel_satisfaccion:N",
            tooltip=["nivel_satisfaccion", "count()"]
        )
        .properties(height=300)
    )
    st.altair_chart(chart, use_container_width=True)

with col2:
    st.subheader("💬 Comentarios recientes")
    for _, row in df.tail(5).iterrows():
        st.info(f"**{row['usuario']}**: {row['comentario']}")

st.divider()
st.subheader("🔍 Filtrar por nivel de satisfacción")

niveles = df["nivel_satisfaccion"].unique().tolist()
nivel_sel = st.selectbox("Seleccione un nivel:", ["Todos"] + niveles)

if nivel_sel != "Todos":
    df = df[df["nivel_satisfaccion"] == nivel_sel]

st.dataframe(df, use_container_width=True)

if st.button("📤 Exportar a CSV"):
    df.to_csv("encuestas_export.csv", index=False)
    st.success("Archivo exportado como encuestas_export.csv ✅")
