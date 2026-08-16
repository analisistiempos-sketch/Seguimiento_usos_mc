import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import config_promedios
import data_loader
import kpi

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


def _aplicar_filtros(df, dim):
    df = _con_corredor(df, dim)
    excluidos = config_promedios.CORREDORES_EXCLUIDOS
    if excluidos:
        df = df[~df["corredor_servicio"].isin(excluidos)]
    zonas_excl = getattr(config_promedios, "ZONAS_EXCLUIDAS", [])
    if zonas_excl:
        df = df[~df["zona"].isin(zonas_excl)]
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


def generar_barras():
    dias = data_loader.listar_dias_actual()
    if not dias:
        return go.Figure()
    ult_fecha = dias[-1]
    ini21 = ult_fecha - datetime.timedelta(days=config_promedios.ULTIMOS_DIAS_BARRAS - 1)
    df21 = data_loader.cargar_rango(ini21, ult_fecha, incluir_historico=False)
    dim = data_loader.cargar_dim_estacion()
    df21 = _aplicar_filtros(df21, dim)

    if df21.empty:
        return go.Figure()

    bar21 = df21.groupby("fecha")["Uso_pago"].sum().reset_index()
    bar21 = bar21.sort_values("fecha", ascending=False)
    cal = data_loader.cargar_calendario()
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
    fig_bar21.update_traces(textposition="inside", textfont=dict(size=16, color="white"), insidetextanchor="end")
    fig_bar21.update_layout(
        height=500, margin=dict(r=20, t=30, b=30),
        xaxis_title="", yaxis_title="",
        yaxis=dict(categoryorder="array", categoryarray=bar21["fecha_str"], dtick=1, automargin=True, ticklabelstandoff=20),
        uniformtext_minsize=12, uniformtext_mode="show"
    )
    return fig_bar21


def generar_lineas():
    lineas = _lineas_config()
    if not lineas:
        return go.Figure()

    fechas_cfg = _fechas_lineas(lineas)
    f_ini_cfg = min(pd.Timestamp(x) for x in fechas_cfg).date()
    f_fin_cfg = max(pd.Timestamp(x) for x in fechas_cfg).date()
    df_cfg = data_loader.cargar_rango(f_ini_cfg, f_fin_cfg, incluir_historico=False)
    dim = data_loader.cargar_dim_estacion()
    df_cfg = _aplicar_filtros(df_cfg, dim)

    horas = list(range(24))
    hoy = datetime.date.today()
    fig = go.Figure()
    for linea in lineas:
        if "fecha" in linea:
            serie = kpi.serie_dia_por_hora(df_cfg, linea["fecha"])
            etiqueta = linea.get("nombre") or pd.Timestamp(linea["fecha"]).strftime("%d/%m")
            es_hoy = pd.Timestamp(linea["fecha"]).date() == hoy
        else:
            ref = df_cfg[df_cfg["fecha"].between(pd.Timestamp(linea["desde"]), pd.Timestamp(linea["hasta"]))]
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
