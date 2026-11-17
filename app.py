"""Dashboard ejecutivo de Churn & Retención para un negocio SaaS / Telecom.

Ejecutar con:
    .\\.venv\\Scripts\\streamlit.exe run app.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "raw" / "saas_subscriptions.csv"
SQL_PATH = BASE_DIR / "sql" / "retention_queries.sql"

PLAN_ORDER = ["Básico", "Pro", "Enterprise"]
CONTRACT_ORDER = ["Mensual", "Anual", "Bianual"]
TENURE_LABELS = ["0-3 meses", "4-12 meses", "13-24 meses", "+24 meses"]

COLOR_ACTIVE = "#22C55E"
COLOR_CHURN = "#EF4444"
COLOR_PRIMARY = "#2DD4BF"
COLOR_ACCENT = "#F97316"
COLOR_INFO = "#38BDF8"

st.set_page_config(
    page_title="Churn & Retención | SaaS",
    page_icon="📉",
    layout="wide",
)


# ---------------------------------------------------------------------------
# Utilidades de formato (español: punto de miles, coma decimal)
# ---------------------------------------------------------------------------
def fmt_int(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".")


def fmt_money(value: float) -> str:
    return "$" + fmt_int(value)


def fmt_pct(value: float) -> str:
    return f"{value:.1f}%".replace(".", ",")


# ---------------------------------------------------------------------------
# Pipeline ETL
# ---------------------------------------------------------------------------
@st.cache_data
def load_and_clean(path: str) -> tuple[pd.DataFrame, dict[str, int]]:
    """Carga el CSV y aplica deduplicación, imputación y feature engineering."""
    raw = pd.read_csv(path)
    df = raw.drop_duplicates().copy()

    stats = {
        "raw_rows": int(len(raw)),
        "clean_rows": int(len(df)),
        "duplicates": int(len(raw) - len(df)),
        "null_monthly": int(df["monthly_charges"].isna().sum()),
        "null_channel": int(df["acquisition_channel"].isna().sum()),
    }

    # Imputación: mediana por plan para cargos; categoría explícita para canal.
    df["monthly_charges"] = df.groupby("plan_type")["monthly_charges"].transform(
        lambda series: series.fillna(series.median())
    )
    df["acquisition_channel"] = df["acquisition_channel"].fillna(
        "Orgánico / No Especificado"
    )

    df["is_churn"] = (df["churn"] == "Sí").astype(int)
    df["tenure_cohort"] = pd.cut(
        df["tenure_months"],
        bins=[0, 3, 12, 24, 48],
        labels=TENURE_LABELS,
    )
    df["ltv"] = df["monthly_charges"] * df["tenure_months"]
    return df, stats


# ---------------------------------------------------------------------------
# Componentes del dashboard
# ---------------------------------------------------------------------------
def render_header(stats: dict[str, int]) -> None:
    st.title("📉 Churn & Retención de Clientes")
    st.caption(
        "SaaS / Telecom · Análisis de cancelaciones, MRR en riesgo y cohorts de antigüedad."
    )
    st.info(
        f"**Calidad del dato:** {fmt_int(stats['raw_rows'])} filas de origen → "
        f"{fmt_int(stats['clean_rows'])} clientes únicos tras el ETL. "
        f"Se depuraron **{stats['duplicates']} filas duplicadas** y "
        f"**{stats['null_monthly'] + stats['null_channel']} valores nulos** "
        f"({stats['null_monthly']} en `monthly_charges`, "
        f"{stats['null_channel']} en `acquisition_channel`)."
    )


def render_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filtros")

    selected_plans = st.sidebar.multiselect(
        "Tipo de plan", PLAN_ORDER, default=PLAN_ORDER
    )
    selected_contracts = st.sidebar.multiselect(
        "Tipo de contrato", CONTRACT_ORDER, default=CONTRACT_ORDER
    )
    selected_cohorts = st.sidebar.multiselect(
        "Cohorte de antigüedad", TENURE_LABELS, default=TENURE_LABELS
    )

    mask = (
        df["plan_type"].isin(selected_plans)
        & df["contract_type"].isin(selected_contracts)
        & df["tenure_cohort"].isin(selected_cohorts)
    )
    filtered = df.loc[mask].copy()

    st.sidebar.divider()
    st.sidebar.metric("Clientes filtrados", fmt_int(len(filtered)))
    return filtered


def render_kpis(df: pd.DataFrame) -> None:
    active = df[df["is_churn"] == 0]
    churned = df[df["is_churn"] == 1]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Clientes Activos", fmt_int(len(active)))
    col2.metric("Churn Rate Global (%)", fmt_pct(df["is_churn"].mean() * 100))
    col3.metric("MRR Activo ($)", fmt_money(active["monthly_charges"].sum()))
    col4.metric("MRR Perdido por Baja ($)", fmt_money(churned["monthly_charges"].sum()))


def chart_churn_by_tenure(df: pd.DataFrame) -> go.Figure:
    stats = (
        df.groupby("tenure_cohort", observed=False)
        .agg(churn_rate=("is_churn", "mean"), customers=("customer_id", "count"))
        .reset_index()
    )
    stats = stats[stats["customers"] > 0]

    fig = go.Figure(
        go.Bar(
            x=stats["tenure_cohort"].astype(str),
            y=stats["churn_rate"] * 100,
            text=[fmt_pct(value * 100) for value in stats["churn_rate"]],
            textposition="outside",
            marker_color=COLOR_ACCENT,
            hovertemplate="Cohorte %{x}<br>Churn %{y:.1f}%<extra></extra>",
        )
    )
    fig.update_layout(
        template="plotly_dark",
        title="Tasa de Churn (%) por Cohorte de Antigüedad",
        xaxis_title="Cohorte",
        yaxis_title="Churn (%)",
        yaxis_range=[0, max(100, (stats["churn_rate"].max() * 100) * 1.25)],
        height=380,
        margin=dict(l=10, r=10, t=50, b=10),
        showlegend=False,
    )
    return fig


def chart_support_tickets(df: pd.DataFrame) -> go.Figure:
    stats = (
        df.groupby("support_tickets")
        .agg(churn_rate=("is_churn", "mean"), customers=("customer_id", "count"))
        .reset_index()
    )

    fig = go.Figure(
        go.Bar(
            x=stats["support_tickets"],
            y=stats["churn_rate"] * 100,
            text=[fmt_pct(value * 100) for value in stats["churn_rate"]],
            textposition="outside",
            marker_color=COLOR_INFO,
            hovertemplate="Tickets: %{x}<br>Churn %{y:.1f}%<extra></extra>",
        )
    )
    fig.add_vline(
        x=3.5,
        line_dash="dash",
        line_color=COLOR_CHURN,
        annotation_text="Umbral crítico (4+)",
        annotation_position="top",
    )
    fig.update_layout(
        template="plotly_dark",
        title="Impacto de los Tickets de Soporte en la Probabilidad de Baja",
        xaxis_title="Tickets de soporte",
        yaxis_title="Churn (%)",
        yaxis_range=[0, max(100, (stats["churn_rate"].max() * 100) * 1.25)],
        height=380,
        margin=dict(l=10, r=10, t=50, b=10),
        showlegend=False,
    )
    return fig


def chart_contract_distribution(df: pd.DataFrame) -> go.Figure:
    stats = (
        df.groupby(["contract_type", "churn"])
        .size()
        .unstack(fill_value=0)
        .reindex(CONTRACT_ORDER, fill_value=0)
    )
    for column in ("No", "Sí"):
        if column not in stats.columns:
            stats[column] = 0

    fig = go.Figure()
    fig.add_bar(
        name="Activos",
        x=stats.index,
        y=stats["No"],
        marker_color=COLOR_ACTIVE,
        hovertemplate="%{x}<br>Activos: %{y:,}<extra></extra>",
    )
    fig.add_bar(
        name="Churn",
        x=stats.index,
        y=stats["Sí"],
        marker_color=COLOR_CHURN,
        hovertemplate="%{x}<br>Bajas: %{y:,}<extra></extra>",
    )
    fig.update_layout(
        template="plotly_dark",
        title="Distribución de Churn por Tipo de Contrato",
        barmode="stack",
        xaxis_title="Tipo de contrato",
        yaxis_title="Clientes",
        height=380,
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def chart_plan_arpu_retention(df: pd.DataFrame) -> go.Figure:
    active = df[df["is_churn"] == 0]
    stats = pd.DataFrame(
        {
            "arpu": active.groupby("plan_type")["monthly_charges"].mean(),
            "retention": df.groupby("plan_type")["is_churn"].apply(
                lambda series: (1 - series.mean()) * 100
            ),
        }
    ).reindex(PLAN_ORDER)
    stats = stats.dropna(how="all")

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(
            name="ARPU ($)",
            x=stats.index,
            y=stats["arpu"],
            marker_color=COLOR_PRIMARY,
            hovertemplate="%{x}<br>ARPU: $%{y:,.2f}<extra></extra>",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            name="Retención (%)",
            x=stats.index,
            y=stats["retention"],
            mode="lines+markers",
            marker=dict(color=COLOR_ACTIVE, size=10),
            line=dict(color=COLOR_ACTIVE, width=3),
            hovertemplate="%{x}<br>Retención: %{y:.1f}%<extra></extra>",
        ),
        secondary_y=True,
    )
    fig.update_layout(
        template="plotly_dark",
        title="Comparativa de ARPU y Retención por Plan",
        height=380,
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(title_text="Plan")
    fig.update_yaxes(title_text="ARPU ($)", secondary_y=False)
    fig.update_yaxes(title_text="Retención (%)", range=[0, 100], secondary_y=True)
    return fig


def render_sql() -> None:
    with st.expander("Ver Consultas SQL Analíticas"):
        st.code(SQL_PATH.read_text(encoding="utf-8"), language="sql")


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
def main() -> None:
    df, stats = load_and_clean(str(DATA_PATH))
    render_header(stats)

    filtered = render_filters(df)
    if filtered.empty:
        st.warning("No hay clientes para la combinación de filtros seleccionada.")
        st.stop()

    render_kpis(filtered)
    st.divider()

    left, right = st.columns(2)
    with left:
        st.plotly_chart(chart_churn_by_tenure(filtered), width="stretch")
        st.plotly_chart(chart_contract_distribution(filtered), width="stretch")
    with right:
        st.plotly_chart(chart_support_tickets(filtered), width="stretch")
        st.plotly_chart(chart_plan_arpu_retention(filtered), width="stretch")

    st.caption(
        "MRR Activo = suma de cargos mensuales de clientes activos · "
        "MRR Perdido = suma de cargos mensuales de clientes dados de baja · "
        "ARPU = ingreso mensual promedio por usuario activo."
    )
    render_sql()


main()
