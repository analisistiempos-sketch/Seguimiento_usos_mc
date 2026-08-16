import datetime
import glob
import re
from pathlib import Path

import pandas as pd

import config

COLUMNAS = ["id_estacion", "Nombre_estacion", "fecha", "hora", "Uso_pago", "Integracion"]


def _parse_fecha_nombre(nombre):
    try:
        return pd.to_datetime(Path(nombre).stem, format="%d-%m-%Y").date()
    except Exception:
        return None


def _sincronizar_fuente():
    if config.FUENTE == "github":
        import github_data

        github_data.sync_desde_github(config.DATOS_ACTUAL_DIR)


def listar_dias_actual():
    if config.USOS_MOTOR == "duckdb":
        import db_duckdb

        return db_duckdb.listar_dias()
    _sincronizar_fuente()
    dias = set()
    for src in [config.DATOS_ACTUAL_DIR] + [config.SHAREPOINT_DIR / a for a in config.ANIOS_DIARIOS]:
        if not src.exists():
            continue
        for f in src.rglob("*.parquet"):
            d = _parse_fecha_nombre(f.name)
            if d is not None:
                dias.add(d)
    return sorted(dias)


def _leer(archivo):
    df = pd.read_parquet(archivo)
    for c in COLUMNAS:
        if c not in df.columns:
            df[c] = 0 if c == "id_estacion" else pd.NA
    df = df[COLUMNAS]
    df["Uso_pago"] = pd.to_numeric(df["Uso_pago"], errors="coerce").fillna(0).astype("int64")
    df["Integracion"] = pd.to_numeric(df["Integracion"], errors="coerce").fillna(0).astype("int64")
    return df


def cargar_rango(fecha_min, fecha_max, incluir_historico=True):
    if config.USOS_MOTOR == "duckdb":
        import db_duckdb

        df = db_duckdb.cargar_rango(fecha_min, fecha_max, incluir_historico)
        if df.empty:
            return df
        df["fecha"] = pd.to_datetime(df["fecha"]).dt.normalize()
        df = df.dropna(subset=["fecha", "Nombre_estacion"])
        df["Uso_pago"] = pd.to_numeric(df["Uso_pago"], errors="coerce").fillna(0).astype("int64")
        df["Integracion"] = pd.to_numeric(df["Integracion"], errors="coerce").fillna(0).astype("int64")
        if "id_estacion" in df.columns:
            df["id_estacion"] = df["id_estacion"].fillna(0).astype("int64")
        return df
    _sincronizar_fuente()
    fecha_min = pd.Timestamp(fecha_min).date()
    fecha_max = pd.Timestamp(fecha_max).date()
    frames = []

    for src in [config.DATOS_ACTUAL_DIR] + [config.SHAREPOINT_DIR / a for a in config.ANIOS_DIARIOS]:
        if not src.exists():
            continue
        for f in src.rglob("*.parquet"):
            d = _parse_fecha_nombre(f.name)
            if d is None:
                continue
            if fecha_min <= d <= fecha_max:
                frames.append(_leer(str(f)))

    if not incluir_historico:
        if not frames:
            return pd.DataFrame(columns=COLUMNAS)
        df = pd.concat(frames, ignore_index=True)
        df["fecha"] = pd.to_datetime(df["fecha"]).dt.normalize()
        df = df.dropna(subset=["fecha", "Nombre_estacion"])
        return df

    for anio in config.ANIOS_TRIMESTRALES:
        carpeta = config.SHAREPOINT_DIR / str(anio)
        if not carpeta.exists():
            continue
        for f in carpeta.rglob("*.parquet"):
            fechas = pd.read_parquet(str(f), columns=["fecha"])
            if fechas.empty:
                continue
            fmin = fechas["fecha"].min().date()
            fmax = fechas["fecha"].max().date()
            if fmax >= fecha_min and fmin <= fecha_max:
                frames.append(_leer(str(f)))

    for f in glob.glob(str(config.SHAREPOINT_DIR / "Usos_*.parquet")):
        fechas = pd.read_parquet(f, columns=["fecha"])
        if fechas.empty:
            continue
        fmin = fechas["fecha"].min().date()
        fmax = fechas["fecha"].max().date()
        if fmax >= fecha_min and fmin <= fecha_max:
            frames.append(_leer(f))

    if not frames:
        return pd.DataFrame(columns=COLUMNAS)

    df = pd.concat(frames, ignore_index=True)
    df["fecha"] = pd.to_datetime(df["fecha"]).dt.normalize()
    df = df.dropna(subset=["fecha", "Nombre_estacion"])
    return df


def fecha_actualizacion():
    dias = listar_dias_actual()
    if not dias:
        return None
    ultima = dias[-1]
    for src in [config.DATOS_ACTUAL_DIR] + [config.SHAREPOINT_DIR / a for a in config.ANIOS_DIARIOS]:
        archivo = src / f"{ultima.strftime('%d-%m-%Y')}.parquet"
        if archivo.exists():
            try:
                df = _leer(str(archivo))
                if not df.empty and "hora" in df.columns:
                    max_hora = df["hora"].max()
                    if pd.notna(max_hora):
                        # La hora del parquet suele ser 0-23
                        return datetime.datetime.combine(ultima, datetime.time(hour=int(max_hora), minute=59))
            except Exception:
                pass
            
            # Fallback
            utc_time = datetime.datetime.fromtimestamp(archivo.stat().st_mtime, tz=datetime.timezone.utc)
            colombia_tz = datetime.timezone(datetime.timedelta(hours=-5))
            return utc_time.astimezone(colombia_tz)
    return None


def _coord(valor):
    if pd.isna(valor) or str(valor).strip() in ("", "0"):
        return 0.0
    partes = re.findall(r"-?\d+", str(valor))
    if not partes:
        return 0.0
    num = float("".join(partes))
    return num / 1e6 if abs(num) > 180 else num


def cargar_dim_estacion():
    ruta = config.DIM_ESTACION_CSV
    if not ruta.exists():
        ruta = config.SHAREPOINT_DIR / "dim_estacion.csv"
    if not ruta.exists():
        return None
    df = pd.read_csv(ruta, sep=",", encoding="latin1")
    df = df.drop_duplicates(subset=["estacion_ruta"])
    df["gps_latitud"] = df["gps_latitud"].map(_coord)
    df["gps_longitud"] = df["gps_longitud"].map(_coord)
    return df


def cargar_calendario():
    ruta = config.DIM_CALENDARIO_XLSX
    if not ruta.exists():
        ruta = config.SHAREPOINT_DIR / "dim_Calendario.xlsx"
    if not ruta.exists():
        return None
    df = pd.read_excel(ruta, usecols=["Fecha", "Dia.tipo", "Dia.nombre"])
    df["fecha"] = pd.to_datetime(df["Fecha"]).dt.normalize()
    df = df[["fecha", "Dia.tipo", "Dia.nombre"]].drop_duplicates(subset=["fecha"])
    return df
