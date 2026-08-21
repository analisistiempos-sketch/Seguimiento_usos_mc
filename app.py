import streamlit as st

st.set_page_config(page_title="Seguimiento de Usos", layout="wide")

pg = st.navigation(
    [
        st.Page("vistas/0_seguimiento_diario.py", title="Seguimiento diario", default=True, icon="📊"),
        st.Page("vistas/2_semanal.py", title="Semanal", icon="📅"),
    ]
)
pg.run()
