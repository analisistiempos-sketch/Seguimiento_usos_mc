import datetime
import io
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image, ImageDraw, ImageFont

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


def con_corredor(df, dim):
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


def lineas_config():
    return [l for l in config_promedios.LINEAS if l.get("mostrar", True)]


def fechas_lineas(lineas):
    fechas = []
    for l in lineas:
        if "fecha" in l:
            fechas.append(l["fecha"])
        else:
            fechas += [l["desde"], l["hasta"]]
    return fechas


def figura_lineas(df, lineas):
    horas = list(range(24))
    fig = go.Figure()
    for linea in lineas:
        if "fecha" in linea:
            serie = kpi.serie_dia_por_hora(df, linea["fecha"])
            etiqueta = linea.get("nombre") or pd.Timestamp(linea["fecha"]).strftime("%d/%m")
        else:
            ref = df[df["fecha"].between(pd.Timestamp(linea["desde"]), pd.Timestamp(linea["hasta"]))]
            serie = kpi.promedio_por_hora(ref)
            etiqueta = linea.get("nombre") or (
                f"Prom. {pd.Timestamp(linea['desde']).strftime('%d/%m')}-"
                f"{pd.Timestamp(linea['hasta']).strftime('%d/%m')}"
            )
        fig.add_trace(go.Scatter(
            x=horas, y=[serie.get(h, 0) for h in horas], name=etiqueta,
            line=dict(color=linea["color"], dash=linea["estilo"]),
        ))
    fig.update_layout(height=380, margin=dict(t=30, b=30, l=10, r=10),
                      xaxis=dict(dtick=1), legend_title_text=None)
    return fig


def figura_barras(cal, df21):
    bar21 = df21.groupby("fecha")["Uso_pago"].sum().reset_index()
    bar21 = bar21.sort_values("fecha")
    if cal is not None and not cal.empty:
        bar21 = bar21.merge(cal, on="fecha", how="left")
        bar21["Tipo"] = bar21.apply(_tipo_dia, axis=1)
        fig = px.bar(
            bar21, x="Uso_pago", y="fecha", orientation="h",
            color="Tipo", color_discrete_map=COLOR_TIPOS_DIA,
            labels={"Uso_pago": "Usos", "fecha": "Día", "Tipo": "Tipo de día"},
        )
    else:
        fig = px.bar(
            bar21, x="Uso_pago", y="fecha", orientation="h",
            labels={"Uso_pago": "Usos", "fecha": "Día"},
        )
    fig.update_layout(height=380, margin=dict(t=30, b=30, l=10, r=10),
                      yaxis=dict(categoryorder="array", categoryarray=bar21["fecha"]))
    return fig


def _componer(titulo=""):
    lineas = lineas_config()
    fechas = fechas_lineas(lineas)
    f_ini = min(pd.Timestamp(x) for x in fechas).date()
    f_fin = max(pd.Timestamp(x) for x in fechas).date()
    df = data_loader.cargar_rango(f_ini, f_fin, incluir_historico=True)
    fig_line = figura_lineas(df, lineas)

    cal = data_loader.cargar_calendario()
    dias = data_loader.listar_dias_actual()
    ult = dias[-1]
    ini21 = ult - datetime.timedelta(days=config_promedios.ULTIMOS_DIAS_BARRAS - 1)
    df21 = data_loader.cargar_rango(ini21, ult, incluir_historico=True)
    fig_bar = figura_barras(cal, df21)

    img_line = fig_line.to_image(format="png", width=660, height=440, scale=1.0)
    img_bar = fig_bar.to_image(format="png", width=620, height=440, scale=1.0)

    im1 = Image.open(io.BytesIO(img_line))
    im2 = Image.open(io.BytesIO(img_bar))
    alto_titulo = 70
    ancho = im1.width + im2.width
    alto = max(im1.height, im2.height) + alto_titulo
    canvas = Image.new("RGB", (ancho, alto), "white")
    draw = ImageDraw.Draw(canvas)
    try:
        fuente = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 26)
    except Exception:
        fuente = ImageFont.load_default()
    x_texto = 20
    logo_ruta = Path(__file__).resolve().parent / "logo.png"
    if logo_ruta.exists():
        try:
            logo = Image.open(logo_ruta).convert("RGBA")
            logo.thumbnail((240, 50), Image.LANCZOS)
            canvas.paste(logo, (16, (alto_titulo - logo.height) // 2), logo)
            x_texto = 16 + logo.width + 14
        except Exception:
            pass
    draw.text((x_texto, 18), titulo, fill="black", font=fuente)
    canvas.paste(im1, (0, alto_titulo))
    canvas.paste(im2, (im1.width, alto_titulo))
    if canvas.width > 1280:
        nuevo_alto = round(1280 * canvas.height / canvas.width)
        canvas = canvas.resize((1280, nuevo_alto), Image.LANCZOS)
    return canvas


def exportar_bytes(titulo="", formato="PNG"):
    canvas = _componer(titulo)
    buf = io.BytesIO()
    if formato.upper() == "JPEG":
        canvas.convert("RGB").save(buf, format="JPEG", quality=92)
    else:
        canvas.save(buf, format="PNG")
    return buf.getvalue()


def exportar_png(destino, titulo=""):
    datos = exportar_bytes(titulo, "PNG")
    Path(destino).parent.mkdir(parents=True, exist_ok=True)
    Path(destino).write_bytes(datos)
    return destino


def exportar_jpeg(destino, titulo=""):
    datos = exportar_bytes(titulo, "JPEG")
    Path(destino).parent.mkdir(parents=True, exist_ok=True)
    Path(destino).write_bytes(datos)
    return destino
