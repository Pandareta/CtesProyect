# Contexto y Estándares del Proyecto
- Proyecto de portafolio profesional orientado a **Data Analyst & Product/Retention Analytics**.
- Todo el texto visible al usuario (UI del dashboard, comentarios de negocio en SQL y README.md) debe estar redactado en **español profesional**, mientras que variables, columnas y funciones deben estar en **inglés (snake_case)**.
- **Entorno Python:** Verifica si `python` está en el PATH; si no lo está, crea un entorno virtual `.venv` con el ejecutable de Python disponible en el sistema e instala las dependencias ahí.
- Genera `requirements.txt` únicamente con los nombres de los paquetes principales (`pandas`, `numpy`, `plotly`, `streamlit`) sin fijar versiones estrictas para garantizar compatibilidad en Streamlit Cloud.
- Antes de finalizar, ejecuta los scripts y valida que `app.py` compile y levante sin errores.
