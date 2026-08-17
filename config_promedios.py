# ============================================================
# PUENTE: la config única vive en APP_USOS\Seguimiento_usos
# Este archivo solo la carga. EDITA SIEMPRE LA DE APP_USOS.
# ============================================================
import importlib.util
import sys

_ruta = r"C:\Users\maortiz\OneDrive - metrocali.gov.co\APP_USOS\Seguimiento_usos\config_promedios.py"
_spec = importlib.util.spec_from_file_location("config_promedios", _ruta)
_modulo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_modulo)
sys.modules["config_promedios"] = _modulo
