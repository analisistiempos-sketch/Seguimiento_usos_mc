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
    fig.update_layout(height=380, margin=dict(t=30, b=30),
                      xaxis=dict(dtick=1), legend_title_text=None)
    return fig


def figura_barras(cal, df21):
    bar21 = df21.groupby("fecha")["Uso_pago"].sum().reset_index()
    bar21 = bar21.sort_values("fecha")
    if cal is not None and not cal.empty:
        bar21 = bar21.merge(cal, on="fecha", how="left")
        bar21["Tipo"] = bar21.apply(_tipo_dia, axis=1)
        bar21["fecha_str"] = bar21["fecha"].dt.strftime("%d/%m/%Y") + " " + bar21["Dia.nombre"].str[:2].fillna("")
        bar21["texto"] = bar21["Uso_pago"].apply(lambda x: f"{x:,.0f}".replace(",", "."))
        fig = px.bar(
            bar21, x="Uso_pago", y="fecha_str", orientation="h", text="texto",
            color="Tipo", color_discrete_map=COLOR_TIPOS_DIA,
            labels={"Uso_pago": "Total Usos Pago", "fecha_str": "Día - Fecha", "Tipo": "Tipo de día"},
        )
    else:
        bar21["fecha_str"] = bar21["fecha"].dt.strftime("%d/%m/%Y")
        bar21["texto"] = bar21["Uso_pago"].apply(lambda x: f"{x:,.0f}".replace(",", "."))
        fig = px.bar(
            bar21, x="Uso_pago", y="fecha_str", orientation="h", text="texto",
            labels={"Uso_pago": "Total Usos Pago", "fecha_str": "Día - Fecha"},
        )
    fig.update_traces(textposition="inside")
    fig.update_layout(height=380, margin=dict(t=30, b=30),
                      yaxis=dict(categoryorder="array", categoryarray=bar21["fecha_str"], dtick=1))
    return fig


def _componer(fig_line, fig_bar, titulo=""):
    import copy
    import config_promedios
    fig_line_img = go.Figure(fig_line)
    fig_bar_img = go.Figure(fig_bar)
    
    fig_bar_img.update_layout(
        title=config_promedios.TITULO_BARRAS.format(n=config_promedios.ULTIMOS_DIAS_BARRAS), 
        title_font_size=22,
        margin=dict(t=60, l=160, r=20, b=30),
        xaxis_title="Usos",
        yaxis=dict(title=dict(text="Días", standoff=30), automargin=True, ticklabelstandoff=20)
    )
    fig_line_img.update_layout(
        title=config_promedios.TITULO_LINEAS_RESUMEN, 
        title_font_size=22,
        margin=dict(t=60, l=60, r=20, b=30),
        xaxis_title="Horas", yaxis_title="Usos"
    )

    img_line = fig_line_img.to_image(format="png", width=850, height=500, scale=1.0)
    img_bar = fig_bar_img.to_image(format="png", width=850, height=500, scale=1.0)

    im1 = Image.open(io.BytesIO(img_line))
    im2 = Image.open(io.BytesIO(img_bar))
    
    alto_logo = 80
    alto_pie = 60
    espacio_medio = 40
    ancho = im2.width + espacio_medio + im1.width
    alto_graficos = max(im1.height, im2.height)
    alto = alto_logo + alto_graficos + alto_pie
    canvas = Image.new("RGB", (ancho, alto), "white")
    draw = ImageDraw.Draw(canvas)
    
    logo_ruta = Path(__file__).resolve().parent / "logo.png"
    if logo_ruta.exists():
        try:
            logo = Image.open(logo_ruta).convert("RGBA")
            logo.thumbnail((240, 60), Image.LANCZOS)
            canvas.paste(logo, (20, 10), logo)
        except Exception:
            pass

    # Gráfica de barras a la izquierda, líneas a la derecha, con espacio en el medio
    canvas.paste(im2, (0, alto_logo))
    canvas.paste(im1, (im2.width + espacio_medio, alto_logo))

    try:
        fuente = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 16)
        fuente_negrita = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 16)
    except Exception:
        fuente = ImageFont.load_default()
        fuente_negrita = fuente
    
    draw.text((20, alto_logo + alto_graficos + 20), titulo, fill="gray", font=fuente)
    
    texto_dir = "DIRECCIÓN DE OPERACIONES - OFICINA DE EVALUACIÓN"
    bbox = draw.textbbox((0, 0), texto_dir, font=fuente_negrita)
    ancho_texto = bbox[2] - bbox[0]
    draw.text((ancho - ancho_texto - 20, alto_logo + alto_graficos + 20), texto_dir, fill="#333333", font=fuente_negrita)

    if canvas.width > 1700:
        nuevo_alto = round(1700 * canvas.height / canvas.width)
        canvas = canvas.resize((1700, nuevo_alto), Image.LANCZOS)
    return canvas


def exportar_bytes(fig_line, fig_bar, titulo="", formato="PNG"):
    canvas = _componer(fig_line, fig_bar, titulo)
    buf = io.BytesIO()
    if formato.upper() == "JPEG":
        canvas.convert("RGB").save(buf, format="JPEG", quality=92)
    else:
        canvas.save(buf, format="PNG")
    return buf.getvalue()


def exportar_png(destino, titulo=""):
    import generador_figuras
    fig_bar = generador_figuras.generar_barras()
    fig_line = generador_figuras.generar_lineas()
    datos = exportar_bytes(fig_line, fig_bar, titulo, "PNG")
    Path(destino).parent.mkdir(parents=True, exist_ok=True)
    Path(destino).write_bytes(datos)
    return destino


def exportar_jpeg(destino, titulo=""):
    import generador_figuras
    fig_bar = generador_figuras.generar_barras()
    fig_line = generador_figuras.generar_lineas()
    datos = exportar_bytes(fig_line, fig_bar, titulo, "JPEG")
    Path(destino).parent.mkdir(parents=True, exist_ok=True)
    Path(destino).write_bytes(datos)
    return destino
