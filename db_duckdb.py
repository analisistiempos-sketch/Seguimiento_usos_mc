import glob
from pathlib import Path

import duckdb
import pandas as pd

import config

COLUMNAS = ["id_estacion", "Nombre_estacion", "fecha", "hora", "Uso_pago", "Integracion"]


def _sincronizar():
    if config.FUENTE == "github":
        import github_data

        github_data.sync_desde_github(config.DATOS_ACTUAL_DIR)


def rutas_parquet(incluir_historico=True):
    _sincronizar()
    rutas = []
    for src in [config.DATOS_ACTUAL_DIR] + [config.SHAREPOINT_DIR / a for a in config.ANIOS_DIARIOS]:
        if src.exists():
            rutas += glob.glob(str(src / "*.parquet"))
    if incluir_historico:
        for anio in config.ANIOS_TRIMESTRALES:
            carpeta = config.SHAREPOINT_DIR / str(anio)
            if carpeta.exists():
                rutas += glob.glob(str(carpeta / "*.parquet"))
    return rutas


def _paths_sql(rutas):
    return ", ".join("'" + p.replace("'", "''") + "'" for p in rutas)


def _crear_vista(con, incluir_historico):
    rutas = rutas_parquet(incluir_historico)
    if not rutas:
        return None
    sql = "CREATE OR REPLACE VIEW vw_usos AS SELECT * FROM read_parquet([{}], union_by_name=true)".format(
        _paths_sql(rutas)
    )
    con.execute(sql)
    return rutas


def listar_dias():
    con = duckdb.connect()
    try:
        if _crear_vista(con, incluir_historico=False) is None:
            return []
        return [
            pd.to_datetime(r[0]).date()
            for r in con.execute("SELECT DISTINCT CAST(fecha AS DATE) FROM vw_usos ORDER BY 1").fetchall()
        ]
    finally:
        con.close()


def cargar_rango(fecha_min, fecha_max, incluir_historico=True):
    con = duckdb.connect()
    try:
        if _crear_vista(con, incluir_historico) is None:
            return pd.DataFrame(columns=COLUMNAS)
        inicio = pd.Timestamp(fecha_min).normalize().strftime("%Y-%m-%d")
        fin = (pd.Timestamp(fecha_max).normalize() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        df = con.execute(
            "SELECT * FROM vw_usos WHERE fecha >= ? AND fecha < ?",
            [inicio, fin],
        ).df()
        return df
    finally:
        con.close()


def construir_db(ruta_db=None, incluir_historico=True):
    ruta_db = Path(ruta_db or config.DB_DUCKDB)
    ruta_db.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(ruta_db))
    try:
        if _crear_vista(con, incluir_historico) is None:
            raise RuntimeError("No hay parquet para construir la base.")
        con.execute("CREATE OR REPLACE TABLE usos AS SELECT * FROM vw_usos")
        con.execute("DROP VIEW IF EXISTS vw_usos")
        total = con.execute("SELECT COUNT(*) FROM usos").fetchone()[0]
        rango = con.execute("SELECT MIN(fecha), MAX(fecha) FROM usos").fetchone()
        estaciones = con.execute("SELECT COUNT(DISTINCT Nombre_estacion) FROM usos").fetchone()[0]
        return {
            "archivo": str(ruta_db),
            "filas": total,
            "estaciones": estaciones,
            "min": str(rango[0]),
            "max": str(rango[1]),
        }
    finally:
        con.close()
