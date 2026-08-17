import base64
import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import config_promedios
import data_loader
import kpi
import resumen_image

st.set_page_config(page_title="Tablero de Usos", layout="wide", initial_sidebar_state="expanded")


def _css_fondo():
    ruta = Path(__file__).resolve().parent / "fondo_vacio.jpg"
    if not ruta.exists():
        return ""
    b64 = base64.b64encode(ruta.read_bytes()).decode()
    return (
        "<style>.stApp{background-image:url(\"data:image/jpeg;base64,"
        + b64
        + "\");background-size:cover;background-position:center;background-attachment:fixed;}</style>"
    )


st.markdown(_css_fondo(), unsafe_allow_html=True)

_logo = Path(__file__).resolve().parent / "logo.png"
if _logo.exists():
    st.image(str(_logo), width=210)


@st.cache_data(ttl=300, show_spinner="Cargando datos de usos...")
def cargar_datos(fecha_min, fecha_max, incluir_historico):
    return data_loader.cargar_rango(fecha_min, fecha_max, incluir_historico=incluir_historico)


@st.cache_data(ttl=3600)
def cargar_dim():
    return data_loader.cargar_dim_estacion()


@st.cache_data(ttl=3600)
def cargar_cal():
    return data_loader.cargar_calendario()


COLOR_TIPOS_DIA = {
    "Habíl": "#1F77B4",
    "Sábado": "#FF7F0E",
    "Domingo": "#2CA02C",
    "Festivo": "#D62728",
}


def _tipo_dia(fila):
    if fila["Dia.tipo"] == "Sab":
        return "Sábado"
    if fila["Dia.tipo"] == "Hab":
        return "Habíl"
    if fila.get("Dia.nombre") == "Domingo":
        return "Domingo"
    return "Festivo"


def nombre_amigable(nombre):
    return str(nombre).replace("_", " ")


def _con_corredor(df, dim):
    df = df.copy()
    if dim is not None and not dim.empty:
        mapa = (
            dim[["estacion_ruta", "corredor_servicio", "zona"]]
            .drop_duplicates(subset=["estacion_ruta"])
            .copy()
        )
        mapa["_k"] = mapa["estacion_ruta"].astype(str).str.strip().str.upper()
        df = df.drop(columns=["corredor_servicio", "zona"], errors="ignore")
        df["_k"] = df["Nombre_estacion"].astype(str).str.strip().str.upper()
        df = df.merge(mapa[["_k", "corredor_servicio", "zona"]], on="_k", how="left")
        df = df.drop(columns=["_k"])
        df["corredor_servicio"] = df["corredor_servicio"].fillna("Sin corredor")
        df["zona"] = df["zona"].fillna("Sin zona")
    else:
        df["corredor_servicio"] = "Sin corredor"
        df["zona"] = "Sin zona"
    return df


def _aplicar_filtros(df, dim, corredores, estaciones, zonas=None):
    df = _con_corredor(df, dim)
    excluidos = config_promedios.CORREDORES_EXCLUIDOS
    if excluidos:
        df = df[~df["corredor_servicio"].isin(excluidos)]
    zonas_excl = config_promedios.ZONAS_EXCLUIDAS
    if zonas_excl:
        df = df[~df["zona"].isin(zonas_excl)]
    if corredores:
        df = df[df["corredor_servicio"].isin(corredores)]
    if zonas:
        df = df[df["zona"].isin(zonas)]
    if estaciones:
        df = df[df["Nombre_estacion"].isin(estaciones)]
    return df


def _lineas_config():
    return [l for l in config_promedios.LINEAS if l.get("mostrar", True)]


def _fechas_lineas(lineas):
    fechas = []
    for l in lineas:
        if "fecha" in l:
            fechas.append(l["fecha"])
        else:
            fechas += [l["desde"], l["hasta"]]
    return fechas


def _figura_lineas(df, lineas):
    horas = list(range(24))
    # Usar la hora de Colombia (UTC-5) para determinar si es "hoy"
    colombia_tz = datetime.timezone(datetime.timedelta(hours=-5))
    hoy = datetime.datetime.now(colombia_tz).date()
    hora_actual = datetime.datetime.now(colombia_tz).hour
    fig = go.Figure()
    for linea in lineas:
        if "fecha" in linea:
            serie = kpi.serie_dia_por_hora(df, linea["fecha"])
            etiqueta = linea.get("nombre") or pd.Timestamp(linea["fecha"]).strftime("%d/%m")
            # Si la línea es de hoy, no mostrar las horas futuras sin dato
            es_hoy = pd.Timestamp(linea["fecha"]).date() == hoy
        else:
            ref = df[df["fecha"].between(pd.Timestamp(linea["desde"]), pd.Timestamp(linea["hasta"]))]
            serie = kpi.promedio_por_hora(ref)
            etiqueta = linea.get("nombre") or (
                f"Prom. {pd.Timestamp(linea['desde']).strftime('%d/%m')}-"
                f"{pd.Timestamp(linea['hasta']).strftime('%d/%m')}"
            )
            es_hoy = False
        if es_hoy:
            max_hora = max(serie.keys()) if not serie.empty else -1
            y_vals = [serie.get(h, 0) if h <= max_hora else None for h in horas]
        else:
            y_vals = [serie.get(h, 0) for h in horas]
        fig.add_trace(go.Scatter(
            x=horas, y=y_vals, name=etiqueta,
            line=dict(color=linea["color"], dash=linea["estilo"]),
            connectgaps=False,
        ))
    fig.update_layout(
        height=420, hovermode="x unified",
        xaxis=dict(dtick=1), yaxis=dict(),
        legend_title_text=None
    )
    return fig


# ------------------------------------------------------------------ DATOS Y FILTROS
dias = data_loader.listar_dias_actual()
hoy = datetime.date.today()
fecha_max = dias[-1] if dias else hoy
dias_barras = getattr(config_promedios, "ULTIMOS_DIAS_BARRAS", 21)
fecha_min = fecha_max - datetime.timedelta(days=dias_barras - 1)
incluir_historico = config_promedios.INCLUIR_HISTORICO

df = cargar_datos(fecha_min, fecha_max, incluir_historico)
if df.empty:
    st.warning("No hay datos en el rango seleccionado.")
    st.stop()

dim = cargar_dim()
df_cc = _con_corredor(df, dim)

excluidos = getattr(config_promedios, "CORREDORES_EXCLUIDOS", [])
if excluidos:
    df_cc = df_cc[~df_cc["corredor_servicio"].isin(excluidos)]
zonas_excl = getattr(config_promedios, "ZONAS_EXCLUIDAS", [])
if zonas_excl:
    df_cc = df_cc[~df_cc["zona"].isin(zonas_excl)]

st.sidebar.title("Filtros")
corredores_disp = sorted(x for x in df_cc["corredor_servicio"].unique() if x)
filtro_corr = st.sidebar.multiselect("Corredor", corredores_disp, placeholder="Todos")

zonas_disp = sorted(x for x in df_cc["zona"].unique() if x)
filtro_zona = st.sidebar.multiselect("Zona", zonas_disp, placeholder="Todas")

if filtro_corr or filtro_zona:
    m = pd.Series(True, index=df_cc.index)
    if filtro_corr:
        m &= df_cc["corredor_servicio"].isin(filtro_corr)
    if filtro_zona:
        m &= df_cc["zona"].isin(filtro_zona)
    est_opciones = sorted(df_cc.loc[m, "Nombre_estacion"].unique())
else:
    est_opciones = sorted(df_cc["Nombre_estacion"].unique())

filtro_est = st.sidebar.multiselect(
    "Ruta Estacion", options=est_opciones, format_func=nombre_amigable, placeholder="Todas"
)

df_filtrado = df_cc
if filtro_corr:
    df_filtrado = df_filtrado[df_filtrado["corredor_servicio"].isin(filtro_corr)]
if filtro_zona:
    df_filtrado = df_filtrado[df_filtrado["zona"].isin(filtro_zona)]
if filtro_est:
    df_filtrado = df_filtrado[df_filtrado["Nombre_estacion"].isin(filtro_est)]

# ------------------------------------------------------------------ RESUMEN
col_barras, col_linea = st.columns(2)

with col_barras:
    st.subheader(config_promedios.TITULO_BARRAS.format(n=config_promedios.ULTIMOS_DIAS_BARRAS))
    ult_fecha = df["fecha"].max().date()
    ini21 = ult_fecha - datetime.timedelta(days=config_promedios.ULTIMOS_DIAS_BARRAS - 1)
    df21 = cargar_datos(ini21, ult_fecha, incluir_historico)
    df21 = _aplicar_filtros(df21, dim, filtro_corr, filtro_est, filtro_zona)
    bar21 = df21.groupby("fecha")["Uso_pago"].sum().reset_index()
    bar21 = bar21.sort_values("fecha", ascending=False)
    cal = cargar_cal()
    if cal is not None and not cal.empty:
        bar21 = bar21.merge(cal, on="fecha", how="left")
        bar21["Tipo"] = bar21.apply(_tipo_dia, axis=1)
        bar21["fecha_str"] = bar21["fecha"].dt.strftime("%d/%m/%Y") + " " + bar21["Dia.nombre"].str[:2].fillna("")
        bar21["texto"] = bar21["Uso_pago"].apply(lambda x: f"{x:,.0f}".replace(",", "."))
        fig_bar21 = px.bar(
            bar21, x="Uso_pago", y="fecha_str", orientation="h", text="texto",
            color="Tipo", color_discrete_map=COLOR_TIPOS_DIA,
            labels={"Uso_pago": "Total Usos Pago", "fecha_str": "Día - Fecha", "Tipo": "Tipo de día"},
        )
    else:
        bar21["fecha_str"] = bar21["fecha"].dt.strftime("%d/%m/%Y")
        bar21["texto"] = bar21["Uso_pago"].apply(lambda x: f"{x:,.0f}".replace(",", "."))
        fig_bar21 = px.bar(
            bar21, x="Uso_pago", y="fecha_str", orientation="h", text="texto",
            labels={"Uso_pago": "Total Usos Pago", "fecha_str": "Día - Fecha"},
        )
    fig_bar21.update_traces(
        insidetextfont=dict(size=12, color="white"),
        outsidetextfont=dict(size=12, color="black"),
        insidetextanchor="end",
        cliponaxis=False
    )
    for trace in fig_bar21.data:
        if trace.x is not None:
            trace.textposition = ["outside" if val is not None and val < 60000 else "inside" for val in trace.x]
    
    fig_bar21.update_layout(
        height=500, margin=dict(r=20, t=30, b=30),
        xaxis_title="", yaxis_title="",
        yaxis=dict(categoryorder="array", categoryarray=bar21["fecha_str"], dtick=1, automargin=True, ticklabelstandoff=20),
        uniformtext_minsize=12, uniformtext_mode="show"
    )
    st.plotly_chart(fig_bar21, width="stretch", key="fig_barras_resumen")

with col_linea:
    st.subheader(config_promedios.TITULO_LINEAS_RESUMEN)
    lineas = _lineas_config()
    if lineas:
        fechas_cfg = _fechas_lineas(lineas)
        f_ini_cfg = min(pd.Timestamp(x) for x in fechas_cfg).date()
        f_fin_cfg = max(pd.Timestamp(x) for x in fechas_cfg).date()
        df_cfg = cargar_datos(f_ini_cfg, f_fin_cfg, incluir_historico)
        df_cfg = _aplicar_filtros(df_cfg, dim, filtro_corr, filtro_est, filtro_zona)
        fig_linea = _figura_lineas(df_cfg, lineas)
        st.plotly_chart(fig_linea, width="stretch", key="fig_lineas_resumen")
    else:
        fig_linea = go.Figure()
        st.info("Configura LINEAS en config_promedios.py (con mostrar: True).")

# ------------------------------------------------------------------ ENCABEZADO Y PIE
actualizacion = data_loader.fecha_actualizacion()
if actualizacion:
    texto_ultimo = f"Datos actualizados al: {actualizacion.strftime('%d/%m/%Y %I:%M %p')}"
else:
    texto_ultimo = "Sin datos"

col_pie1, col_pie2 = st.columns([1, 1])
col_pie1.caption(f"**{texto_ultimo}**")
col_pie2.markdown("<div style='text-align: right; color: gray; font-size: 0.85em; font-weight: bold; margin-top: 5px;'>DIRECCIÓN DE OPERACIONES - OFICINA DE EVALUACIÓN</div>", unsafe_allow_html=True)

try:
    png_bytes = resumen_image.exportar_bytes(fig_linea, fig_bar21, texto_ultimo, "PNG")
    st.download_button(
        "Descargar imagen del Resumen",
        data=png_bytes,
        file_name="resumen_usos.png",
        mime="image/png",
        key="btn_descargar_resumen",
    )
except Exception as e:
    st.caption(f"No se pudo generar la imagen: {e}")
