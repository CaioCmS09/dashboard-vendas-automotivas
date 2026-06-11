import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Dashboard de Vendas Automotivas", layout="wide")

MESES_PT = {
    1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr",
    5: "Mai", 6: "Jun", 7: "Jul", 8: "Ago",
    9: "Set", 10: "Out", 11: "Nov", 12: "Dez",
}

@st.cache_data
def load_data():
    df = pd.read_csv("dados_vendas.csv", parse_dates=["data"])
    df["mes_num"] = df["data"].dt.month
    df["ano"] = df["data"].dt.year
    df["mes_label"] = df.apply(
        lambda r: f"{MESES_PT[r['mes_num']]}/{r['ano']}", axis=1
    )
    df["mes_sort"] = df["data"].dt.to_period("M").astype(str)
    return df

df_orig = load_data()

# Meses disponíveis em ordem cronológica
meses_ordem = (
    df_orig[["mes_sort", "mes_label"]]
    .drop_duplicates()
    .sort_values("mes_sort")["mes_label"]
    .tolist()
)

# ── Sidebar com filtros ────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filtros")

    meses_sel = st.multiselect(
        "Período (mês)",
        options=meses_ordem,
        default=meses_ordem,
    )

    vendedores_disp = sorted(df_orig["vendedor"].unique())
    vendedores_sel = st.multiselect(
        "Vendedor",
        options=vendedores_disp,
        default=vendedores_disp,
    )

# Aplicar filtros
df = df_orig[
    df_orig["mes_label"].isin(meses_sel) &
    df_orig["vendedor"].isin(vendedores_sel)
]

if df.empty:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")
    st.stop()

vendidos = df[df["status"] == "Vendido"]

# ── Título ────────────────────────────────────────────────────────────────────
st.title("Dashboard de Vendas Automotivas")
st.divider()

# ── KPIs ──────────────────────────────────────────────────────────────────────
total_vendas = len(vendidos)
receita_total = vendidos["valor"].sum()
ticket_medio = vendidos["valor"].mean() if total_vendas > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("Total de Vendas", f"{total_vendas}")
col2.metric("Receita Total", f"R$ {receita_total:,.0f}".replace(",", "."))
col3.metric("Ticket Médio", f"R$ {ticket_medio:,.0f}".replace(",", "."))

st.divider()

# ── Evolução Mensal ────────────────────────────────────────────────────────────
st.subheader("Evolução Mensal de Vendas")

evolucao = (
    vendidos.groupby(["mes_sort", "mes_label"])
    .agg(vendas=("valor", "count"), receita=("valor", "sum"))
    .reset_index()
    .sort_values("mes_sort")
)

fig_evol = px.bar(
    evolucao,
    x="mes_label",
    y="vendas",
    text="vendas",
    color_discrete_sequence=["#2563EB"],
    labels={"mes_label": "Mês", "vendas": "Vendas"},
)
fig_evol.update_traces(textposition="outside")
fig_evol.update_layout(
    xaxis=dict(categoryorder="array", categoryarray=evolucao["mes_label"].tolist()),
    xaxis_title=None,
    yaxis_title="Vendas",
    margin=dict(l=0, r=20, t=10, b=0),
)
st.plotly_chart(fig_evol, use_container_width=True)

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
    modelos_df = (
        vendidos.groupby("modelo")
        .size()
        .sort_values(ascending=True)
        .reset_index(name="vendas")
    )
    fig_mod = px.bar(
        modelos_df,
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
    cols_exibir = [c for c in df.columns if c not in ("mes_num", "ano", "mes_label", "mes_sort")]
    st.dataframe(
        df[cols_exibir].sort_values("data", ascending=False),
        use_container_width=True,
        hide_index=True,
    )
