---
name: churn-etl-metrics
description: Limpieza de datos de suscripción, imputación estadística y cálculo de métricas SaaS (MRR, ARPU, Churn Rate, Tenure Cohorts).
---
# Estándares de ETL y Métricas de Retención
1. **Limpieza:** Elimina duplicados explícitamente (`drop_duplicates()`). Imputa cargos mensuales (`monthly_charges`) nulos con la **mediana agrupada por tipo de plan (`plan_type`)**. Imputa canales de adquisición nulos como `'Orgánico / No Especificado'`.
2. **Feature Engineering:**
   - Crea segmentos de antigüedad (`tenure_cohort`): `'0-3 meses'`, `'4-12 meses'`, `'13-24 meses'`, `'+24 meses'`.
   - Convierte `churn` a bandera numérica (`is_churn`: 1 o 0) para calcular tasas de cancelación vectorizadas.
3. **Métricas de Negocio:** Calcula el **MRR en riesgo** (suma de `monthly_charges` de clientes dados de baja) y el **ARPU** (ingreso promedio por usuario activo).
