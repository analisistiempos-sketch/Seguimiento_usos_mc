import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import data_loader
import config_promedios

COLOR_TIPOS_DIA = {"Habil": "#1f77b4", "Sábado": "#ff7f0e", "Domingo": "#2ca02c", "Festivo": "#d62728", "Otro": "gray"}

def _tipo_dia(row):
    if str(row.get("Dia.tipo", "")).upper() == "H": return "Habil"
    if str(row.get("Dia.tipo", "")).upper() == "S": return "Sábado"
    if str(row.get("Dia.tipo", "")).upper() == "D": return "Domingo"
    if str(row.get("Dia.tipo", "")).upper() == "F": return "Festivo"
    return "Otro"

def _fechas_lineas(lineas):
    return [c["fecha"] for c in lineas if "fecha" in c]

def generar_barras():
    dias = data_loader.listar_dias_actual()
    if not dias:
        return go.Figure()
    ult_fecha = dias[-1]
    ini21 = ult_fecha - datetime.timedelta(days=config_promedios.ULTIMOS_DIAS_BARRAS - 1)
    df21 = data_loader.cargar_rango(ini21, ult_fecha, incluir_historico=False)
    
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
    lineas = getattr(config_promedios, "LINEAS", [])
    if not lineas:
        return go.Figure()
    
    fechas_cfg = _fechas_lineas(lineas)
    f_ini_cfg = min(pd.Timestamp(x) for x in fechas_cfg).date()
    f_fin_cfg = max(pd.Timestamp(x) for x in fechas_cfg).date()
    df_cfg = data_loader.cargar_rango(f_ini_cfg, f_fin_cfg, False)
    
    horas = list(range(24))
    hoy = datetime.date.today()
    hora_actual = datetime.datetime.now().hour
    fig = go.Figure()
    
    for linea in lineas:
        if "fecha" in linea:
            fecha_dt = pd.Timestamp(linea["fecha"]).date()
            es_hoy = (fecha_dt == hoy)
            df_dia = df_cfg[df_cfg["fecha"].dt.date == fecha_dt]
            serie = df_dia.groupby("hora")["Uso_pago"].sum()
            etiqueta = linea.get("etiqueta", str(fecha_dt))
        else:
            continue
        
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
