---
name: streamlit-bi-ui
description: Diseño de dashboard ejecutivo de retención en Streamlit y Plotly en modo oscuro.
---
# Estándares de Visualización BI
1. Usa `st.set_page_config(..., layout="wide")` y `@st.cache_data` para la carga y limpieza.
2. Barra lateral (`st.sidebar`) con filtros de `plan_type`, `contract_type` y `tenure_cohort`.
3. Fila superior de 4 KPIs (`st.metric`): **Clientes Activos**, **Churn Rate Global (%)**, **MRR Activo ($)** y **MRR Perdido por Baja ($)**.
4. Grilla 2x2 de gráficos Plotly (`template="plotly_dark"`):
   - Tasa de Churn (%) por Cohorte de Antigüedad (`tenure_cohort`).
   - Impacto de Tickets de Soporte (`support_tickets`) en la probabilidad de baja.
   - Distribución de Churn por Tipo de Contrato (`Mensual`, `Anual`, `Bianual`).
   - Comparativa de ARPU y Retención por Plan (`Básico`, `Pro`, `Enterprise`).
