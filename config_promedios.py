# ============================================================
# CONFIGURACIÓN DEL PANEL DE PROMEDIOS
# (pestaña Resumen y Seguimiento semanal)
# Todo el panel se configura desde este archivo: títulos y líneas.
# ============================================================

# --- Títulos de los paneles ---
TITULO_LINEAS_RESUMEN = "Usos por Hora"
TITULO_BARRAS = "Usos Últimos {n} días"   # {n} se reemplaza por ULTIMOS_DIAS_BARRAS

# --- Días del gráfico de barras del Resumen ---
ULTIMOS_DIAS_BARRAS = 21

# --- True si quieres incluir el histórico 2019-2025 en los gráficos ---
# (en la nube solo funcionará si el histórico está en el repo datos/)
INCLUIR_HISTORICO = False

# --- Corredores que NO quieres que aparezcan (se excluyen de filtros y gráficos) ---
CORREDORES_EXCLUIDOS = ["Aerosuspendido", "Sin Identificar"]

# ============================================================
# LÍNEAS DE LA GRÁFICA (días y/o promedios)
# ============================================================
# Cada línea:
#   mostrar -> True (se dibuja) o False (se oculta)
#   color   -> color de la línea (hex o nombre en inglés)
#   estilo  -> "solid" (continuo) | "dash" (guiones) | "dot" (puntos)
#   nombre  -> texto que sale en la leyenda (opcional)
# Y según el tipo:
#   DÍA:       {"fecha": "AAAA-MM-DD", ...}
#   PROMEDIO:  {"desde": "AAAA-MM-DD", "hasta": "AAAA-MM-DD", ...}
LINEAS = [
    # --- Promedios (agrega cuantos quieras; cada uno con su mostrar) ---
    {"mostrar": False,  "desde": "2026-08-03", "hasta": "2026-08-06", "color": "#FF7F0E", "estilo": "dash",  "nombre": "Promedio 03-06 ago"},
    {"mostrar": False, "desde": "2026-08-10", "hasta": "2026-08-14", "color": "#17BECF", "estilo": "dash",  "nombre": "Promedio 10-14 ago"},
    # --- Días a evaluar ---
    {"mostrar": False,  "fecha": "2026-08-10", "color": "#1F77B4", "estilo": "solid", "nombre": "Lunes 10"},
    {"mostrar": True,  "fecha": "2026-08-14", "color": "#2CA02C", "estilo": "dash", "nombre": "Viernes 14"},
    {"mostrar": True,  "fecha": "2026-08-08", "color": "#D62728", "estilo": "dash", "nombre": "Sábado 08"},
    {"mostrar": True,  "fecha": "2026-08-15", "color": "#9467BD", "estilo": "solid",  "nombre": "Sábado 15"},
]

# ============================================================
# GUÍA DE COLORES
# ============================================================
# Puedes usar nombres en inglés o códigos hex.
#
# AZULES      #1F77B4 azul, #17BECF cian, #7EC8E3 azul claro
# VERDES      #2CA02C verde, #98DF8A verde claro
# ROJOS       #D62728 rojo, #E377C2 rosa, #FF9896 rojo claro
# NARANJAS    #FF7F0E naranja, #FFBB78 durazno, #C44E52 granate
# MORADOS     #9467BD morado, #8C564B café, #C5B0D5 lila
# GRISES      #7F7F7F gris, #000000 negro, #636EFA índigo
# AMARILLOS   #FFD700 dorado, #F2C80F amarillo
#
# ESTILOS: "solid" (continuo) | "dash" (guiones) | "dot" (puntos)
