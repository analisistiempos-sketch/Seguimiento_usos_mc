import re
import pandas as pd


def dias_con_datos(df):
    if df.empty:
        return []
    por_dia = df.groupby("fecha")["Uso_pago"].sum()
    return por_dia[por_dia > 0].index.tolist()


def promedio_por_hora(df):
    if df.empty:
        return pd.Series(dtype="float64")
    dias = len(dias_con_datos(df))
    if dias == 0:
        return pd.Series(dtype="float64")
    return df.groupby("hora")["Uso_pago"].sum() / dias


def serie_dia_por_hora(df, fecha):
    sub = df[df["fecha"] == pd.Timestamp(fecha).normalize()]
    if sub.empty:
        return pd.Series(dtype="float64")
    return sub.groupby("hora")["Uso_pago"].sum()


def normalizar_tipo_dia(val):
    if not val or str(val).strip().lower() in ("todos", "none", "", "all"):
        return None
    s = str(val).strip().lower()
    if "hab" in s:
        return "Habíl"
    if "sab" in s:
        return "Sábado"
    if "dom" in s or "fest" in s or "fes" in s:
        return "Domingo/Festivo"
    return str(val)


def extraer_tipo_dia_nombre(nombre):
    if not nombre:
        return None
    s = str(nombre).lower()
    if re.search(r"(?:^|[_\s-])hab(?:il|íl)?(?:[_\s-]|$)", s):
        return "Habíl"
    if re.search(r"(?:^|[_\s-])sab(?:ado|ádo)?(?:[_\s-]|$)", s):
        return "Sábado"
    if re.search(r"(?:^|[_\s-])(?:dom|fes|festivo|domingo)(?:[_\s-]|$)", s):
        return "Domingo/Festivo"
    return None


def extraer_top_nombre(nombre):
    if not nombre:
        return None
    match = re.search(r"top[_\s-]*(\d+)", str(nombre), re.IGNORECASE)
    if match:
        try:
            return int(match.group(1))
        except (ValueError, TypeError):
            return None
    return None


def filtrar_top_dias(df, top=None):
    if df.empty or top is None or int(top) <= 0:
        return df
    por_dia = df.groupby("fecha")["Uso_pago"].sum()
    por_dia = por_dia[por_dia > 0]
    if por_dia.empty:
        return df
    top_fechas = por_dia.nlargest(int(top)).index
    return df[df["fecha"].isin(top_fechas)]


def _ref_de_linea(df, linea, cal=None, con_dia_tipo_fn=None, filtro_tipo_fallback=None):
    """Aplica a un rango (desde/hasta) el filtro de tipo de día y el Top N días.

    Devuelve (ref_filtrado, tipo_dia, top_n, n_candidatos), donde n_candidatos es
    el número de días que quedaron antes de aplicar el Top N.
    """
    ref = df[df["fecha"].between(pd.Timestamp(linea["desde"]), pd.Timestamp(linea["hasta"]))]

    # 1. Determinar tipo de día
    tipo_dia = normalizar_tipo_dia(linea.get("tipo_dia"))
    if not tipo_dia:
        tipo_dia = extraer_tipo_dia_nombre(linea.get("nombre"))
    if not tipo_dia and filtro_tipo_fallback:
        # Si se pasó una lista o valor único desde el filtro global
        if isinstance(filtro_tipo_fallback, (list, tuple, set)) and len(filtro_tipo_fallback) == 1:
            tipo_dia = normalizar_tipo_dia(list(filtro_tipo_fallback)[0])
        elif isinstance(filtro_tipo_fallback, str):
            tipo_dia = normalizar_tipo_dia(filtro_tipo_fallback)

    if tipo_dia:
        if "Tipo_dia" not in ref.columns and con_dia_tipo_fn is not None:
            ref = con_dia_tipo_fn(ref, cal)
        elif "Tipo_dia" not in ref.columns and cal is not None and not cal.empty:
            mapa = cal[["fecha", "Dia.tipo"]].drop_duplicates(subset=["fecha"])
            ref = ref.merge(mapa, on="fecha", how="left")
            ref["Tipo_dia"] = ref["Dia.tipo"].map({"Sab": "Sábado", "Hab": "Habíl"}).fillna("Domingo/Festivo")

        if "Tipo_dia" in ref.columns:
            ref = ref[ref["Tipo_dia"] == tipo_dia]

    # 2. Filtrar Top N días con más usos (si aplica)
    n_candidatos = int(ref["fecha"].nunique())
    top_n = linea.get("top")
    if top_n is None:
        top_n = extraer_top_nombre(linea.get("nombre"))
    top_n = int(top_n) if top_n and int(top_n) > 0 else None
    if top_n:
        ref = filtrar_top_dias(ref, top_n)

    return ref, tipo_dia, top_n, n_candidatos


def calcular_serie_linea(df, linea, cal=None, con_dia_tipo_fn=None, filtro_tipo_fallback=None):
    """
    Calcula la serie por hora para una configuración de línea en el gráfico.
    Soporta:
      - 'fecha': serie de un día específico.
      - 'desde' / 'hasta': rango de fechas promedio.
        - 'tipo_dia': 'Habíl', 'Sábado', 'Domingo/Festivo' o None/'Todos'.
        - 'top': número N de días con mayor demanda (None o 0 para todo el periodo).
    """
    if "fecha" in linea:
        serie = serie_dia_por_hora(df, linea["fecha"])
        etiqueta = linea.get("nombre") or pd.Timestamp(linea["fecha"]).strftime("%d/%m")
        return serie, etiqueta

    ref, tipo_dia, top_n, _ = _ref_de_linea(df, linea, cal, con_dia_tipo_fn, filtro_tipo_fallback)
    serie = promedio_por_hora(ref)

    # 3. Etiqueta
    if linea.get("nombre"):
        etiqueta = linea["nombre"]
    else:
        partes = ["Prom."]
        if top_n:
            partes.append(f"Top {top_n}")
        if tipo_dia:
            partes.append(tipo_dia)
        partes.append(
            f"{pd.Timestamp(linea['desde']).strftime('%d/%m')}-"
            f"{pd.Timestamp(linea['hasta']).strftime('%d/%m')}"
        )
        etiqueta = " ".join(partes)

    return serie, etiqueta


def describe_linea(df, linea, cal=None, con_dia_tipo_fn=None, filtro_tipo_fallback=None):
    """Metadatos de una línea para mostrarlos como diagnóstico.

    Devuelve: tipo (día/promedio), tipo_dia, top_n, n_dias (días realmente usados)
    y total (suma de la serie por hora = total/promedio diario).
    """
    if "fecha" in linea:
        sub = df[df["fecha"] == pd.Timestamp(linea["fecha"]).normalize()]
        return {
            "tipo": "día",
            "tipo_dia": None,
            "top": None,
            "n_dias": int(sub["fecha"].nunique()),
            "n_candidatos": int(sub["fecha"].nunique()),
            "total": float(sub["Uso_pago"].sum()),
        }

    ref, tipo_dia, top_n, n_candidatos = _ref_de_linea(df, linea, cal, con_dia_tipo_fn, filtro_tipo_fallback)
    return {
        "tipo": "promedio",
        "tipo_dia": tipo_dia,
        "top": top_n,
        "n_dias": int(ref["fecha"].nunique()),
        "n_candidatos": n_candidatos,
        "total": float(promedio_por_hora(ref).sum()),
    }
