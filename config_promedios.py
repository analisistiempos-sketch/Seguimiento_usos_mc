# Configuración del panel (actualizada desde la app)
COLORES = {
    'azul_marino': '#000080',
    'azul_oscuro': '#00008B',
    'azul_medio': '#0000CD',
    'azul_puro': '#0000FF',
    'azul_medianoche': '#191970',
    'azul_petroleo': '#003F5C',
    'azul_corporativo': '#1F4E78',
    'azul': '#1F77B4',
    'azul_office': '#0070C0',
    'azul_tecnologico': '#007ACC',
    'azul_rey': '#4169E1',
    'azul_acero': '#4682B4',
    'azul_claro': '#7EC8E3',
    'azul_cielo': '#87CEEB',
    'azul_cielo_claro': '#87CEFA',
    'azul_pastel': '#AEC6CF',
    'cian': '#17BECF',
    'cian_puro': '#00FFFF',
    'turquesa': '#40E0D0',
    'turquesa_oscuro': '#00CED1',
    'turquesa_medio': '#48D1CC',
    'aguamarina': '#66CDAA',
    'teal': '#008080',
    'verde_oscuro': '#006400',
    'verde': '#2CA02C',
    'verde_bosque': '#228B22',
    'verde_esmeralda': '#50C878',
    'verde_lima': '#32CD32',
    'verde_oliva': '#6B8E23',
    'verde_claro': '#90EE90',
    'verde_pastel': '#98DF8A',
    'verde_menta': '#98FF98',
    'rojo_oscuro': '#8B0000',
    'rojo': '#D62728',
    'rojo_ladrillo': '#B22222',
    'carmesi': '#DC143C',
    'rojo_material': '#E53935',
    'rojo_puro': '#FF0000',
    'rojo_claro': '#FF9896',
    'coral': '#FF7F50',
    'salmon': '#FA8072',
    'naranja': '#FF7F0E',
    'naranja_oscuro': '#FF8C00',
    'naranja_intenso': '#FF6600',
    'naranja_pastel': '#FFB347',
    'durazno': '#FFBB78',
    'amarillo': '#F2C80F',
    'amarillo_puro': '#FFFF00',
    'amarillo_oro': '#FFD000',
    'oro': '#FFD700',
    'mostaza': '#FFDB58',
    'caqui': '#F0E68C',
    'morado_oscuro': '#4B0082',
    'morado': '#9467BD',
    'morado_office': '#7030A0',
    'purpura': '#800080',
    'violeta': '#8A2BE2',
    'amatista': '#8E44AD',
    'lila': '#C5B0D5',
    'lavanda': '#E6E6FA',
    'rosa': '#E377C2',
    'rosa_fuerte': '#FF69B4',
    'rosa_claro': '#FF80AB',
    'rosa_pastel': '#FFB6C1',
    'fucsia': '#FF00FF',
    'cafe': '#8C564B',
    'cafe_oscuro': '#654321',
    'marron': '#795548',
    'siena': '#A0522D',
    'beige': '#D2B48C',
    'negro': '#000000',
    'carbon': '#36454F',
    'gris_oscuro': '#404040',
    'gris': '#7F7F7F',
    'gris_pizarra': '#708090',
    'gris_claro': '#B0B0B0',
    'plata': '#C0C0C0',
    'gris_muy_claro': '#E0E0E0',
    'blanco': '#FFFFFF'
}


TITULO_LINEAS_RESUMEN = 'Usos por Hora'
TITULO_BARRAS = 'Usos Últimos {n} días'
ULTIMOS_DIAS_BARRAS = 21
INCLUIR_HISTORICO = False
# HORA_CORTE_HOY: última hora (incluida) que se muestra para el día de HOY en la línea.
# Ej. 8 = mostrar hasta las 8:59 · 9 = hasta las 9:59 · None = mostrar todo (hasta la hora con datos).
HORA_CORTE_HOY = None
CORREDORES_EXCLUIDOS = ['Aerosuspendido', 'Sin Identificar']
ZONAS_EXCLUIDAS = ['Prueba']

SEMANAS_TERREMOTO = {'3 - 9 ago': {'desde': '2026-08-03', 'hasta': '2026-08-09', 'color': '#2CA02C'}, '10 - 16 ago': {'desde': '2026-08-10', 'hasta': '2026-08-16', 'color': '#D62728'}, '17 - 23 ago': {'desde': '2026-08-17', 'hasta': '2026-08-23', 'color': '#FF7F0E'}, '24 - 30 ago': {'desde': '2026-08-24', 'hasta': '2026-08-30', 'color': '#FFB347'}}
SEMANA_BASE = '3 - 9 ago'


# Habil

LINEAS = [
    {'mostrar': True, 'desde': '2026-08-03', 'hasta': '2026-08-06', 'color': '#404040', 'estilo': 'solid', 'nombre': 'Promedio 03-06 ago'},
    {'mostrar': True, 'desde': '2026-08-10', 'hasta': '2026-08-14', 'color': '#919191', 'estilo': 'dash', 'nombre': 'Promedio 10-14 ago'},
    {'mostrar': True, 'desde': '2026-08-18', 'hasta': '2026-08-21', 'color': '#2f35b5', 'estilo': 'dash', 'nombre': 'Promedio 18-21 ago'}, 
    
    
    {'mostrar': True, 'fecha': '2026-08-26', 'color': '#FF80AB', 'estilo': 'dash', 'nombre': '26_agosto'},
    {'mostrar': True, 'fecha': '2026-08-27', 'color': '#FF80AB', 'estilo': 'dash', 'nombre': '27_agosto'},
    {'mostrar': True, 'fecha': '2026-08-28', 'color': '#4B0082', 'estilo': 'solid', 'nombre': '28_agosto'},    
    ]

'''
# Sabado
LINEAS = [
    {'mostrar': False , 'desde': '2026-08-03', 'hasta': '2026-08-06', 'color': '#404040', 'estilo': 'solid', 'nombre': 'Promedio 03-06 ago'},
    {'mostrar': False, 'desde': '2026-08-10', 'hasta': '2026-08-16', 'color': '#919191', 'estilo': 'dash', 'nombre': 'Promedio 10-16 ago'},
    {'mostrar': False, 'desde': '2026-08-17', 'hasta': '2026-08-23', 'color': '#2f35b5', 'estilo': 'dot', 'nombre': 'Promedio 17-23 ago'}, 
    {'mostrar': False, 'fecha': '2026-08-19', 'color': '#b95bd8', 'estilo': 'dash', 'nombre': '19_agosto'},
    {'mostrar': False, 'fecha': '2026-08-20', 'color': '#dc3579', 'estilo': 'dash', 'nombre': '20_agosto'}, 
    {'mostrar': False, 'fecha': '2026-08-21', 'color': '#7d38c3', 'estilo': 'solid', 'nombre': '21_agosto'},

    {'mostrar': True, 'fecha': '2026-08-01', 'color': '#000000', 'estilo': 'solid', 'nombre': '01_agosto'},
    {'mostrar': True, 'fecha': '2026-08-08', 'color': '#E377C2', 'estilo': 'dash', 'nombre': '08_agosto'},
    {'mostrar': True, 'fecha': '2026-08-15', 'color': '#FFB6C1', 'estilo': 'dash', 'nombre': '15_agosto'},
    {'mostrar': True, 'fecha': '2026-08-22', 'color': '#9467BD', 'estilo': 'solid', 'nombre': '22_agosto'}
    
    ] 

# Domingo
LINEAS = [
    {'mostrar': False , 'desde': '2026-08-03', 'hasta': '2026-08-06', 'color': '#404040', 'estilo': 'solid', 'nombre': 'Promedio 03-06 ago'},
    {'mostrar': False, 'desde': '2026-08-10', 'hasta': '2026-08-16', 'color': '#919191', 'estilo': 'dash', 'nombre': 'Promedio 10-16 ago'},
    {'mostrar': False, 'desde': '2026-08-17', 'hasta': '2026-08-23', 'color': '#2f35b5', 'estilo': 'dot', 'nombre': 'Promedio 17-23 ago'}, 
    {'mostrar': False, 'fecha': '2026-08-19', 'color': '#b95bd8', 'estilo': 'dash', 'nombre': '19_agosto'},
    {'mostrar': False, 'fecha': '2026-08-20', 'color': '#dc3579', 'estilo': 'dash', 'nombre': '20_agosto'}, 
    {'mostrar': False, 'fecha': '2026-08-21', 'color': '#7d38c3', 'estilo': 'solid', 'nombre': '21_agosto'},

    {'mostrar': True, 'fecha': '2026-08-02', 'color': '#000000', 'estilo': 'solid', 'nombre': '02_agosto'},
    {'mostrar': True, 'fecha': '2026-08-09', 'color': '#E377C2', 'estilo': 'dash', 'nombre': '09_agosto'},
    {'mostrar': True, 'fecha': '2026-08-16', 'color': '#FFB6C1', 'estilo': 'dash', 'nombre': '16_agosto'},
    {'mostrar': True, 'fecha': '2026-08-23', 'color': '#9467BD', 'estilo': 'solid', 'nombre': '23_agosto'}
    
]
'''