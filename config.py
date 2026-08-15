import os
from pathlib import Path


def _env(key, default):
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.environ.get(key, default)


# Ruta base donde viven los .parquet (carpeta sincronizada de SharePoint o disco local en la nube)
SHAREPOINT_DIR = Path(_env(
    "USOS_SHAREPOINT_DIR",
    r"C:\Users\maortiz\OneDrive - metrocali.gov.co\Reportes power Bi Oficina de Evaluación - Documentos\Datos_usos",
))

# Datos diarios recientes
DATOS_ACTUAL_DIR = SHAREPOINT_DIR / "Actual"

# Anios con parquet trimestrales historicos
ANIOS_TRIMESTRALES = list(range(2019, 2026))

# Anios con parquet diarios por mes
ANIOS_DIARIOS = ["2026"]

# Dimension de estaciones (opcional; habilita mapa, zona y tipo de servicio)
DIM_ESTACION_CSV = Path(_env("USOS_DIM_ESTACION", "dim_estacion.csv"))
if not DIM_ESTACION_CSV.exists():
    DIM_ESTACION_CSV = Path(r"C:\Users\maortiz\OneDrive - metrocali.gov.co\Scripts\Informe_Presidencia\usosdiarios\dim_estacion.csv")

# Correcciones de nombres de estaciones (necesarias para la descarga)
CORRECCIONES_JSON = Path(_env("USOS_CORRECCIONES", "correcciones_estaciones.json"))
if not CORRECCIONES_JSON.exists():
    CORRECCIONES_JSON = Path(r"C:\Users\maortiz\OneDrive - metrocali.gov.co\Scripts\Informe_Presidencia\usosdiarios\correcciones_estaciones.json")

# Calendario de días (habíl/sábado/domingo/festivo)
DIM_CALENDARIO_XLSX = Path(_env("USOS_DIM_CALENDARIO", "dim_Calendario.xlsx"))
if not DIM_CALENDARIO_XLSX.exists():
    DIM_CALENDARIO_XLSX = Path(r"C:\Users\maortiz\OneDrive - metrocali.gov.co\Reportes power Bi Oficina de Evaluación - Documentos\Datos_dimensiones\dim_Calendario.xlsx")

# --- SharePoint (Microsoft Graph API) ---
SP_SITE_HOST = _env("USOS_SP_HOST", "metrocaligovco.sharepoint.com")
SP_SITE_PATH = _env("USOS_SP_SITE", "/sites/ReportespowerBiOficinadeEvaluacin")
SP_CARPETA = _env("USOS_SP_CARPETA", "Datos_usos/Actual")

# --- Credenciales de la descarga (APEX UTRYT) ---
URL_LOGIN = _env(
    "USOS_URL_LOGIN",
    "https://apex.utryt.com.co:10443/apex/r/desarrollo/informes-metrocali/login",
)
USUARIO_LOGIN = _env("USOS_LOGIN", "")
PASSWORD_LOGIN = _env("USOS_PASSWORD", "")

# --- Fuente de datos: "local" (carpeta sincronizada de SharePoint) o "github" (puente de datos) ---
FUENTE = _env("USOS_FUENTE", "local")

# --- Motor de lectura: "duckdb" (recomendado, lee todos los parquet) o "pandas" ---
USOS_MOTOR = _env("USOS_MOTOR", "duckdb")

# --- Ruta del archivo de base DuckDB (para construir_db.py) ---
DB_DUCKDB = Path(_env("USOS_DB_PATH", str(SHAREPOINT_DIR / "usos.duckdb")))

# --- GitHub (puente de datos, vía B) ---
GITHUB_REPO = _env("GITHUB_REPO", "")
GITHUB_RUTA = _env("GITHUB_RUTA", "datos")
GITHUB_BRANCH = _env("GITHUB_BRANCH", "main")
GITHUB_TOKEN = _env("GITHUB_TOKEN", "")

# --- WhatsApp (envío del resumen) ---
# Número destino en formato internacional sin símbolos (ej: 573001234567)
WHATSAPP_NUMERO = _env("USOS_WHATSAPP_NUMERO", "")

# --- Correo (envío del resumen) ---
SMTP_HOST = _env("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = _env("SMTP_PORT", "587")
SMTP_USER = _env("SMTP_USER", "")
SMTP_PASSWORD = _env("SMTP_PASSWORD", "")
CORREO_ORIGEN = _env("CORREO_ORIGEN", "")
CORREO_DESTINO = _env("CORREO_DESTINO", "miguel.ortiz01@gmail.com")
