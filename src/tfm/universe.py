"""
Módulo para gestión del universo de activos financieros.

Este módulo proporciona funciones para:
- Cargar configuración del universo desde YAML
- Descargar datos históricos OHLCV desde Yahoo Finance
- Validar calidad de datos
- Filtrar activos por disponibilidad de datos
- Guardar y cargar snapshots de datos
"""

from pathlib import Path
from typing import Dict, List, Tuple, Optional
import datetime as dt
import yaml
import pandas as pd
import yfinance as yf
import warnings

# Suprimir warnings comunes de yfinance y pandas
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)


def load_universe_config(universe_path: Path) -> dict:
    """
    Carga la configuración del universo desde un archivo YAML.
    
    Args:
        universe_path: Ruta al archivo YAML del universo
        
    Returns:
        Diccionario con la configuración del universo
        
    Raises:
        FileNotFoundError: Si el archivo no existe
        yaml.YAMLError: Si hay un error al parsear el YAML
    """
    if not universe_path.exists():
        raise FileNotFoundError(f"Archivo de universo no encontrado: {universe_path}")
    
    with open(universe_path, 'r', encoding='utf-8') as f:
        universe = yaml.safe_load(f)
    
    if 'tickers' not in universe:
        raise ValueError("El archivo de universo debe contener una clave 'tickers'")
    
    return universe


def extract_symbols(universe: dict) -> List[str]:
    """
    Extrae los símbolos de Yahoo Finance del universo.
    
    Args:
        universe: Diccionario de configuración del universo
        
    Returns:
        Lista de símbolos de Yahoo Finance
    """
    return [ticker["symbol_yf"] for ticker in universe["tickers"]]


def download_ohlcv_data(
    symbols: List[str],
    start_date: str,
    end_date: str,
    auto_adjust: bool = False,
    progress: bool = False
) -> pd.DataFrame:
    """
    Descarga datos OHLCV desde Yahoo Finance para una lista de símbolos.
    
    Args:
        symbols: Lista de símbolos a descargar
        start_date: Fecha de inicio (formato 'YYYY-MM-DD')
        end_date: Fecha de fin (formato 'YYYY-MM-DD')
        auto_adjust: Si True, usa precios ajustados automáticamente
        progress: Si True, muestra barra de progreso
        
    Returns:
        DataFrame con MultiIndex (Date, (Ticker, Field))
        
    Raises:
        ValueError: Si no se pueden descargar datos
    """
    print(f"Descargando datos OHLCV para {len(symbols)} activos desde Yahoo Finance...")
    print(f"Período: {start_date} a {end_date}")
    
    # Descarga completa OHLCV
    raw = yf.download(
        tickers=symbols,
        start=start_date,
        end=end_date,
        auto_adjust=auto_adjust,
        group_by="ticker",
        progress=progress
    )
    
    if raw.empty:
        raise ValueError("No se pudieron descargar datos. Verifica símbolos y fechas.")
    
    # Construir estructura final con todas las columnas por ticker
    full_data = {}
    failed_tickers = []
    
    for ticker in symbols:
        try:
            # Manejar caso de un solo ticker (estructura diferente)
            if len(symbols) == 1:
                df_t = raw[["Open", "High", "Low", "Close", "Adj Close", "Volume"]]
            else:
                df_t = raw[ticker][["Open", "High", "Low", "Close", "Adj Close", "Volume"]]
            full_data[ticker] = df_t
        except (KeyError, TypeError):
            failed_tickers.append(ticker)
            print(f"[WARN] {ticker}: no descargado")
    
    if failed_tickers:
        print(f"\nTotal de activos no descargados: {len(failed_tickers)}")
    
    # Crear un MultiIndex DataFrame: niveles → Fecha × (Ticker, Campo)
    prices_df = pd.concat(full_data, axis=1)
    
    print(f"Descarga completada. Dimensiones: {prices_df.shape}")
    print(f"Activos descargados exitosamente: {len(full_data)}/{len(symbols)}")
    
    return prices_df


def split_ohlcv_dataframe(prices_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Separa el DataFrame MultiIndex en DataFrames individuales por campo OHLCV.
    
    Args:
        prices_df: DataFrame con MultiIndex (Date, (Ticker, Field))
        
    Returns:
        Diccionario con claves 'open', 'high', 'low', 'close', 'adj_close', 'volume'
    """
    return {
        'open': prices_df.xs("Open", level=1, axis=1).copy(),
        'high': prices_df.xs("High", level=1, axis=1).copy(),
        'low': prices_df.xs("Low", level=1, axis=1).copy(),
        'close': prices_df.xs("Close", level=1, axis=1).copy(),
        'adj_close': prices_df.xs("Adj Close", level=1, axis=1).copy(),
        'volume': prices_df.xs("Volume", level=1, axis=1).copy()
    }


def filter_by_data_availability(
    ohlcv_dict: Dict[str, pd.DataFrame],
    max_missing_pct: float = 0.10,
    reference_field: str = 'adj_close'
) -> Tuple[Dict[str, pd.DataFrame], List[str], List[str]]:
    """
    Filtra activos basándose en la disponibilidad de datos.
    
    Elimina activos con más del porcentaje especificado de datos faltantes.
    
    Args:
        ohlcv_dict: Diccionario con DataFrames OHLCV
        max_missing_pct: Porcentaje máximo de datos faltantes permitido (0.0 a 1.0)
        reference_field: Campo de referencia para calcular datos faltantes
        
    Returns:
        Tupla con:
        - Diccionario filtrado de DataFrames OHLCV
        - Lista de tickers válidos
        - Lista de tickers eliminados
    """
    adj_df = ohlcv_dict[reference_field]
    
    # Calcular porcentaje de nulos por ticker
    missing_pct = adj_df.isna().mean()
    
    tickers_ok = missing_pct[missing_pct <= max_missing_pct].index.tolist()
    tickers_bad = missing_pct[missing_pct > max_missing_pct].index.tolist()
    
    if tickers_bad:
        print(f"\nActivos eliminados (>{max_missing_pct*100:.0f}% datos faltantes):")
        for ticker in tickers_bad:
            print(f"  - {ticker}: {missing_pct[ticker]*100:.1f}% faltante")
    
    # Filtrar en TODOS los DataFrames OHLCV
    filtered_dict = {
        field: df[tickers_ok] for field, df in ohlcv_dict.items()
    }
    
    print(f"\nActivos válidos: {len(tickers_ok)}/{len(missing_pct)}")
    
    return filtered_dict, tickers_ok, tickers_bad


def save_snapshot(
    prices_df: pd.DataFrame,
    snapshot_dir: Path,
    prefix: str = "prices_OHLCV"
) -> Path:
    """
    Guarda un snapshot de los datos de precios.
    
    Args:
        prices_df: DataFrame de precios a guardar
        snapshot_dir: Directorio donde guardar el snapshot
        prefix: Prefijo para el nombre del archivo
        
    Returns:
        Ruta del archivo guardado
    """
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    snapshot_name = f"{prefix}_{dt.date.today().strftime('%Y%m%d')}.csv.gz"
    snapshot_path = snapshot_dir / snapshot_name
    
    prices_df.to_csv(snapshot_path, compression="gzip")
    print(f"Snapshot guardado en: {snapshot_path}")
    
    return snapshot_path


def load_snapshot(snapshot_path: Path) -> pd.DataFrame:
    """
    Carga un snapshot de datos previamente guardado.
    
    Args:
        snapshot_path: Ruta al archivo snapshot
        
    Returns:
        DataFrame con los datos cargados
        
    Raises:
        FileNotFoundError: Si el archivo no existe
    """
    if not snapshot_path.exists():
        raise FileNotFoundError(f"Snapshot no encontrado: {snapshot_path}")
    
    print(f"Cargando snapshot desde: {snapshot_path}")
    
    # Leer el CSV con MultiIndex
    df = pd.read_csv(snapshot_path, compression="gzip", header=[0, 1], index_col=0, parse_dates=True)
    
    print(f"Snapshot cargado. Dimensiones: {df.shape}")
    
    return df


def load_and_prepare_universe(
    universe_path: Path,
    years_of_data: int = 2,
    max_missing_pct: float = 0.10,
    save_snapshot_dir: Optional[Path] = None
) -> Tuple[Dict[str, pd.DataFrame], dict, List[str]]:
    """
    Función de alto nivel que carga el universo, descarga datos y los prepara.
    
    Esta función integra todo el flujo de trabajo:
    1. Carga configuración del universo
    2. Descarga datos OHLCV
    3. Filtra por calidad de datos
    4. Opcionalmente guarda un snapshot
    
    Args:
        universe_path: Ruta al archivo YAML del universo
        years_of_data: Número de años de datos históricos a descargar
        max_missing_pct: Porcentaje máximo de datos faltantes permitido
        save_snapshot_dir: Si se proporciona, guarda un snapshot en este directorio
        
    Returns:
        Tupla con:
        - Diccionario de DataFrames OHLCV filtrados
        - Configuración del universo
        - Lista de tickers válidos
    """
    # 1. Cargar configuración del universo
    universe = load_universe_config(universe_path)
    symbols_yf = extract_symbols(universe)
    
    # 2. Calcular fechas
    start_date = (dt.date.today() - dt.timedelta(days=365*years_of_data)).strftime("%Y-%m-%d")
    end_date = dt.date.today().strftime("%Y-%m-%d")
    
    # 3. Descargar datos OHLCV
    prices_df = download_ohlcv_data(
        symbols=symbols_yf,
        start_date=start_date,
        end_date=end_date,
        auto_adjust=False,
        progress=False
    )
    
    # 4. Guardar snapshot si se especifica
    if save_snapshot_dir:
        save_snapshot(prices_df, save_snapshot_dir)
    
    # 5. Separar en DataFrames individuales
    ohlcv_dict = split_ohlcv_dataframe(prices_df)
    
    # 6. Filtrar por disponibilidad de datos
    filtered_dict, tickers_ok, tickers_bad = filter_by_data_availability(
        ohlcv_dict,
        max_missing_pct=max_missing_pct
    )
    
    return filtered_dict, universe, tickers_ok
