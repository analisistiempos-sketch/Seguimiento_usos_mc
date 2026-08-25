import base64
import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
TIPOS = ("Habíl", "Sábado", "Domingo/Festivo")


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


def _label_base():
    return semana_base


def _label_post():
    return "Promedio después del terremoto"


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
totales_semana = df.copy()
totales_semana["Semana"] = totales_semana["fecha"].map(_semana_de)
totales_semana = totales_semana[totales_semana["Semana"] != "Fuera"]
semanas_con_datos = set(totales_semana.groupby("Semana")["Uso_pago"].sum().loc[lambda s: s > 0].index)

tabla_total, tabla_prom, tabla_var = [], [], []
prom_base = {}
semanas_visibles = [n for n in semanas.keys() if n in semanas_con_datos]
for nombre in semanas_visibles:
    s = semanas[nombre]
    sub = df[(df["fecha"] >= pd.Timestamp(s["desde"])) & (df["fecha"] <= pd.Timestamp(s["hasta"]))]
    diario = sub.groupby("fecha")["Uso_pago"].sum()
    tipo_de_dia = sub.groupby("fecha")["Tipo_dia"].first()
    fila_total = {"Semana": nombre}
    fila_prom = {"Semana": nombre}
    for tipo in TIPOS:
        idx = tipo_de_dia[tipo_de_dia == tipo].index
        fila_total[f"Total {tipo}"] = int(diario.reindex(idx).sum())
        # Promedio SOLO con días completos (excluye el día actual, incompleto)
        idx_comp = [d for d in idx if d.date() < datetime.date.today()]
        fila_prom[f"Prom {tipo}"] = int(round(diario.reindex(idx_comp).mean())) if len(idx_comp) else 0
    tabla_total.append(fila_total)
    tabla_prom.append(fila_prom)
    if nombre == semana_base:
        prom_base = {t: fila_prom[f"Prom {t}"] for t in TIPOS}

for nombre, fila in zip(semanas_visibles, tabla_prom):
    fila_var = {"Semana": nombre}
    for tipo in TIPOS:
        if not prom_base.get(tipo):
            fila_var[f"Var {tipo}"] = "N/D"
        else:
            fila_var[f"Var {tipo}"] = _pct((fila[f"Prom {tipo}"] - prom_base[tipo]) / prom_base[tipo])
    tabla_var.append(fila_var)


def _estilo_num(df_):
    s = df_.style
    cols_num = [c for c in df_.columns[1:] if pd.api.types.is_numeric_dtype(df_[c])]
    s = s.set_properties(subset=df_.columns[1:].tolist(), **{"text-align": "right"})
    s = s.set_properties(subset=[df_.columns[0]], **{"text-align": "left"})
    if cols_num:
        s = s.format({c: "{:,.0f}" for c in cols_num})
    return s


def _estilo_var(df_):
    s = _estilo_num(df_)
    cols_var = [c for c in df_.columns if c.startswith("Var ")]
    if cols_var:
        s = s.apply(
            lambda row: [("color: #D62728; font-weight: bold" if isinstance(v, str) and v.startswith("-") else "") for v in row],
            subset=cols_var, axis=1,
        )
    return s


c1, c2, c3 = st.columns(3)
with c1:
    st.subheader("1. Total de usos por día tipo")
    st.dataframe(_estilo_num(pd.DataFrame(tabla_total)), hide_index=True, width="stretch", height=200)
with c2:
    st.subheader("2. Promedio de usos por día tipo")
    st.dataframe(_estilo_num(pd.DataFrame(tabla_prom)), hide_index=True, width="stretch", height=200)
with c3:
    st.subheader("3. Variación vs pre")
    st.dataframe(_estilo_var(pd.DataFrame(tabla_var)), hide_index=True, width="stretch", height=200)

# ---------------- comportamiento por hora (promedio) ----------------
st.subheader("4. Comportamiento por hora (promedio)")
df_hora = df.copy()
df_hora["Semana"] = df_hora["fecha"].map(_semana_de)
df_hora = df_hora[df_hora["Semana"] != "Fuera"]
por_hora = df_hora.groupby(["Semana", "hora"])["Uso_pago"].sum().reset_index()
n_dias = df_hora.groupby("Semana")["fecha"].nunique().rename("n_dias")
por_hora = por_hora.merge(n_dias, on="Semana")
por_hora["Promedio"] = por_hora["Uso_pago"] / por_hora["n_dias"]

# rejilla completa solo para semanas con datos, horas 4-23
horas_linea = list(range(4, 24))
grid = pd.DataFrame(
    [(s, h) for s in semanas.keys() if s in semanas_con_datos for h in horas_linea],
    columns=["Semana", "hora"],
)
por_hora = por_hora.merge(grid, on=["Semana", "hora"], how="right")
por_hora["Promedio"] = por_hora["Promedio"].fillna(0)
por_hora = por_hora.sort_values("hora")

color_map = {nombre: s["color"] for nombre, s in semanas.items()}
fig_hora = px.line(
    por_hora, x="hora", y="Promedio", color="Semana",
    color_discrete_map=color_map,
    category_orders={"Semana": list(semanas.keys())},
    labels={"hora": "Hora", "Promedio": "Promedio de usos", "Semana": ""},
)
fig_hora.update_layout(height=450, xaxis=dict(dtick=1, range=[4, 23]), legend_title_text=None)
st.plotly_chart(fig_hora, width="stretch")
st.caption("Promedio de usos por hora = total de esa hora en la semana ÷ días de esa semana con datos.")


# ---------------- sección de afectación ----------------
def _proyectar(datos, grupo_col, entidad):
    sub = datos[datos[grupo_col].astype(str).str.replace("_", " ").str.strip() == entidad.strip()]
    if sub.empty:
        sub = datos[datos[grupo_col] == entidad]
    sub = sub.copy()
    if sub.empty or len(sub) < 10:
        st.info("Datos insuficientes para proyectar esta entidad.")
        return
    sub = sub.groupby(["fecha", "Tipo_dia"], as_index=False)["Uso_pago"].sum()
    sub = sub[sub["fecha"].dt.date < datetime.date.today()]
    sub["dia_semana"] = sub["fecha"].dt.weekday
    sub["dias_desde_evento"] = (sub["fecha"] - pd.Timestamp("2026-08-10")).dt.days

    X = pd.get_dummies(sub[["dia_semana", "Tipo_dia", "dias_desde_evento"]], columns=["Tipo_dia"], drop_first=True)
    y = sub["Uso_pago"].astype(float)

    from sklearn.ensemble import RandomForestRegressor

    modelo = RandomForestRegressor(n_estimators=200, max_depth=4, random_state=42)
    modelo.fit(X, y)

    ult = sub["fecha"].max()
    fechas_pred = [ult + pd.Timedelta(days=i) for i in range(1, 8)]
    cal = data_loader.cargar_calendario()
    tipos_pred = []
    for f in fechas_pred:
        t = "Habíl"
        if cal is not None and not cal.empty:
            fila = cal[cal["fecha"] == f]
            if not fila.empty:
                t = generador_figuras._tipo_dia({"Dia.tipo": fila["Dia.tipo"].iloc[0], "Dia.nombre": fila["Dia.nombre"].iloc[0]})
        tipos_pred.append(t)
    X_pred = pd.DataFrame({
        "dia_semana": [f.weekday() for f in fechas_pred],
        "dias_desde_evento": [(f - pd.Timestamp("2026-08-10")).days for f in fechas_pred],
        "Tipo_dia": tipos_pred,
    })
    X_pred = pd.get_dummies(X_pred, columns=["Tipo_dia"], drop_first=True)
    X_pred = X_pred.reindex(columns=X.columns, fill_value=0)
    y_pred = modelo.predict(X_pred)

    hist = sub.groupby("fecha")["Uso_pago"].sum().reset_index()
    pre_val = float(hist[hist["fecha"] <= pd.Timestamp("2026-08-09")]["Uso_pago"].mean())

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist["fecha"], y=hist["Uso_pago"], name="Histórico",
                             line=dict(color="#1F77B4")))
    fig.add_trace(go.Scatter(x=fechas_pred, y=y_pred, name="Proyección 7 días",
                             line=dict(color="#D62728", dash="dot")))
    fig.add_hline(y=pre_val, line_dash="dash", line_color="#7F7F7F",
                  annotation_text=f"Pre-sismo ({pre_val:,.0f})")
    fig.update_layout(title=f"Proyección de usos — {entidad}", height=420,
                      xaxis_title="Fecha", yaxis_title="Usos", legend_title_text=None)
    st.plotly_chart(fig, width="stretch")


def _seccion_afectacion(datos, grupo_col, titulo):
    st.subheader(titulo)
    if datos.empty:
        st.info("Sin datos para esta selección.")
        return

    # 1) Totales DIARIOS por entidad (antes de cualquier promedio)
    diario = datos.groupby([grupo_col, "fecha"])["Uso_pago"].sum().reset_index()
    diario = diario.rename(columns={grupo_col: "Nombre", "Uso_pago": "Total"})
    diario["Nombre"] = diario["Nombre"].astype(str).str.replace("_", " ")
    tipo_por_dia = datos.groupby("fecha")["Tipo_dia"].first()
    diario["Tipo_dia"] = diario["fecha"].map(tipo_por_dia)

    # Pre-sismo: promedio de los totales diarios en la semana base (3 - 9 ago)
    base_s = semanas[semana_base]
    base_dias = diario[(diario["fecha"] >= pd.Timestamp(base_s["desde"])) & (diario["fecha"] <= pd.Timestamp(base_s["hasta"]))]
    pre = base_dias.groupby("Nombre")["Total"].mean().round(0).astype(int)

    # Último día HÁBIL COMPLETO: solo fechas con tipo "Habíl", sin incluir el día actual (incompleto)
    hoy = datetime.date.today()
    habiles = diario[(diario["Tipo_dia"] == "Habíl") & (diario["fecha"].dt.date < hoy)]
    if habiles.empty:
        habiles = diario
    ult_fecha = habiles["fecha"].max()
    ult = diario[diario["fecha"] == ult_fecha].set_index("Nombre")["Total"].astype(int)

    tabla = pd.DataFrame({"Nombre": pre.index})
    tabla["Pre-sismo"] = pre.values
    tabla["Último día hábil"] = ult.reindex(pre.index).fillna(0).values
    base_safe = pre.where(pre > 0)
    tabla["Variación %"] = (((tabla["Último día hábil"] - tabla["Pre-sismo"]) / base_safe.values) * 100).values
    tabla = tabla.sort_values("Variación %", ascending=True, na_position="last")

    # Aplicamos el estilo de barras de Pandas para el Impacto Visual en la Tabla
    estilo_tabla = tabla.style.bar(
        subset=["Variación %"],
        align="mid",
        color=["#D62728", "#2CA02C"],
        vmin=-100,
        vmax=100
    )

    fecha_str = ult_fecha.strftime('%d/%m/%Y')
    st.caption(f"💡 La **Variación %** compara el volumen de usos del **último día hábil registrado ({fecha_str})** contra el promedio diario de la semana **Pre-sismo**.")

    st.dataframe(
        estilo_tabla,
        column_config={
            "Nombre": st.column_config.TextColumn("Entidad"),
            "Pre-sismo": st.column_config.NumberColumn("Pre-sismo", format="%d"),
            "Último día hábil": st.column_config.NumberColumn(f"Último hábil ({fecha_str})", format="%d"),
            "Variación %": st.column_config.NumberColumn("Variación %", format="%+.1f %%"),
        },
        hide_index=True,
        width="stretch",
    )

    # Sistema de Pestañas para Gráficos
    tab1, tab2 = st.tabs(["📊 Gráfico General (Todas)", "📈 Proyección por Entidad"])

    with tab1:
        # Recuperamos el gráfico de barras gigante
        df_bar = tabla.dropna(subset=["Variación %"]).copy()
        df_bar["Variación %"] = df_bar["Variación %"].round(1)
        df_bar["Color"] = df_bar["Variación %"].apply(lambda x: "Subida" if x > 0 else "Caída")
        fig_bar = px.bar(
            df_bar, x="Variación %", y="Nombre", color="Color",
            color_discrete_map={"Subida": "#2CA02C", "Caída": "#D62728"},
            orientation="h", text="Variación %"
        )
        fig_bar.update_traces(texttemplate='%{text:+.1f}%', textposition='outside')
        fig_bar.update_layout(
            yaxis={'categoryorder': 'total ascending'}, 
            height=max(400, len(df_bar) * 25), # Ajuste automático de altura según cantidad
            showlegend=False, 
            xaxis_title="Variación %", 
            yaxis_title=""
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        entidades = tabla["Nombre"].tolist()
        entidad = st.selectbox("Entidad para proyectar", entidades, key=f"proy_{grupo_col}")
        _proyectar(datos, grupo_col, entidad)


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
