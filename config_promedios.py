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

# --- Zonas que NO quieres que aparezcan (se excluyen de filtros y gráficos) ---
ZONAS_EXCLUIDAS = ["Prueba"]

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

COLORES = {
    # AZULES
    "azul_marino": "#000080",
    "azul_oscuro": "#00008B",
    "azul_medio": "#0000CD",
    "azul_puro": "#0000FF",
    "azul_medianoche": "#191970",
    "azul_petroleo": "#003F5C",
    "azul_corporativo": "#1F4E78",
    "azul": "#1F77B4",
    "azul_office": "#0070C0",
    "azul_tecnologico": "#007ACC",
    "azul_rey": "#4169E1",
    "azul_acero": "#4682B4",
    "azul_claro": "#7EC8E3",
    "azul_cielo": "#87CEEB",
    "azul_cielo_claro": "#87CEFA",
    "azul_pastel": "#AEC6CF",

    # TURQUESAS / CIAN
    "cian": "#17BECF",
    "cian_puro": "#00FFFF",
    "turquesa": "#40E0D0",
    "turquesa_oscuro": "#00CED1",
    "turquesa_medio": "#48D1CC",
    "aguamarina": "#66CDAA",
    "teal": "#008080",

    # VERDES
    "verde_oscuro": "#006400",
    "verde": "#2CA02C",
    "verde_bosque": "#228B22",
    "verde_esmeralda": "#50C878",
    "verde_lima": "#32CD32",
    "verde_oliva": "#6B8E23",
    "verde_claro": "#90EE90",
    "verde_pastel": "#98DF8A",
    "verde_menta": "#98FF98",

    # ROJOS
    "rojo_oscuro": "#8B0000",
    "rojo": "#D62728",
    "rojo_ladrillo": "#B22222",
    "carmesi": "#DC143C",
    "rojo_material": "#E53935",
    "rojo_puro": "#FF0000",
    "rojo_claro": "#FF9896",
    "coral": "#FF7F50",
    "salmon": "#FA8072",

    # NARANJAS
    "naranja": "#FF7F0E",
    "naranja_oscuro": "#FF8C00",
    "naranja_intenso": "#FF6600",
    "naranja_pastel": "#FFB347",
    "durazno": "#FFBB78",

    # AMARILLOS
    "amarillo": "#F2C80F",
    "amarillo_puro": "#FFFF00",
    "amarillo_oro": "#FFD000",
    "oro": "#FFD700",
    "mostaza": "#FFDB58",
    "caqui": "#F0E68C",

    # MORADOS
    "morado_oscuro": "#4B0082",
    "morado": "#9467BD",
    "morado_office": "#7030A0",
    "purpura": "#800080",
    "violeta": "#8A2BE2",
    "amatista": "#8E44AD",
    "lila": "#C5B0D5",
    "lavanda": "#E6E6FA",

    # ROSAS
    "rosa": "#E377C2",
    "rosa_fuerte": "#FF69B4",
    "rosa_claro": "#FF80AB",
    "rosa_pastel": "#FFB6C1",
    "fucsia": "#FF00FF",

    # CAFÉS
    "cafe": "#8C564B",
    "cafe_oscuro": "#654321",
    "marron": "#795548",
    "siena": "#A0522D",
    "beige": "#D2B48C",

    # GRISES
    "negro": "#000000",
    "carbon": "#36454F",
    "gris_oscuro": "#404040",
    "gris": "#7F7F7F",
    "gris_pizarra": "#708090",
    "gris_claro": "#B0B0B0",
    "plata": "#C0C0C0",
    "gris_muy_claro": "#E0E0E0",
    "blanco": "#FFFFFF",
}




LINEAS = [
    # --- Promedios (agrega cuantos quieras; cada uno con su mostrar) ---
    {"mostrar": False,  "desde": "2026-08-03", "hasta": "2026-08-06", "color": "#FF7F0E", "estilo": "dash",  "nombre": "Promedio 03-06 ago"},
    {"mostrar": False, "desde": "2026-08-10", "hasta": "2026-08-14", "color": "#17BECF", "estilo": "dash",  "nombre": "Promedio 10-14 ago"},
    # --- Días a evaluar ---


    {"mostrar": True,  "fecha": "2026-08-09", "color": COLORES["azul_cielo_claro"], "estilo": "solid", "nombre": "Domingo 09"},
    {"mostrar": True,  "fecha": "2026-08-14", "color": COLORES["azul_corporativo"], "estilo": "dash", "nombre": "Viernes 14"},
    {"mostrar": True,  "fecha": "2026-08-16", "color": COLORES["violeta"], "estilo": "dash", "nombre": "Domingo 16"},
    {"mostrar": True,  "fecha": "2026-08-17", "color": COLORES["morado_oscuro"], "estilo": "solid",  "nombre": "Lunes 17"},
]

# ============================================================
# GUÍA DE COLORES COMPLETA
# ============================================================
# Puedes usar nombres en inglés o códigos HEX.
#
# Ejemplo:
# color = "#1F77B4"
# color = "royalblue"
#
# ============================================================

# ESTILOS: "solid" (continuo) | "dash" (guiones) | "dot" (puntos)

