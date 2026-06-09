import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Dashboard de Vendas Automotivas", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("dados_vendas.csv", parse_dates=["data"])
    return df

df = load_data()
vendidos = df[df["status"] == "Vendido"]

# ── Título ────────────────────────────────────────────────────────────────────
st.title("Dashboard de Vendas Automotivas")
st.divider()

# ── KPIs ──────────────────────────────────────────────────────────────────────
total_vendas = len(vendidos)
receita_total = vendidos["valor"].sum()
ticket_medio = vendidos["valor"].mean()

col1, col2, col3 = st.columns(3)
col1.metric("Total de Vendas", f"{total_vendas}")
col2.metric("Receita Total", f"R$ {receita_total:,.0f}".replace(",", "."))
col3.metric("Ticket Médio", f"R$ {ticket_medio:,.0f}".replace(",", "."))

st.divider()

# ── Gráficos ──────────────────────────────────────────────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Ranking de Vendedores")
    ranking = (
        vendidos.groupby("vendedor")
        .size()
        .sort_values(ascending=True)
        .reset_index(name="vendas")
    )
    fig_vend = px.bar(
        ranking,
        x="vendas",
        y="vendedor",
        orientation="h",
        text="vendas",
        color="vendas",
        color_continuous_scale="Blues",
    )
    fig_vend.update_traces(textposition="outside")
    fig_vend.update_layout(
        showlegend=False,
        coloraxis_showscale=False,
        xaxis_title="Quantidade de Vendas",
        yaxis_title=None,
        margin=dict(l=0, r=20, t=10, b=0),
    )
    st.plotly_chart(fig_vend, use_container_width=True)

with col_b:
    st.subheader("Modelos Mais Vendidos")
    modelos = (
        vendidos.groupby("modelo")
        .size()
        .sort_values(ascending=True)
        .reset_index(name="vendas")
    )
    fig_mod = px.bar(
        modelos,
        x="vendas",
        y="modelo",
        orientation="h",
        text="vendas",
        color="vendas",
        color_continuous_scale="Teal",
    )
    fig_mod.update_traces(textposition="outside")
    fig_mod.update_layout(
        showlegend=False,
        coloraxis_showscale=False,
        xaxis_title="Quantidade de Vendas",
        yaxis_title=None,
        margin=dict(l=0, r=20, t=10, b=0),
    )
    st.plotly_chart(fig_mod, use_container_width=True)

st.divider()

# ── Tabela de dados ────────────────────────────────────────────────────────────
with st.expander("Ver dados completos"):
    st.dataframe(
        df.sort_values("data", ascending=False),
        use_container_width=True,
        hide_index=True,
    )
