import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Dashboard de Vendas Automotivas", layout="wide")

MESES_PT = {
    1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr",
    5: "Mai", 6: "Jun", 7: "Jul", 8: "Ago",
    9: "Set", 10: "Out", 11: "Nov", 12: "Dez",
}

COR_STATUS = {
    "Vendido": "#22C55E",
    "Em negociação": "#F59E0B",
    "Perdido": "#EF4444",
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

meses_ordem = (
    df_orig[["mes_sort", "mes_label"]]
    .drop_duplicates()
    .sort_values("mes_sort")["mes_label"]
    .tolist()
)

# ── Sidebar ────────────────────────────────────────────────────────────────────
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

# Filtros aplicados globalmente — todas as abas usam df e vendidos
df = df_orig[
    df_orig["mes_label"].isin(meses_sel) &
    df_orig["vendedor"].isin(vendedores_sel)
]

if df.empty:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")
    st.stop()

vendidos = df[df["status"] == "Vendido"]
perdidos = df[df["status"] == "Perdido"]
em_neg = df[df["status"] == "Em negociação"]

# ── Título e abas ─────────────────────────────────────────────────────────────
st.title("Dashboard de Vendas Automotivas")

tab_visao, tab_leads, tab_vend, tab_estoque = st.tabs(
    ["Visão Geral", "Leads e Funil", "Vendedores", "Estoque"]
)

# ══════════════════════════════════════════════════════════════════════════════
# ABA 1 — VISÃO GERAL
# ══════════════════════════════════════════════════════════════════════════════
with tab_visao:
    total_vendas = len(vendidos)
    receita_total = vendidos["valor"].sum()
    ticket_medio = vendidos["valor"].mean() if total_vendas > 0 else 0
    taxa_conversao = total_vendas / len(df) * 100

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de Vendas", f"{total_vendas}")
    col2.metric("Receita Total", f"R$ {receita_total:,.0f}".replace(",", "."))
    col3.metric("Ticket Médio", f"R$ {ticket_medio:,.0f}".replace(",", "."))
    col4.metric("Taxa de Conversão", f"{taxa_conversao:.1f}%")

    st.divider()
    st.subheader("Evolução Mensal de Vendas")

    evolucao = (
        vendidos.groupby(["mes_sort", "mes_label"])
        .size()
        .reset_index(name="vendas")
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

# ══════════════════════════════════════════════════════════════════════════════
# ABA 2 — LEADS E FUNIL
# ══════════════════════════════════════════════════════════════════════════════
with tab_leads:
    origem_counts = df["origem_lead"].value_counts()
    top_canal = origem_counts.idxmax()
    taxa_conv_geral = len(vendidos) / len(df) * 100

    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Leads", f"{len(df)}")
    col2.metric("Melhor Canal", top_canal, f"{origem_counts.max()} leads")
    col3.metric("Taxa de Conversão Geral", f"{taxa_conv_geral:.1f}%")

    st.divider()
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Distribuição por Origem")
        leads_origem = (
            df.groupby("origem_lead")
            .size()
            .reset_index(name="total")
            .sort_values("total", ascending=False)
        )
        CORES_ORIGEM = ["#3B82F6", "#10B981", "#F59E0B", "#8B5CF6"]
        fig_pizza = px.pie(
            leads_origem,
            names="origem_lead",
            values="total",
            color_discrete_sequence=CORES_ORIGEM,
            hole=0.45,
        )
        fig_pizza.update_traces(
            textposition="outside",
            textinfo="percent+label",
            textfont_size=13,
            pull=[0.04] * len(leads_origem),
        )
        fig_pizza.update_layout(
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            margin=dict(l=0, r=0, t=10, b=40),
        )
        st.plotly_chart(fig_pizza, use_container_width=True)

    with col_b:
        st.subheader("Funil de Conversão")
        etapas = ["Total de Leads", "Em Negociação", "Vendidos"]
        valores = [len(df), len(em_neg) + len(vendidos), len(vendidos)]
        pcts = [100.0, (len(em_neg) + len(vendidos)) / len(df) * 100, taxa_conv_geral]
        labels_funil = [
            f"{e}<br><b>{v}</b>  ({p:.1f}%)"
            for e, v, p in zip(etapas, valores, pcts)
        ]
        fig_funil = go.Figure(go.Funnel(
            y=labels_funil,
            x=valores,
            marker=dict(color=["#3B82F6", "#F59E0B", "#22C55E"]),
            textposition="inside",
            textinfo="none",
            connector=dict(line=dict(color="rgba(0,0,0,0)", width=0)),
            opacity=0.9,
        ))
        fig_funil.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            funnelmode="stack",
            showlegend=False,
            yaxis=dict(tickfont=dict(size=13)),
        )
        st.plotly_chart(fig_funil, use_container_width=True)

    st.divider()
    st.subheader("Taxa de Conversão por Origem")

    leads_orig = df.groupby("origem_lead").size().reset_index(name="leads")
    vendidos_orig = vendidos.groupby("origem_lead").size().reset_index(name="vendidos")
    conv_orig = leads_orig.merge(vendidos_orig, on="origem_lead", how="left")
    conv_orig["vendidos"] = conv_orig["vendidos"].fillna(0).astype(int)
    conv_orig["conversao"] = conv_orig["vendidos"] / conv_orig["leads"] * 100
    conv_orig = conv_orig.sort_values("conversao", ascending=True)

    fig_conv = px.bar(
        conv_orig,
        x="conversao",
        y="origem_lead",
        orientation="h",
        text=conv_orig["conversao"].map("{:.1f}%".format),
        color="conversao",
        color_continuous_scale="Greens",
        range_color=[0, conv_orig["conversao"].max() * 1.1],
        labels={"conversao": "Taxa (%)", "origem_lead": ""},
        custom_data=["leads", "vendidos"],
    )
    fig_conv.update_traces(
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Leads: %{customdata[0]}<br>Vendidos: %{customdata[1]}<br>Conversão: %{x:.1f}%<extra></extra>",
    )
    fig_conv.update_layout(
        showlegend=False,
        coloraxis_showscale=False,
        xaxis_title="Taxa de Conversão (%)",
        yaxis_title=None,
        margin=dict(l=0, r=70, t=10, b=0),
        xaxis=dict(range=[0, conv_orig["conversao"].max() * 1.25]),
    )
    st.plotly_chart(fig_conv, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# ABA 3 — VENDEDORES
# ══════════════════════════════════════════════════════════════════════════════
with tab_vend:
    META_VENDAS = 15

    # Base de desempenho reutilizada em toda a aba
    leads_vend = df.groupby("vendedor").size().reset_index(name="leads")
    stats_vend = vendidos.groupby("vendedor").agg(
        vendas=("valor", "count"),
        receita=("valor", "sum"),
        ticket_medio=("valor", "mean"),
    ).reset_index()
    desemp = leads_vend.merge(stats_vend, on="vendedor", how="left")
    desemp["vendas"] = desemp["vendas"].fillna(0).astype(int)
    desemp["receita"] = desemp["receita"].fillna(0)
    desemp["ticket_medio"] = desemp["ticket_medio"].fillna(0)
    desemp["conversao"] = desemp["vendas"] / desemp["leads"] * 100
    desemp["bateu_meta"] = desemp["vendas"] >= META_VENDAS

    # ── KPIs ──────────────────────────────────────────────────────────────────
    mv = desemp.loc[desemp["vendas"].idxmax()]
    mr = desemp.loc[desemp["receita"].idxmax()]
    mc = desemp.loc[desemp["conversao"].idxmax()]
    qtd_meta = int(desemp["bateu_meta"].sum())

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Melhor Vendedor", mv["vendedor"], f"{mv['vendas']} vendas")
    col2.metric(
        "Maior Receita",
        mr["vendedor"],
        f"R$ {mr['receita']:,.0f}".replace(",", "."),
    )
    col3.metric("Melhor Conversão", mc["vendedor"], f"{mc['conversao']:.1f}%")
    col4.metric(
        "Bateram a Meta",
        f"{qtd_meta} / {len(desemp)}",
        f"Meta: {META_VENDAS} vendas",
    )

    st.divider()
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Ranking por Vendas")
        rank = desemp[["vendedor", "vendas", "bateu_meta"]].sort_values("vendas", ascending=True)
        cores_rank = ["#22C55E" if b else "#94A3B8" for b in rank["bateu_meta"]]
        fig_rank = go.Figure(go.Bar(
            x=rank["vendas"],
            y=rank["vendedor"],
            orientation="h",
            text=rank["vendas"],
            textposition="outside",
            marker_color=cores_rank,
            hovertemplate="<b>%{y}</b><br>Vendas: %{x}<extra></extra>",
        ))
        fig_rank.add_vline(
            x=META_VENDAS,
            line_dash="dash",
            line_color="#EF4444",
            line_width=2,
            annotation_text=f"Meta ({META_VENDAS})",
            annotation_position="top right",
            annotation_font_color="#EF4444",
            annotation_font_size=12,
        )
        fig_rank.update_layout(
            showlegend=False,
            xaxis_title="Vendas",
            yaxis_title=None,
            margin=dict(l=0, r=40, t=20, b=0),
            xaxis=dict(range=[0, rank["vendas"].max() * 1.25]),
        )
        st.plotly_chart(fig_rank, use_container_width=True)

        # Legenda da cor
        st.caption("🟢 Bateu a meta  |  ⚫ Abaixo da meta")

    with col_b:
        st.subheader("Receita por Vendedor")
        rec = desemp[["vendedor", "receita"]].sort_values("receita", ascending=True)
        fig_rec = go.Figure(go.Bar(
            x=rec["receita"],
            y=rec["vendedor"],
            orientation="h",
            text=[f"R$ {v / 1e6:.2f}M" for v in rec["receita"]],
            textposition="outside",
            marker=dict(
                color=rec["receita"],
                colorscale="Purples",
                showscale=False,
            ),
            hovertemplate="<b>%{y}</b><br>Receita: R$ %{x:,.0f}<extra></extra>",
        ))
        fig_rec.update_layout(
            showlegend=False,
            xaxis_title="Receita (R$)",
            yaxis_title=None,
            margin=dict(l=0, r=100, t=20, b=0),
            xaxis=dict(range=[0, rec["receita"].max() * 1.3]),
        )
        st.plotly_chart(fig_rec, use_container_width=True)

    st.divider()
    st.subheader("Desempenho Completo por Vendedor")

    tabela_num = desemp[["vendedor", "leads", "vendas", "conversao", "receita", "ticket_medio", "bateu_meta"]].copy()
    tabela_num["meta_status"] = tabela_num["bateu_meta"].map(lambda x: "✅ Sim" if x else "❌ Não")
    tabela_num = tabela_num.rename(columns={
        "vendedor": "Vendedor",
        "leads": "Leads",
        "vendas": "Vendas",
        "conversao": "Conversão (%)",
        "receita": "Receita Total (R$)",
        "ticket_medio": "Ticket Médio (R$)",
        "meta_status": f"Bateu Meta ({META_VENDAS})",
    }).drop(columns="bateu_meta").sort_values("Vendas", ascending=False)

    st.dataframe(
        tabela_num,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Vendas": st.column_config.ProgressColumn(
                f"Vendas (meta {META_VENDAS})",
                help=f"Barra mostra progresso em relação à meta de {META_VENDAS} vendas",
                format="%d",
                min_value=0,
                max_value=META_VENDAS,
            ),
            "Conversão (%)": st.column_config.NumberColumn(
                "Conversão (%)",
                format="%.1f%%",
            ),
            "Receita Total (R$)": st.column_config.NumberColumn(
                "Receita Total",
                format="R$ %.0f",
            ),
            "Ticket Médio (R$)": st.column_config.NumberColumn(
                "Ticket Médio",
                format="R$ %.0f",
            ),
        },
    )

# ══════════════════════════════════════════════════════════════════════════════
# ABA 4 — ESTOQUE
# ══════════════════════════════════════════════════════════════════════════════
with tab_estoque:
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Modelos Mais Vendidos")
        modelos_rank = (
            vendidos.groupby("modelo")
            .size()
            .sort_values(ascending=True)
            .reset_index(name="vendas")
        )
        fig_mod = px.bar(
            modelos_rank,
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
            xaxis_title="Vendas",
            yaxis_title=None,
            margin=dict(l=0, r=20, t=10, b=0),
        )
        st.plotly_chart(fig_mod, use_container_width=True)

    with col_b:
        st.subheader("Ticket Médio por Modelo")
        ticket_modelo = (
            vendidos.groupby("modelo")["valor"]
            .mean()
            .sort_values(ascending=True)
            .reset_index(name="ticket")
        )
        fig_ticket = px.bar(
            ticket_modelo,
            x="ticket",
            y="modelo",
            orientation="h",
            text=ticket_modelo["ticket"].map(lambda v: f"R$ {v / 1000:.0f}k"),
            color="ticket",
            color_continuous_scale="Oranges",
        )
        fig_ticket.update_traces(textposition="outside")
        fig_ticket.update_layout(
            showlegend=False,
            coloraxis_showscale=False,
            xaxis_title="Ticket Médio (R$)",
            yaxis_title=None,
            margin=dict(l=0, r=70, t=10, b=0),
        )
        st.plotly_chart(fig_ticket, use_container_width=True)

    st.divider()
    st.subheader("Status por Modelo")

    status_modelo = (
        df.groupby(["modelo", "status"])
        .size()
        .reset_index(name="total")
    )
    fig_status_mod = px.bar(
        status_modelo,
        x="total",
        y="modelo",
        color="status",
        orientation="h",
        text="total",
        color_discrete_map=COR_STATUS,
        barmode="stack",
        labels={"total": "Quantidade", "modelo": "", "status": "Status"},
    )
    fig_status_mod.update_traces(textposition="inside", textfont_size=11)
    fig_status_mod.update_layout(
        xaxis_title="Quantidade",
        yaxis_title=None,
        legend_title=None,
        margin=dict(l=0, r=20, t=10, b=0),
    )
    st.plotly_chart(fig_status_mod, use_container_width=True)
