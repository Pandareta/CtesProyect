---
name: sql-cohort-analytics
description: Consultas SQL analíticas sobre retención, tasas de baja por cohorte y riesgo de fuga.
---
# Estándares de SQL para Retención
1. Escribe SQL estándar compatible con PostgreSQL / DuckDB.
2. Usa **CTEs (`WITH ... AS`)** y **Window Functions** (`SUM() OVER ()`, `RANK() OVER (...)`, `ROUND(..., 2)`).
3. Documenta cada consulta con la pregunta de negocio que responde (ej. *¿Qué combinación de plan y cantidad de tickets de soporte dispara el Churn?*).
