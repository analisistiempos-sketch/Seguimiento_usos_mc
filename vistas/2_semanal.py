import base64
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

import config_promedios
import data_loader
import generador_figuras

st.set_page_config(page_title="Semanal - Terremoto", layout="wide")


def _ruta_recurso(nombre):
    p = Path(__file__).resolve().parent / nombre
    if not p.exists():
        p = Path(__file__).resolve().parent.parent / nombre
    return p


def _css_fondo():
    ruta = _ruta_recurso("fondo_vacio.jpg")
    if not ruta.exists():
        return ""
    b64 = base64.b64encode(ruta.read_bytes()).decode()
    return (
        "<style>.stApp{background-image:url(\"data:image/jpeg;base64,"
        + b64
        + "\");background-size:cover;background-position:center;background-attachment:fixed;}</style>"
    )


st.markdown(_css_fondo(), unsafe_allow_html=True)

_logo = _ruta_recurso("logo.png")
if _logo.exists():
    st.image(str(_logo), width=210)

st.title("Análisis semanal (Terremoto 10/08/2026)")
st.markdown("Comparación de usos por **día tipo** entre la semana previa, la del terremoto y la posterior. La variación es **vs la semana pre-terremoto**.")

semanas = config_promedios.SEMANAS_TERREMOTO
semana_base = config_promedios.SEMANA_BASE
TIPOS = ("Habíl", "Sábado", "Domingo")


def _con_dia_tipo(df, cal):
    df = df.copy()
    if cal is not None and not cal.empty:
        mapa = cal[["fecha", "Dia.tipo", "Dia.nombre"]].drop_duplicates(subset=["fecha"])
        df = df.merge(mapa, on="fecha", how="left")
        df["Tipo_dia"] = df.apply(generador_figuras._tipo_dia, axis=1)
    else:
        df["Tipo_dia"] = "Sin dato"
    return df


def _con_tipo_servicio(df, dim):
    if dim is not None and not dim.empty:
        mapa = dim[["estacion_ruta", "tipo_servicio_agrupado"]].drop_duplicates(subset=["estacion_ruta"]).copy()
        mapa["_k"] = mapa["estacion_ruta"].astype(str).str.strip().str.upper()
        df = df.copy()
        df["_k"] = df["Nombre_estacion"].astype(str).str.strip().str.upper()
        df = df.merge(mapa[["_k", "tipo_servicio_agrupado"]], on="_k", how="left")
        df = df.drop(columns=["_k"])
        df["tipo_servicio_agrupado"] = df["tipo_servicio_agrupado"].fillna("Sin tipo")
    else:
        df["tipo_servicio_agrupado"] = "Sin tipo"
    return df


def _var(actual, base):
    if base is None or base == 0:
        return None
    return (actual - base) / base


def _semana_de(f):
    for n, s in semanas.items():
        if pd.Timestamp(s["desde"]) <= f <= pd.Timestamp(s["hasta"]):
            return n
    return "Fuera"


def _pct(v):
    return f"{v:+.1%}" if v is not None else "—"


MESES_ES = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def _label_base():
    d = pd.Timestamp(semanas[semana_base]["desde"])
    h = pd.Timestamp(semanas[semana_base]["hasta"])
    return f"{d.day} al {h.day:02d} {MESES_ES[h.month].capitalize()}"


def _label_post():
    h = pd.Timestamp(semanas[semana_base]["hasta"])
    return f"Promedio después del {h.day:02d} {MESES_ES[h.month]}"


# ---------------- carga ----------------
f_ini = min(pd.Timestamp(s["desde"]) for s in semanas.values()).date()
f_fin = max(pd.Timestamp(s["hasta"]) for s in semanas.values()).date()
df = data_loader.cargar_rango(f_ini, f_fin, incluir_historico=False)
dim = data_loader.cargar_dim_estacion()
cal = data_loader.cargar_calendario()
df = generador_figuras._aplicar_filtros(df, dim)
df = _con_dia_tipo(df, cal)
df = _con_tipo_servicio(df, dim)

if df.empty:
    st.warning("No hay datos en el rango de las semanas configuradas.")
    st.stop()

# ---------------- filtros (igual que el Resumen) ----------------
st.sidebar.title("Filtros")
corredores_disp = sorted(x for x in df["corredor_servicio"].unique() if x)
filtro_corr = st.sidebar.multiselect("Corredor", corredores_disp, placeholder="Todos")

zonas_disp = sorted(x for x in df["zona"].unique() if x)
filtro_zona = st.sidebar.multiselect("Zona", zonas_disp, placeholder="Todas")

tipos_disp = sorted(x for x in df["Tipo_dia"].unique() if x)
filtro_tipo = st.sidebar.multiselect("Tipo de día", tipos_disp, placeholder="Todos")

if filtro_corr or filtro_zona:
    m = pd.Series(True, index=df.index)
    if filtro_corr:
        m &= df["corredor_servicio"].isin(filtro_corr)
    if filtro_zona:
        m &= df["zona"].isin(filtro_zona)
    est_disp = sorted(df.loc[m, "Nombre_estacion"].unique())
else:
    est_disp = sorted(df["Nombre_estacion"].unique())

filtro_est = st.sidebar.multiselect("Ruta/Estación", options=est_disp, format_func=lambda n: str(n).replace("_", " "), placeholder="Todas")

if filtro_corr:
    df = df[df["corredor_servicio"].isin(filtro_corr)]
if filtro_zona:
    df = df[df["zona"].isin(filtro_zona)]
if filtro_tipo:
    df = df[df["Tipo_dia"].isin(filtro_tipo)]
if filtro_est:
    df = df[df["Nombre_estacion"].isin(filtro_est)]

# ---------------- tablas por día tipo ----------------
tabla_total, tabla_prom, tabla_var = [], [], []
prom_base = {}
for nombre, s in semanas.items():
    sub = df[(df["fecha"] >= pd.Timestamp(s["desde"])) & (df["fecha"] <= pd.Timestamp(s["hasta"]))]
    diario = sub.groupby("fecha")["Uso_pago"].sum()
    tipo_de_dia = sub.groupby("fecha")["Tipo_dia"].first()
    fila_total = {"Semana": nombre}
    fila_prom = {"Semana": nombre}
    for tipo in TIPOS:
        idx = tipo_de_dia[tipo_de_dia == tipo].index
        total_tipo = int(diario.reindex(idx).sum())
        prom_tipo = round(diario.reindex(idx).mean(), 0) if len(idx) else 0
        fila_total[f"Total {tipo}"] = total_tipo
        fila_prom[f"Prom {tipo}"] = prom_tipo
    tabla_total.append(fila_total)
    tabla_prom.append(fila_prom)
    if nombre == semana_base:
        prom_base = {t: fila_prom[f"Prom {t}"] for t in TIPOS}

for nombre, fila in zip(semanas, tabla_prom):
    fila_var = {"Semana": nombre}
    for tipo in TIPOS:
        fila_var[f"Var {tipo}"] = _pct(_var(fila[f"Prom {tipo}"], prom_base.get(tipo)))
    tabla_var.append(fila_var)

c1, c2, c3 = st.columns(3)
with c1:
    st.subheader("1. Total de usos por día tipo")
    st.dataframe(pd.DataFrame(tabla_total), hide_index=True, width="stretch")
with c2:
    st.subheader("2. Promedio de usos por día tipo")
    st.dataframe(pd.DataFrame(tabla_prom), hide_index=True, width="stretch")
with c3:
    st.subheader("3. Variación del promedio vs pre-terremoto")
    st.dataframe(pd.DataFrame(tabla_var), hide_index=True, width="stretch")

# ---------------- comportamiento por hora (promedio) ----------------
st.subheader("4. Comportamiento por hora (promedio)")
df_hora = df.copy()
df_hora["Semana"] = df_hora["fecha"].map(_semana_de)
df_hora = df_hora[df_hora["Semana"] != "Fuera"]
por_hora = df_hora.groupby(["Semana", "hora"])["Uso_pago"].sum().reset_index()
n_dias = df_hora.groupby("Semana")["fecha"].nunique().rename("n_dias")
por_hora = por_hora.merge(n_dias, on="Semana")
por_hora["Promedio"] = por_hora["Uso_pago"] / por_hora["n_dias"]
fig_hora = px.line(
    por_hora, x="hora", y="Promedio", color="Semana",
    labels={"hora": "Hora", "Promedio": "Promedio de usos", "Semana": ""},
)
fig_hora.update_layout(height=450, xaxis=dict(dtick=1), legend_title_text=None)
st.plotly_chart(fig_hora, width="stretch")
st.caption("Promedio de usos por hora = total de esa hora en la semana ÷ días de esa semana con datos.")


# ---------------- sección de afectación ----------------
def _seccion_afectacion(datos, grupo_col, titulo):
    st.subheader(titulo)
    if datos.empty:
        st.info("Sin datos para esta selección.")
        return
    por = datos.groupby([grupo_col, "fecha"])["Uso_pago"].sum().reset_index()
    por["Semana"] = por["fecha"].map(_semana_de)
    por = por[por["Semana"] != "Fuera"]
    if por.empty:
        st.info("Sin datos.")
        return
    pivot = por.pivot_table(index=grupo_col, columns="Semana", values="Uso_pago", aggfunc="sum", fill_value=0)
    pivot = pivot[[c for c in semanas.keys() if c in pivot.columns]]
    if semana_base not in pivot.columns:
        st.info("No hay datos de la semana base.")
        return
    post = [c for c in pivot.columns if c != semana_base]
    pivot = pivot.reset_index().rename(columns={grupo_col: "Nombre"})
    pivot["Nombre"] = pivot["Nombre"].astype(str).str.replace("_", " ")
    base = pivot[semana_base].astype(float)
    pivot["Promedio post"] = pivot[post].astype(float).mean(axis=1) if post else 0.0
    base_safe = base.where(base > 0)
    pivot["Variación"] = ((pivot["Promedio post"] - base) / base_safe).astype(float)
    pivot["Variación %"] = pivot["Variación"].map(_pct)
    pivot = pivot.sort_values("Variación", ascending=True)

    pivot = pivot.rename(columns={semana_base: _label_base(), "Promedio post": _label_post(), "Variación %": "Variación Promedio"})
    resumen = pivot[["Nombre", _label_base(), _label_post(), "Variación Promedio"]]
    st.dataframe(resumen, hide_index=True, width="stretch")

    chart = pivot.dropna(subset=["Variación"])
    if not chart.empty:
        chart = chart.copy()
        fig = px.bar(
            chart, x="Variación", y="Nombre", orientation="h", text="Variación Promedio",
            color=(chart["Variación"] < 0).map({True: "Caída", False: "Subida"}),
            color_discrete_map={"Caída": "#D62728", "Subida": "#2CA02C"},
            title=f"{titulo} — todas",
            labels={"Variación": "Variación del promedio vs base", "Nombre": "", "color": ""},
        )
        fig.update_layout(
            height=max(500, len(chart) * 16),
            yaxis=dict(categoryorder="array", categoryarray=chart["Nombre"]),
        )
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, width="stretch")


# ---------------- afectación (con selector) ----------------
st.subheader("Afectación")
st.caption(f"Variación del **promedio de las semanas posteriores** vs la semana base ({_label_base()}).")
grupo = st.selectbox("Ver afectación de:", ["Estaciones", "Rutas", "Corredores"])
if grupo == "Estaciones":
    _seccion_afectacion(df[df["tipo_servicio_agrupado"] == "Estacion"], "Nombre_estacion", "🏢 Afectación estaciones")
elif grupo == "Rutas":
    rutas = df[df["tipo_servicio_agrupado"] != "Estacion"]
    rutas = rutas[rutas["Nombre_estacion"].astype(str).str[0].str.upper().isin(["A", "P", "T", "E"])]
    _seccion_afectacion(rutas, "Nombre_estacion", "🚌 Afectación rutas")
else:
    _seccion_afectacion(df, "corredor_servicio", "🛣️ Afectación corredores")
