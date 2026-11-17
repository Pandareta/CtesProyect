"""Generador reproducible del dataset de suscripciones SaaS (Churn & Retención).

Crea 12.000 clientes únicos y añade suciedad controlada para el pipeline ETL:
40 filas duplicadas, 95 nulos en ``monthly_charges`` y 60 nulos en
``acquisition_channel``.

Uso:
    .\\.venv\\Scripts\\python.exe src/generate_data.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
N_CUSTOMERS = 12_000
N_DUPLICATES = 40
N_NULL_MONTHLY_CHARGES = 95
N_NULL_ACQUISITION_CHANNEL = 60
REFERENCE_DATE = pd.Timestamp("2026-11-01")

PLANS = ["Básico", "Pro", "Enterprise"]
PLAN_WEIGHTS = [0.50, 0.35, 0.15]
PLAN_BASE_PRICE = {"Básico": 29.0, "Pro": 79.0, "Enterprise": 199.0}

CONTRACTS = ["Mensual", "Anual", "Bianual"]
CONTRACT_WEIGHTS = [0.55, 0.30, 0.15]
CONTRACT_PRICE_FACTOR = {"Mensual": 1.00, "Anual": 0.85, "Bianual": 0.75}

CHANNELS = ["Paid Ads", "Orgánico", "Referidos", "Outbound"]
CHANNEL_WEIGHTS = [0.35, 0.30, 0.20, 0.15]
# El canal de adquisición ajusta el precio efectivo (promociones vs. venta directa).
CHANNEL_PRICE_FACTOR = {"Paid Ads": 0.92, "Orgánico": 1.00, "Referidos": 1.03, "Outbound": 1.06}

SUPPORT_LAMBDA = {"Básico": 1.3, "Pro": 1.9, "Enterprise": 2.6}

# Modelo de riesgo de churn (multiplicadores sobre la probabilidad base).
BASE_CHURN_PROBABILITY = 0.165
CONTRACT_RISK = {"Mensual": 1.35, "Anual": 0.81, "Bianual": 0.49}
PLAN_RISK = {"Básico": 1.25, "Pro": 1.00, "Enterprise": 0.75}
CHANNEL_RISK = {"Paid Ads": 1.15, "Orgánico": 0.90, "Referidos": 0.75, "Outbound": 1.00}
TICKET_RISK = np.array([1.00, 1.05, 1.55, 2.20, 5.20, 6.50, 8.45, 10.40, 13.00])
TENURE_DECAY = 0.015  # la antigüedad reduce el riesgo a partir del mes 3

OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "saas_subscriptions.csv"


def build_dataset() -> pd.DataFrame:
    """Construye los 12.000 clientes únicos (sin suciedad)."""
    rng = np.random.default_rng(SEED)

    plan_type = rng.choice(PLANS, size=N_CUSTOMERS, p=PLAN_WEIGHTS)
    contract_type = rng.choice(CONTRACTS, size=N_CUSTOMERS, p=CONTRACT_WEIGHTS)
    acquisition_channel = rng.choice(CHANNELS, size=N_CUSTOMERS, p=CHANNEL_WEIGHTS)

    tenure_months = np.clip(
        np.round(rng.gamma(shape=2.2, scale=8.5, size=N_CUSTOMERS)), 1, 48
    ).astype(int)

    support_lambda = np.array([SUPPORT_LAMBDA[p] for p in plan_type])
    support_tickets = np.clip(rng.poisson(lam=support_lambda), 0, 8).astype(int)

    price_noise = rng.lognormal(mean=0.0, sigma=0.06, size=N_CUSTOMERS)
    monthly_charges = (
        np.array([PLAN_BASE_PRICE[p] for p in plan_type])
        * np.array([CONTRACT_PRICE_FACTOR[c] for c in contract_type])
        * np.array([CHANNEL_PRICE_FACTOR[ch] for ch in acquisition_channel])
        * price_noise
    )
    monthly_charges = np.round(monthly_charges, 2)

    tenure_factor = np.exp(-TENURE_DECAY * np.maximum(0, tenure_months - 3))
    risk = (
        np.array([CONTRACT_RISK[c] for c in contract_type])
        * np.array([PLAN_RISK[p] for p in plan_type])
        * np.array([CHANNEL_RISK[ch] for ch in acquisition_channel])
        * tenure_factor
        * TICKET_RISK[support_tickets]
    )
    churn_probability = np.clip(BASE_CHURN_PROBABILITY * risk, 0.01, 0.99)
    is_churn = rng.binomial(1, churn_probability)

    signup_days = tenure_months * 30 + rng.integers(0, 30, size=N_CUSTOMERS)
    signup_date = (REFERENCE_DATE - pd.to_timedelta(signup_days, unit="D")).date

    return pd.DataFrame(
        {
            "customer_id": [f"CUST-{i:05d}" for i in range(1, N_CUSTOMERS + 1)],
            "signup_date": signup_date,
            "plan_type": plan_type,
            "contract_type": contract_type,
            "acquisition_channel": acquisition_channel,
            "tenure_months": tenure_months,
            "monthly_charges": monthly_charges,
            "support_tickets": support_tickets,
            "churn": np.where(is_churn == 1, "Sí", "No"),
        }
    )


def inject_dirt(df: pd.DataFrame) -> pd.DataFrame:
    """Añade nulos y duplicados sin alterar las reglas de negocio."""
    rng = np.random.default_rng(SEED + 1)
    dirty = df.copy()

    dirty.loc[
        rng.choice(dirty.index, size=N_NULL_MONTHLY_CHARGES, replace=False),
        "monthly_charges",
    ] = np.nan
    dirty.loc[
        rng.choice(dirty.index, size=N_NULL_ACQUISITION_CHANNEL, replace=False),
        "acquisition_channel",
    ] = np.nan

    # Solo se duplican filas completas para que, tras el ETL, los conteos
    # de nulos sigan siendo exactamente 95 y 60.
    complete_rows = dirty.index[
        dirty[["monthly_charges", "acquisition_channel"]].notna().all(axis=1)
    ]
    duplicate_rows = rng.choice(complete_rows, size=N_DUPLICATES, replace=False)

    dirty = pd.concat([dirty, dirty.loc[duplicate_rows]], ignore_index=True)
    return dirty.sample(frac=1.0, random_state=SEED).reset_index(drop=True)


def summarize(df: pd.DataFrame) -> None:
    """Imprime las métricas de control usadas para validar el dataset."""
    clean = df.drop_duplicates()
    churn = clean["churn"].eq("Sí")

    segment_a = clean[clean["contract_type"].eq("Mensual") & clean["tenure_months"].le(3)]
    segment_b = clean[clean["support_tickets"].ge(4)]

    print(f"Filas totales:            {len(df):,}")
    print(f"Clientes únicos:          {len(clean):,}")
    print(f"Duplicados eliminables:   {len(df) - len(clean):,}")
    print(f"Nulos monthly_charges:    {clean['monthly_charges'].isna().sum():,}")
    print(f"Nulos acquisition_channel:{clean['acquisition_channel'].isna().sum():,}")
    print(f"Churn global:             {churn.mean():.2%}")
    print(f"Churn Mensual & <=3m:     {segment_a['churn'].eq('Sí').mean():.2%}")
    print(f"Churn support_tickets>=4: {segment_b['churn'].eq('Sí').mean():.2%}")


def validate(df: pd.DataFrame) -> None:
    """Falla de forma explícita si el dataset no cumple los objetivos."""
    clean = df.drop_duplicates()
    churn_rate = clean["churn"].eq("Sí").mean()
    segment_a = clean[clean["contract_type"].eq("Mensual") & clean["tenure_months"].le(3)]
    segment_b = clean[clean["support_tickets"].ge(4)]

    assert len(clean) == N_CUSTOMERS, "El número de clientes únicos no es 12.000"
    assert len(df) - len(clean) == N_DUPLICATES, "El número de duplicados no es 40"
    assert clean["monthly_charges"].isna().sum() == N_NULL_MONTHLY_CHARGES
    assert clean["acquisition_channel"].isna().sum() == N_NULL_ACQUISITION_CHANNEL
    assert 0.24 <= churn_rate <= 0.28, f"Churn global fuera de rango: {churn_rate:.2%}"
    assert 0.38 <= segment_a["churn"].eq("Sí").mean() <= 0.46, "Churn del segmento Mensual<=3m fuera de rango"
    assert segment_b["churn"].eq("Sí").mean() > 0.65, "Churn de support_tickets>=4 no supera el 65%"


def main() -> None:
    df = inject_dirt(build_dataset())
    summarize(df)
    validate(df)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
    print(f"\nDataset escrito en: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
