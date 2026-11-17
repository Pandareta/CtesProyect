# ChurnPy — Churn & Retención de Clientes (SaaS / Telecom)

Proyecto de portafolio de **Data Analyst & Product/Retention Analytics**: un pipeline
completo que va del dataset crudo a un dashboard ejecutivo, pasando por ETL, métricas
SaaS y consultas SQL analíticas.

---

## Contexto de negocio

Una empresa SaaS / Telecom con **12.000 clientes** necesita responder tres preguntas:

1. **¿Cuánto ingreso recurrente está en riesgo** por las bajas?
2. **¿Qué segmentos cancelan más** y por qué?
3. **¿Dónde debe actuar el equipo** de retención y soporte?

El dataset es sintético y reproducible (`seed=42`), con reglas de negocio inyectadas para
que el análisis produzca hallazgos accionables.

---

## Resumen ejecutivo

- **Churn global: 24,95 %** (2.994 bajas sobre 12.000 clientes).
- **MRR perdido: $208.930 / mes**, equivalente al **26,9 %** del MRR total ($776.816).
- El contrato **Mensual** concentra el **73,3 %** del MRR perdido pese a representar solo el
  54,4 % de los clientes: es la palanca de retención más grande.
- Los clientes con **4 o más tickets de soporte** (10,7 % de la base) cancelan al **68,5 %** y
  explican **$86.165** de MRR perdido (**41,2 %** del total).
- **Paid Ads** es el canal con peor retención (70,4 %) y menor LTV ($1.102), mientras que
  **Referidos** lidera la retención (80,2 %) y **Outbound** el LTV ($1.262).

---

## Métricas SaaS calculadas

| Métrica | Valor | Definición |
| --- | ---: | --- |
| Clientes activos | 9.006 | Clientes con `churn = 'No'` |
| Churn Rate Global | 24,95 % | Bajas / total de clientes |
| MRR Activo | $567.886 | Suma de `monthly_charges` de clientes activos |
| MRR Perdido por Baja | $208.931 | Suma de `monthly_charges` de clientes dados de baja |
| ARPU activo | $63,06 | Ingreso mensual promedio por usuario activo |
| LTV medio (histórico) | $1.179,73 | `monthly_charges × tenure_months` |
| Antigüedad media | 18,25 meses | Promedio de `tenure_months` |
| Tickets de soporte medios | 1,71 | Promedio de `support_tickets` |

---

## Hallazgos cuantitativos

### 1. El tipo de contrato explica la mayor parte del riesgo

| Tipo de contrato | Clientes | Churn | MRR perdido | % del MRR perdido |
| --- | ---: | ---: | ---: | ---: |
| Mensual | 6.532 | **31,81 %** | $153.231 | **73,34 %** |
| Anual | 3.671 | 19,15 % | $43.570 | 20,85 % |
| Bianual | 1.797 | **11,85 %** | $12.129 | 5,81 % |

Un cliente **Mensual** tiene **2,7 veces** más probabilidad de cancelar que uno **Bianual**.

### 2. Los tickets de soporte son un umbral, no una tendencia

| Tickets | Clientes | Churn |
| ---: | ---: | ---: |
| 0 | 2.414 | 14,83 % |
| 1 | 3.630 | 16,23 % |
| 2 | 2.972 | 22,68 % |
| 3 | 1.706 | 29,13 % |
| **4** | **805** | **63,85 %** |
| 5 | 325 | 73,54 % |
| 6 | 98 | 79,59 % |
| 7 | 38 | 86,84 % |
| 8 | 12 | 100,00 % |

El salto ocurre exactamente en **4 tickets**: la tasa pasa de 29,1 % a 63,9 %. Ese grupo
(1.278 clientes) genera **$86.165** de MRR perdido.

### 3. La antigüedad temprana es la ventana crítica

| Cohorte | Clientes | Churn | MRR perdido |
| --- | ---: | ---: | ---: |
| 0-3 meses | 560 | **33,21 %** | $13.140 |
| 4-12 meses | 3.937 | 27,64 % | $74.583 |
| 13-24 meses | 4.404 | 24,95 % | $78.757 |
| +24 meses | 3.099 | **20,04 %** | $42.452 |

El segmento **Mensual con ≤ 3 meses** alcanza un churn del **41,77 %** (316 clientes).

### 4. Canales: retención y LTV no van de la mano

| Canal | Clientes | Retención | ARPU | LTV medio |
| --- | ---: | ---: | ---: | ---: |
| Referidos | 2.450 | **80,20 %** | $67,08 | $1.230 |
| Orgánico | 3.531 | 77,63 % | $65,89 | $1.194 |
| Outbound | 1.771 | 73,80 % | $69,84 | **$1.262** |
| Paid Ads | 4.188 | **70,42 %** | $60,25 | **$1.102** |
| Orgánico / No Especificado | 60 | 73,33 % | $62,89 | $1.231 |

**Outbound** capta clientes de mayor valor pero retiene peor que **Referidos**; **Paid Ads**
es el extremo opuesto en ambas dimensiones.

### 5. Matriz de riesgo plan × contrato

| Plan | Contrato | Clientes | Churn | MRR perdido | % del MRR perdido |
| --- | --- | ---: | ---: | ---: | ---: |
| Enterprise | Mensual | 932 | **37,45 %** | $68.039 | **32,57 %** |
| Pro | Mensual | 2.288 | 32,04 % | $56.876 | 27,22 % |
| Básico | Mensual | 3.312 | 30,07 % | $28.316 | 13,55 % |

**Enterprise** tiene el churn más alto (28,3 %) pese a su menor riesgo intrínseco, porque
concentra más tickets de soporte. El soporte, no el precio, es el principal *driver*.

---

## Dataset

`data/raw/saas_subscriptions.csv` (12.040 filas, 12.000 clientes únicos):

| Columna | Descripción |
| --- | --- |
| `customer_id` | Identificador único (`CUST-00001` … `CUST-12000`) |
| `signup_date` | Fecha de alta |
| `plan_type` | `Básico`, `Pro`, `Enterprise` |
| `contract_type` | `Mensual`, `Anual`, `Bianual` |
| `acquisition_channel` | `Paid Ads`, `Orgánico`, `Referidos`, `Outbound` |
| `tenure_months` | Antigüedad en meses (1-48) |
| `monthly_charges` | Cargo mensual en USD |
| `support_tickets` | Tickets de soporte (0-8) |
| `churn` | `Sí` / `No` |

**Suciedad inyectada a propósito** (se depura en el ETL y se reporta en el dashboard):

- 40 filas duplicadas.
- 95 nulos en `monthly_charges` → imputados con la **mediana por `plan_type`**.
- 60 nulos en `acquisition_channel` → imputados como `'Orgánico / No Especificado'`.

---

## Estructura del repositorio

```text
.
├── AGENTS.md
├── app.py                          # Dashboard Streamlit (capa de presentación)
├── requirements.txt
├── .gitignore
├── .streamlit/
│   └── config.toml                 # Tema oscuro
├── data/
│   └── raw/
│       └── saas_subscriptions.csv  # Dataset versionado (Streamlit Cloud)
├── sql/
│   └── retention_queries.sql       # 4 consultas analíticas
├── src/
│   └── generate_data.py            # Generador reproducible (seed=42)
└── .opencode/skills/               # Estándares del proyecto para agentes
```

---

## Cómo ejecutar

> En este equipo `python` no está en el `PATH`; se usa la ruta completa del intérprete
> para crear el entorno virtual. Si tu `python` sí está en el `PATH`, reemplaza el primer
> comando por `python -m venv .venv`.

```powershell
# 1. Crear e instalar dependencias
& "C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe" -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 2. (Opcional) Regenerar el dataset — es reproducible con seed=42
.\.venv\Scripts\python.exe src\generate_data.py

# 3. Levantar el dashboard
.\.venv\Scripts\streamlit.exe run app.py
```

Abre <http://localhost:8501>.

### Comando exacto para levantar Streamlit en local

Desde `C:\Users\Admin\Documents\BUSQUEDA LABORAL\ChurnPy`:

```powershell
.\.venv\Scripts\streamlit.exe run app.py
```

---

## Consultas SQL

`sql/retention_queries.sql` contiene cuatro consultas documentadas:

| Consulta | Pregunta de negocio | Técnica |
| --- | --- | --- |
| (a) Churn y MRR perdido por contrato | ¿Qué contrato destruye más MRR? | CTE + `SUM() OVER ()` |
| (b) Riesgo por tickets de soporte | ¿Cómo escala la baja con los tickets? | Agregación condicional |
| (c) Ranking de canales | ¿Qué canal retiene y aporta más LTV? | `DENSE_RANK() OVER` |
| (d) Matriz plan × contrato | ¿Cuál es el segmento más volátil? | CTE + `RANK() OVER` |

Las cuatro se muestran también dentro del dashboard, en el desplegable
**“Ver Consultas SQL Analíticas”**.

---

## Limitaciones y supuestos

- El dataset es **sintético**: las distribuciones y reglas de churn están inyectadas para
  demostrar el análisis, no corresponden a una empresa real.
- El LTV es **histórico** (`monthly_charges × tenure_months`), no una proyección futura.
- El MRR no descuenta impuestos, descuentos posteriores ni devoluciones.
- Los KPIs y gráficos se recalculan sobre los filtros activos del dashboard.
