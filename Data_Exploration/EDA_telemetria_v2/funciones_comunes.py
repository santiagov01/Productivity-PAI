# =============================================================================
# FUNCIONES COMUNES DEL EDA (usadas por varios notebooks)
# Importar en los notebooks con:  from funciones_comunes import ...
# =============================================================================
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import ipywidgets as widgets

from config import (Finca, FINCAS_POR_NOMBRE, N_RANGOS_AUTO, RUTAS_TELEMETRIA_FIJA, COL_TIEMPO,
                    RUTAS_CROPX, COL_TIEMPO_CROPX, VARIABLES_CROPX)


# =============================================================================
# 1. RANGOS DE FECHAS Y ETAPAS
# =============================================================================
def _limites_rango(inicio: str, fin: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Devuelve (inicio, fin_exclusivo). Un `fin` sin hora incluye todo ese día."""
    t_ini = pd.Timestamp(inicio)
    t_fin = pd.Timestamp(fin)
    
    if ":" not in str(fin):                      # "2026-01-11" -> hasta 2026-01-11 23:59:59.999
        t_fin = t_fin.normalize() + pd.Timedelta(days=1)
    return t_ini, t_fin


def obtener_rangos(finca: Finca) -> dict[str, tuple[str, str]]:
    """Rangos definidos en la finca o, si es None, N_RANGOS_AUTO tramos iguales del ciclo."""
    if finca.rangos:
        return finca.rangos
    
    t_ini, t_fin = _limites_rango(finca.fecha_inicio, finca.fecha_fin)
    cortes = pd.date_range(t_ini, t_fin, periods=N_RANGOS_AUTO + 1)

    return {f"Tramo {i + 1}": (str(cortes[i]), str(cortes[i + 1] - pd.Timedelta(seconds=1)))
            for i in range(N_RANGOS_AUTO)}


def periodo_finca(finca: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Periodo que se carga de una finca: desde la primera hasta la última fecha de su ciclo y sus etapas.

    Args:
        finca (str): Nombre de la finca (clave de FINCAS_POR_NOMBRE).

    Returns:
        tuple[pd.Timestamp, pd.Timestamp]: (inicio, fin_exclusivo). Incluye etapas fuera del ciclo (Descanso).
    """
    f = FINCAS_POR_NOMBRE[finca]
    limites = [_limites_rango(f.fecha_inicio, f.fecha_fin)]
    limites += [_limites_rango(inicio, fin) for inicio, fin in obtener_rangos(f).values()]
    return min(l[0] for l in limites), max(l[1] for l in limites)


def filtrar_etapa(df: pd.DataFrame, finca: str, etapa: str | None) -> pd.DataFrame:
    """Recorta la telemetría a una etapa o al ciclo del cultivo.

    Args:
        df (pd.DataFrame): Telemetría de la finca.
        finca (str): Nombre de la finca (clave de FINCAS_POR_NOMBRE).
        etapa (str | None): Nombre de la etapa, o None para el ciclo completo (fecha_inicio a fecha_fin).

    Returns:
        pd.DataFrame: Sub-DataFrame dentro del rango (vacío si no hay datos en esas fechas).
    """
    f = FINCAS_POR_NOMBRE[finca]
    inicio, fin = (f.fecha_inicio, f.fecha_fin) if etapa is None else obtener_rangos(f)[etapa]
    t_ini, t_fin = _limites_rango(inicio, fin)
    return df.loc[(df.index >= t_ini) & (df.index < t_fin)]


def columnas_analisis(df: pd.DataFrame) -> pd.Index:
    """Numéricas, sin lat/lon, no vacías."""
    return (df.select_dtypes(include=np.number)
              .drop(columns=["lat", "lon"], errors="ignore")
              .dropna(axis=1, how="all")
              .columns)


# =============================================================================
# 2. CARGA DE LA TELEMETRIA FIJA
# =============================================================================
def cargar_finca(path_finca,
                 FINCA: Finca,
                 col_tiempo="timestamp") -> pd.DataFrame:
    df = pd.read_excel(path_finca)

    # Convertir la columna de tiempo a tipo datetime y manejar errores
    df[col_tiempo] = pd.to_datetime(df[col_tiempo], errors="coerce")

    counts_before = df[col_tiempo].isna().sum()
    # Eliminar filas con valores NaN en la columna de tiempo, establecerla como índice y ordenar
    df = df.dropna(subset=[col_tiempo]).set_index(col_tiempo).sort_index()

    counts_after = df.index.isna().sum()
    print(f"Se eliminaron {counts_before - counts_after} filas con valores NaN en la columna '{col_tiempo}' y {counts_after} filas con índice NaN.")

    # Eliminar duplicados en el índice, manteniendo la primera ocurrencia
    #df = df[~df.index.duplicated(keep="first")]
    # Registros con la misma fecha y hora: se conserva el primero
    duplicados = df.index.duplicated(keep="first")
    if duplicados.any():
        iguales = df.reset_index().duplicated(keep="first").to_numpy()   # misma fecha y mismos valores
        print(f"{FINCA.nombre}: {duplicados.sum()} registros con fecha repetida "
              f"({iguales.sum()} idénticos, {duplicados.sum() - iguales.sum()} con valores distintos) -> se eliminan")
    df = df[~duplicados]

    # Comparar como fechas (no como texto) e incluir todo el día de `fecha_fin`
    t_ini_ciclo, t_fin_ciclo = _limites_rango(FINCA.fecha_inicio, FINCA.fecha_fin)
    if t_ini_ciclo >= t_fin_ciclo:
        raise ValueError(f"{FINCA.nombre}: fecha_inicio ({FINCA.fecha_inicio}) es posterior a fecha_fin ({FINCA.fecha_fin})")

    # Filtrar el df al periodo que cubren el ciclo y todas las etapas (incluye Descanso)
    inicio, fin = periodo_finca(FINCA.nombre)
    df = df.loc[(df.index >= inicio) & (df.index < fin)].copy()
    df.index.name = "timestamp"
    assert isinstance(df.index, pd.DatetimeIndex), "El índice debe ser DatetimeIndex"
    return df


def cargar_bd_fija() -> dict[str, pd.DataFrame]:
    """Carga la telemetría fija de todas las fincas de config.FINCAS, recortada al periodo de sus etapas.

    Args:
        None

    Returns:
        dict[str, pd.DataFrame]: {finca: telemetría con índice temporal}.
    """
    BD_FIJA_FILTERED = {}
    for finca, path in RUTAS_TELEMETRIA_FIJA.items():
        print(f"\nCargando datos de la finca: {finca}")
        BD_FIJA_FILTERED[finca] = cargar_finca(
            path,
            FINCAS_POR_NOMBRE[finca],
            col_tiempo=COL_TIEMPO
        )
        print(f"Datos cargados para {finca}: {BD_FIJA_FILTERED[finca].shape[0]} filas y {BD_FIJA_FILTERED[finca].shape[1]} columnas.")
    return BD_FIJA_FILTERED

def es_formato_12h(fechas: pd.Series) -> bool:
    """True si las horas solo van de 0 a 12 (reloj de 12 horas sin AM/PM).

    Args:
        fechas (pd.Series): Fechas ya convertidas con pd.to_datetime.

    Returns:
        bool: True si ninguna hora es mayor que 12.
    """
    horas = fechas.dropna().dt.hour
    return len(horas) > 0 and horas.max() <= 12


def corregir_formato_12h(fechas: pd.Series, finca: str, max_por_mitad: int = 24) -> pd.Series:
    """Asigna AM/PM a fechas de 12 horas usando el orden del archivo.

    Dentro de un mismo día, cuando la hora "retrocede" (p. ej. 11:30 -> 12:00) empieza la tarde.
    "12:xx" antes de ese salto es medianoche (00:xx) y después es mediodía (12:xx).

    Args:
        fechas (pd.Series): Fechas en el orden original del archivo (sin ordenar).
        finca (str): Nombre de la finca para los mensajes.
        max_por_mitad (int): Registros máximos esperados en 12 h (24 con datos cada 30 min).

    Returns:
        pd.Series: Fechas en formato de 24 horas, mismo índice y orden que la entrada.
    """
    dia = fechas.dt.normalize()
    descendente = dia.dropna().iloc[0] > dia.dropna().iloc[-1]
    if descendente:                                        # archivo del más reciente al más antiguo
        fechas, dia = fechas.iloc[::-1], dia.iloc[::-1]

    hora = fechas.dt.hour % 12                             # "12:xx" pasa a 0 y se decide AM/PM abajo
    minutos = hora * 60 + fechas.dt.minute
    retrocede = (minutos.diff() < 0) & (dia == dia.shift())
    pm = retrocede.astype(int).groupby(dia).cumsum() > 0   # todo lo que va después del salto es tarde

    corregidas = (dia + pd.to_timedelta(hora + 12 * pm, unit="h")
                  + pd.to_timedelta(fechas.dt.minute, unit="min"))

    # Control: con datos cada 30 min no puede haber más de 24 registros en una mitad del día
    por_mitad = pd.DataFrame({"dia": dia, "pm": pm}).dropna().value_counts()
    dudosos = sorted({d.date() for (d, _), n in por_mitad.items() if n > max_por_mitad})
    print(f"{finca}: fechas en reloj de 12 h sin AM/PM -> {int(pm.sum())} registros pasados a la tarde "
          f"según el orden del archivo.")
    if dudosos:
        print(f"   REVISAR {len(dudosos)} días con más de {max_por_mitad} registros en media jornada "
              f"(AM/PM ambiguo): {dudosos[:10]}")
    return corregidas.iloc[::-1] if descendente else corregidas

def cargar_cropx(path: Path, finca: str, col_tiempo: str = "Date") -> pd.DataFrame:
    """Carga la base CropX de una finca y la recorta al periodo de sus etapas.

    Args:
        path (Path): Ruta del archivo Excel de CropX.
        finca (str): Nombre de la finca (clave de FINCAS_POR_NOMBRE).
        col_tiempo (str): Nombre de la columna de fecha y hora.

    Returns:
        pd.DataFrame: Variables de VARIABLES_CROPX con índice temporal ordenado y sin duplicados.
    """
    df = pd.read_excel(path)
    df[col_tiempo] = pd.to_datetime(df[col_tiempo], errors="coerce")
    if es_formato_12h(df[col_tiempo]):                     # CropX exporta "Nov 1, 2025 1:30" sin AM/PM
        df[col_tiempo] = corregir_formato_12h(df[col_tiempo], finca)
    df = df.dropna(subset=[col_tiempo]).set_index(col_tiempo).sort_index()
    #df = df[~df.index.duplicated(keep="first")]
    # Registros con la misma fecha y hora: se conserva el primero
    duplicados = df.index.duplicated(keep="first")
    if duplicados.any():
        iguales = df.reset_index().duplicated(keep="first").to_numpy()   # misma fecha y mismos valores
        print(f"{finca}: {duplicados.sum()} registros con fecha repetida "
              f"({iguales.sum()} idénticos, {duplicados.sum() - iguales.sum()} con valores distintos) -> se eliminan")
    df = df[~duplicados]

    t_ini, t_fin = periodo_finca(finca)
    df = df.loc[(df.index >= t_ini) & (df.index < t_fin)]

    columnas = [c for c in VARIABLES_CROPX if c in df.columns]
    ausentes = [c for c in VARIABLES_CROPX if c not in df.columns]
    if ausentes:
        print(f"{finca}: columnas que no están en el archivo: {ausentes}")
    return df[columnas].apply(pd.to_numeric, errors="coerce")


def cargar_bd_cropx() -> dict[str, pd.DataFrame]:
    """Carga la base CropX de todas las fincas que tengan archivo en config.RUTAS_CROPX.

    Args:
        None

    Returns:
        dict[str, pd.DataFrame]: {finca: datos CropX con índice temporal}. Las fincas sin archivo no aparecen.
    """
    BD_CROPX = {}
    for finca, path in RUTAS_CROPX.items():
        if not Path(path).exists():
            print(f"{finca}: no se encontró el archivo CropX en {path}")
            continue
        BD_CROPX[finca] = cargar_cropx(path, finca, COL_TIEMPO_CROPX)
        print(f"{finca}: {len(BD_CROPX[finca])} registros CropX, "
              f"{BD_CROPX[finca].index.min()} a {BD_CROPX[finca].index.max()}")
    return BD_CROPX


# =============================================================================
# 3. FIGURAS CUANDO NO HAY DATOS
# =============================================================================
def mostrar_sin_datos(titulo: str, texto: str = "Sin datos en este rango de fechas",
                      figsize: tuple[float, float] = (10, 3)) -> None:
    """Muestra una figura vacía con un aviso, para que una etapa sin datos se vea en vez de dar error.

    Args:
        titulo (str): Título de la figura.
        texto (str): Mensaje en el centro.
        figsize (tuple[float, float]): Tamaño de la figura en pulgadas.

    Returns:
        None: Muestra la figura.
    """
    fig, ax = plt.subplots(figsize=figsize)
    ax.text(0.5, 0.5, texto, ha="center", va="center", fontsize=12, color="0.4", transform=ax.transAxes)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(titulo)
    plt.show()


# =============================================================================
# 4. BANDAS DE REFERENCIA (notebooks 04 y 05)
# =============================================================================
def contar_por_banda(serie: pd.Series, bandas: list[tuple[float, float]]) -> pd.DataFrame:
    """Contar datos dentro y fuera de cada banda.

    Args:
        serie (pd.Series): Valores de la variable (se ignoran los NaN).
        bandas (list[tuple[float, float]]): Lista de (mínimo, máximo) de cada banda.

    Returns:
        pd.DataFrame: Una fila por banda con conteos y porcentajes dentro/fuera.
    """
    datos = serie.dropna()
    total = len(datos)
    filas = []
    for i, (bmin, bmax) in enumerate(bandas, 1):
        dentro = int(datos.between(bmin, bmax).sum())
        filas.append({"Banda": f"Banda {i}", "Rango": f"{bmin:.2f} - {bmax:.2f}",
                      "Dentro": dentro, "% Dentro": 100 * dentro / total if total else np.nan,
                      "Fuera": total - dentro, "% Fuera": 100 * (total - dentro) / total if total else np.nan})
    return pd.DataFrame(filas).set_index("Banda")


def _ajustar_slider(slider: widgets.FloatRangeSlider, vmin: float, vmax: float) -> None:
    """Ajusta límites del slider al rango de la variable y lo deja desactivado (min == max).

    Args:
        slider (widgets.FloatRangeSlider): Slider de banda.
        vmin (float): Mínimo de la variable.
        vmax (float): Máximo de la variable.

    Returns:
        None
    """
    if not np.isfinite(vmin) or not np.isfinite(vmax):    # variable sin datos
        vmin, vmax = 0.0, 1.0
    if vmax <= vmin:
        vmax = vmin + 1
    slider.max = max(slider.max, vmax)
    slider.min = min(slider.min, vmin)
    slider.value = (vmin, vmin)
    slider.min, slider.max = vmin, vmax
    slider.step = (vmax - vmin) / 200
