---
name: clean-code-git
description: Arquitectura de repositorio, configuración de Streamlit Cloud y Git.
---
# Estándares de Ingeniería y Estructura
1. Separa responsabilidades:
   - `data/raw/` para el dataset CSV crudo.
   - `src/` para scripts de generación y transformación de datos.
   - `sql/` para consultas analíticas puras.
   - `.streamlit/config.toml` con tema oscuro configurado (`base="dark"`).
   - `app.py` en la raíz para la capa de visualización.
2. Crea `.gitignore` ignorando `.venv/`, `__pycache__/`, `.env`, `.DS_Store`, pero **manteniendo trackeado `data/raw/*.csv`** para que Streamlit Cloud lea los datos sin base externa.
3. Usa `pathlib.Path` para todas las rutas de archivos.
