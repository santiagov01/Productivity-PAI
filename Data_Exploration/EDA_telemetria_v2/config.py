# =============================================================================
# CONFIGURACION DEL EDA DE TELEMETRIA (proyecto PAI-New)
# Todas las variables que se ajustan a mano están aquí. Los notebooks las importan con:
#     from config import *
# Después de editar este archivo, reinicia el kernel del notebook para que tome los cambios.
# =============================================================================
from dataclasses import dataclass
from pathlib import Path


# =============================================================================
# 1. RUTAS
# =============================================================================
DIR_BASE = Path(__file__).resolve().parent          # carpeta donde están config.py y los notebooks
# Carpeta donde están los datos
DIR_DATOS = Path(R"D:\Estudio\OneDrive - Universidad de Antioquia\Estudio\PAI\Nuevos-Modelos-Paulina\Datos")

DIR_SALIDA = DIR_BASE / "outputs" / "EDA_telemetria_fija"
TIPO_TELEMETRIA = "fija"
RANGO_ARCHIVOS = "2024-01-01_to_2026-10-19"  # NOTE: Nombre de datos aparece con este sufijo.
COL_TIEMPO = "timestamp"  # Nombre de columna de tiempo
COLUMNAS_METADATOS = ["departamento", "municipio", "tipo", "nombre"]


# =============================================================================
# 2. FINCAS: ciclo del cultivo y etapas
# =============================================================================
@dataclass(frozen=True)
class Finca:
    nombre: str
    fecha_inicio: str            # inicio del ciclo del cultivo en ESTA finca (paso 1)
    fecha_fin: str               # fin del ciclo del cultivo en ESTA finca
    rangos: dict | None = None   # {"Etapa": (inicio, fin)} propios de la finca (pasos 6 y 9)
                                 # None -> el ciclo se divide en N_RANGOS_AUTO tramos iguales


# --- Fincas a analizar: cada una con su ciclo y sus etapas ---
# Fechas sin hora en `fecha_fin` o en el fin de un rango incluyen todo ese día.
# Ciclos confirmados del cultivo. `rangos=None` divide cada ciclo en N_RANGOS_AUTO tramos iguales
FINCAS = [
    Finca(
        nombre="La_Orquidea", # TODO: Agregar info de todo el año. Empezaron desde octubre.
        fecha_inicio="2025-11-24",
        fecha_fin="2026-05-21",
        rangos={
            "Descanso": ("2025-10-21", "2025-11-23"),
            "Pre-siembra": ("2025-11-24", "2025-12-8"),
            "Vegetativa": ("2025-12-09", "2026-01-11"),
            "Floración":  ("2026-01-12", "2026-03-9"),
            "Cosecha":    ("2026-03-10", "2026-05-21"),
            "Descanso2": ("2026-05-22", "2026-10-19")
        },
    ),
    Finca(
        nombre="Venecia",
        fecha_inicio="2026-05-5",
        fecha_fin="2026-10-19",
        rangos={
            "Descanso": ("2025-10-21", "2026-05-4"),
            "Pre-siembra": ("2026-05-5", "2026-05-20"),
            "Vegetativa": ("2026-05-21", "2026-06-20"),
            "Floración":  ("2026-06-21", "2026-08-26"),
            "Cosecha":    ("2026-08-27", "2026-10-19"),
            # "Descanso2": ("2026-10-20", "AAAA-MM-DD"),   # activar cuando haya datos después del 19/10/2026
        },
    ),
    Finca(
        nombre="Puerto_Arturo",
        fecha_inicio="2026-02-06",
        fecha_fin="2026-09-01",
        rangos={
            "Descanso": ("2025-10-21", "2026-02-5"),
            "Pre-siembra": ("2026-02-06", "2026-02-09"),
            "Vegetativa": ("2026-02-10", "2026-03-21"),
            "Floración":  ("2026-03-22", "2026-06-14"),
            "Cosecha":    ("2026-06-15", "2026-09-01"),
            "Descanso2": ("2026-09-02", "2026-10-19")
        },
    )
]
# fecha_inicio / fecha_fin = ciclo del cultivo ("Ciclo completo" en los análisis).
# Se cargan los datos de TODO el periodo que cubren las etapas (incluye Descanso y Descanso2).
# Si las etapas usan los mismos nombres en todas las fincas, el paso 6 las compara entre fincas.
FINCAS_POR_NOMBRE = {f.nombre: f for f in FINCAS}
FINCAS_COMPARAR = ("La_Orquidea", "Venecia")   # paso 7
N_RANGOS_AUTO = 3                              # solo se usa si una finca tiene rangos=None

# Archivo de telemetría fija de cada finca
RUTAS_TELEMETRIA_FIJA = {finca.nombre: DIR_DATOS / finca.nombre /
                         f"telemetria_{TIPO_TELEMETRIA}_{finca.nombre}_{RANGO_ARCHIVOS}.xlsx"
                         for finca in FINCAS}


# =============================================================================
# 3. TIPOS DE VARIABLES DE LA TELEMETRIA FIJA
# =============================================================================
TIPO_VARS_BD_FIJA = {
    "soil_60cm" : ['bottom_nitrogen_60cm', 'bottom_phosphorus_60cm', 'bottom_potassium_60cm', 'bottom_ph_60cm',
                    'bottom_moisture_60cm', 'bottom_temperature_60cm', 'bottom_conductivity_60cm'],
    "soil_40cm" : ['medium_nitrogen_40cm', 'medium_phosphorus_40cm', 'medium_potassium_40cm', 'medium_ph_40cm',
                    'medium_moisture_40cm', 'medium_temperature_40cm', 'medium_conductivity_40cm'],
    "soil_20cm" : ['top_nitrogen_20cm', 'top_phosphorus_20cm', 'top_potassium_20cm', 'top_ph_20cm',
                    'top_moisture_20cm', 'top_temperature_20cm', 'top_conductivity_20cm'],
    "ambient" : ['radiation', 'air_temperature', 'air_humidity'],
    "pred_60cm" : ['conductivity_est_extratrees_60cm', 'conductivity_est_randomforest_60cm','conductivity_est_lightgbm_60cm'],
    "pred_40cm" : ['medium_moisture41_pred', 'medium_ecpw41_pred', 'conductivity_est_extratrees_40cm',
                    'conductivity_est_randomforest_40cm','conductivity_est_lightgbm_40cm'],
    "pred_20cm" : ['top_moisture20_pred', 'top_ecpw20_pred', 'conductivity_est_extratrees_20cm',
                   'conductivity_est_randomforest_20cm','conductivity_est_lightgbm_20cm',
                   'top_conductivity_20cm']
}

var_nosel = ["lat", "lon",
"conductivity_est_20",
"conductivity_est_40",
"conductivity_est_60",
"cultivo_reentrenamiento",
"finca_cropx", "cropx_sheet"]

Mod2_tom = ['medium_conductivity_40cm', 'medium_temperature_40cm', 'medium_moisture_40cm']


# =============================================================================
# 4. CALIDAD DE DATOS Y ALARMAS (notebook 06)
# =============================================================================
valid_ranges = {
    "conductivity": (0, 5), "temperature": (10, 25), "pH": (3, 9),
    "radiation": (0, 1000), "moisture": (0, 100), "airTemperature": (10, 50),
    "airHumidity": (20, 100)
}

variables_mapping = {
    "top_conductivity_20cm": "conductivity",
    "medium_conductivity_40cm": "conductivity",
    "bottom_conductivity_60cm": "conductivity",
    "top_ph_20cm": "pH", "medium_ph_40cm": "pH", "bottom_ph_60cm": "pH",
    "top_temperature_20cm": "temperature", "medium_temperature_40cm": "temperature", "bottom_temperature_60cm": "temperature",
    "top_moisture_20cm": "moisture", "medium_moisture_40cm": "moisture", "bottom_moisture_60cm": "moisture",
    "air_temperature": "airTemperature",
    "air_humidity": "airHumidity",
    "radiation": "radiation",
    "ECpw 20": "conductivity",
    "ECpw 41": "conductivity",
    "ECpw 66": "conductivity",
    "Moisture 20": "moisture",
    "Moisture 41": "moisture",
    "Moisture 66": "moisture",
    "Temperature 20": "temperature",
    "Temperature 41": "temperature"
}

max_change = {
    "conductivity": 0.8,
    "temperature": 1,
    "pH": 0.5,
    "radiation": 200,
    "moisture": 10,
    "airTemperature": 6,
    "airHumidity": 25
}

FLAGS = {
    0: "Normal",
    1: "Anomalía física",
    2: "Anomalía histórica",
    3: "Spike aislado",
    4: "Cambio brusco",
    5: "Outlier MAD",
    6: "Anomalía multivariable",
    7: "Valor interpolado"
}
DIR_ALARMAS = DIR_SALIDA / "alarmas"           # Excel {finca}_{base}_alarmas.xlsx
COLORES_FLAGS = {1: "#D55E00", 2: "#066806", 3: "#CC0773",
                 4: "#0331CA", 5: "#00EEFF", 6: "#000000"}


# =============================================================================
# 5. BASE DE DATOS CROPX (notebook 07)
# =============================================================================
# --- AJUSTAR rutas y nombre de la columna de tiempo ---
RUTAS_CROPX = {
    "La_Orquidea": DIR_DATOS / "La_Orquidea" / "CropXLaOrquidea.xlsx",
    "Venecia": DIR_DATOS / "Venecia" / "CropXVenecia.xlsx",
    "Puerto_Arturo": DIR_DATOS / "Puerto_Arturo" / "CropXPuertoArturo.xlsx",
}
COL_TIEMPO_CROPX = "Date"

GRUPOS_CROPX = {
    "Humedad (%)": ["Moisture 20", "Moisture 41", "Moisture 66"],
    "Temperatura (C)": ["Temperature 20", "Temperature 41"],
    "Conductividad ECpw (dS/m)": ["ECpw 20", "ECpw 41", "ECpw 66"],
}
VARIABLES_CROPX = [v for grupo in GRUPOS_CROPX.values() for v in grupo]

# Grupos de la comparativa en el tiempo telemetría fija + CropX
GRUPOS_COMPARATIVA = {
    "Humedad (%)": {
        "fija": ["top_moisture_20cm", "medium_moisture_40cm", "bottom_moisture_60cm", "air_humidity"],
        "cropx": ["Moisture 20", "Moisture 41", "Moisture 66"]},
    "Temperatura (C)": {
        "fija": ["top_temperature_20cm", "medium_temperature_40cm", "bottom_temperature_60cm", "air_temperature"],
        "cropx": ["Temperature 20", "Temperature 41"]},
    "Conductividad (dS/m)": {
        "fija": ["top_conductivity_20cm", "medium_conductivity_40cm", "bottom_conductivity_60cm"],
        "cropx": ["ECpw 20", "ECpw 41", "ECpw 66"]},
    "pH": {
        "fija": ["top_ph_20cm", "medium_ph_40cm", "bottom_ph_60cm"], "cropx": []},
    "Nitrógeno (mg/kg)": {
        "fija": ["top_nitrogen_20cm", "medium_nitrogen_40cm", "bottom_nitrogen_60cm"], "cropx": []},
    "Fósforo (mg/kg)": {
        "fija": ["top_phosphorus_20cm", "medium_phosphorus_40cm", "bottom_phosphorus_60cm"], "cropx": []},
    "Potasio (mg/kg)": {
        "fija": ["top_potassium_20cm", "medium_potassium_40cm", "bottom_potassium_60cm"], "cropx": []},
    "Radiación (W/m2)": {
        "fija": ["radiation"], "cropx": []},
}


# =============================================================================
# 6. BASES DE DATOS ANALIZADAS (nombre usado en títulos y archivos de salida)
# =============================================================================
NOMBRE_BD_FIJA = "telemetria_fija"
NOMBRE_BD_CROPX = "cropx"

# Huecos de información (notebook 01): resolución con la que se buscan periodos sin datos
FRECUENCIA_HUECOS = "1h"        # "1h" = por hora, "1D" = por día


# =============================================================================
# 7. OPCIONES DE ANALISIS Y ESTILO DE GRAFICOS
# =============================================================================
# Diferencias entre fincas (notebook 02)
COLS_EXCLUIR_DIF = ["count", "% faltantes"]   # igual que Tomate.ipynb: no se resta el conteo

# Gráficos de varianza (notebook 04)
FRECUENCIAS = {"Día": "D", "Semana": "W"}

# Boxplot semanal estilo publicación (notebook 04)
ESTILO_PUBLICACION = {
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],   # respaldo si no está instalada
    "font.size": 9,
}

# Comparación entre dos fincas, figura en inglés (notebook 05)
# Paleta Okabe-Ito (apta para daltonismo, habitual en revistas Q1)
COLORES_FINCAS = ("#0072B2", "#D55E00")
ESTILOS_BANDAS = ("--", ":", "-.", (0, (5, 1, 1, 1)))
ESTILO_REVISTA = {
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 8, "axes.labelsize": 9, "axes.titlesize": 9,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 7.5,
    "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "svg.fonttype": "none", "pdf.fonttype": 42,              # texto editable en SVG/PDF
}
ETAPAS_EN = {"Ciclo completo": "Full cycle", "Descanso": "Rest period", "Descanso2": "Rest period 2",
             "Pre-siembra": "Pre-planting",
             "Vegetativa": "Vegetative", "Floración": "Flowering", "Cosecha": "Harvest"}
AGRUPACION = {"Día": ("Day", 1), "Semana": ("Week", 7)}       # (nombre en inglés, días)

# Colores por profundidad en las series de tiempo (notebook 07)
COLORES_PROFUNDIDAD = {"20": "tab:blue", "40": "tab:orange", "41": "tab:orange",
                       "60": "tab:green", "66": "tab:green"}
