"""
Módulo para preparación de datos históricos con targets conocidos para ML.

Este módulo proporciona funciones para:
- Convertir datos de retornos en formato panel (Date, Asset)
- Generar features basadas en ventanas móviles (retornos y volatilidad)
- Crear variables target (retornos futuros) para aprendizaje supervisado
- Separar datos en conjuntos de entrenamiento y prueba con orden temporal
- Escalar features para modelos de machine learning
"""

from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler


def create_panel_data(returns_df: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte una matriz de retornos en formato panel (Date, Asset).
    
    Args:
        returns_df: DataFrame con índice Date y columnas Asset, conteniendo retornos diarios
        
    Returns:
        DataFrame con MultiIndex (Date, Asset) y columna 'ret' con los retornos
        
    Example:
        >>> returns = pd.DataFrame({'AAPL': [0.01, 0.02], 'MSFT': [0.015, 0.025]})
        >>> panel = create_panel_data(returns)
        >>> panel.index.names
        ['Date', 'Asset']
    """
    panel = returns_df.stack().to_frame("ret")
    panel.index.names = ["Date", "Asset"]
    return panel


def add_rolling_features(
    panel: pd.DataFrame,
    windows: Optional[Dict[str, int]] = None
) -> pd.DataFrame:
    """
    Añade features basadas en ventanas móviles de retornos y volatilidad.
    
    Args:
        panel: DataFrame con MultiIndex (Date, Asset) y columna 'ret'
        windows: Diccionario con nombres de períodos y sus ventanas en días.
                 Por defecto: {'1m': 21, '3m': 63, '6m': 126}
        
    Returns:
        DataFrame con columnas adicionales: ret_1m, ret_3m, ret_6m, vol_1m, vol_3m, vol_6m
        
    Example:
        >>> panel = create_panel_data(returns_df)
        >>> panel_with_features = add_rolling_features(panel)
    """
    if windows is None:
        windows = {'1m': 21, '3m': 63, '6m': 126}
    
    panel = panel.copy()
    g = panel.groupby("Asset")["ret"]
    
    # Crear features de retornos acumulados
    for period_name, window_size in windows.items():
        panel[f"ret_{period_name}"] = g.rolling(window_size).sum().reset_index(level=0, drop=True)
    
    # Crear features de volatilidad
    for period_name, window_size in windows.items():
        panel[f"vol_{period_name}"] = g.rolling(window_size).std().reset_index(level=0, drop=True)
    
    return panel


def add_target_variable(
    panel: pd.DataFrame,
    target_window: int = 21,
    target_col: str = "target_21d"
) -> pd.DataFrame:
    """
    Añade variable target: retorno adelantado (futuro) para aprendizaje supervisado.
    
    Args:
        panel: DataFrame con MultiIndex (Date, Asset) y columna 'ret'
        target_window: Ventana de días para calcular el retorno futuro (default: 21)
        target_col: Nombre de la columna target a crear (default: 'target_21d')
        
    Returns:
        DataFrame con columna target adicional
        
    Note:
        La columna target contiene el retorno futuro acumulado de los próximos
        target_window días. Usa shift(-target_window) para adelantar los valores.
    """
    panel = panel.copy()
    g = panel.groupby("Asset")["ret"]
    
    # Crear target: retorno adelantado a target_window días
    panel[target_col] = g.rolling(target_window).sum().shift(-target_window).reset_index(level=0, drop=True)
    
    return panel


def prepare_ml_dataset(
    returns_df: pd.DataFrame,
    test_size: int = 25,
    windows: Optional[Dict[str, int]] = None,
    target_window: int = 21,
    drop_na: bool = True
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepara un dataset completo para ML con features y target.
    
    Pipeline completo que:
    1. Convierte retornos a formato panel
    2. Añade features de ventanas móviles
    3. Añade variable target (retornos futuros)
    4. Separa en train y test manteniendo orden temporal
    5. Elimina valores nulos (opcional)
    
    Args:
        returns_df: DataFrame con índice Date y columnas Asset, conteniendo retornos diarios
        test_size: Número de días para el conjunto de test (default: 25)
        windows: Diccionario con ventanas para features (default: {'1m': 21, '3m': 63, '6m': 126})
        target_window: Ventana para el target en días (default: 21)
        drop_na: Si True, elimina filas con valores nulos (default: True)
        
    Returns:
        Tupla (train_panel, test_panel) con los datos preparados
        
    Example:
        >>> train, test = prepare_ml_dataset(returns_df, test_size=25)
        >>> features = ['ret_1m', 'ret_3m', 'ret_6m', 'vol_1m', 'vol_3m', 'vol_6m']
        >>> X_train = train[features]
        >>> y_train = train['target_21d']
    """
    # Separar train y test temporalmente
    returns_train = returns_df.iloc[:-test_size]
    
    # Convertir a panel
    panel = create_panel_data(returns_train)
    
    # Añadir features
    panel = add_rolling_features(panel, windows=windows)
    
    # Añadir target
    panel = add_target_variable(panel, target_window=target_window)
    
    # Eliminar valores nulos si se especifica
    if drop_na:
        panel = panel.dropna()
    
    # Separar train y test (últimos test_size días del índice original de train)
    cutoff = returns_train.index[-test_size]
    train_panel = panel.loc[panel.index.get_level_values("Date") < cutoff]
    test_panel = panel.loc[panel.index.get_level_values("Date") >= cutoff]
    
    return train_panel, test_panel


def split_features_target(
    panel: pd.DataFrame,
    feature_cols: Optional[List[str]] = None,
    target_col: str = "target_21d"
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Separa features (X) y target (y) de un panel de datos.
    
    Args:
        panel: DataFrame con features y target
        feature_cols: Lista de nombres de columnas a usar como features.
                     Por defecto: ['ret_1m', 'ret_3m', 'ret_6m', 'vol_1m', 'vol_3m', 'vol_6m']
        target_col: Nombre de la columna target (default: 'target_21d')
        
    Returns:
        Tupla (X, y) con features y target
        
    Example:
        >>> X_train, y_train = split_features_target(train_panel)
        >>> X_test, y_test = split_features_target(test_panel)
    """
    if feature_cols is None:
        feature_cols = ['ret_1m', 'ret_3m', 'ret_6m', 'vol_1m', 'vol_3m', 'vol_6m']
    
    X = panel[feature_cols]
    y = panel[target_col]
    
    return X, y


def scale_features(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    scaler: Optional[StandardScaler] = None
) -> Tuple[np.ndarray, np.ndarray, StandardScaler]:
    """
    Escala features usando StandardScaler, ajustando solo con datos de entrenamiento.
    
    Args:
        X_train: Features de entrenamiento
        X_test: Features de prueba
        scaler: StandardScaler preajustado (opcional). Si no se provee, se crea uno nuevo.
        
    Returns:
        Tupla (X_train_scaled, X_test_scaled, scaler) con arrays escalados y el scaler usado
        
    Note:
        Es fundamental que el scaler se ajuste SOLO con datos de entrenamiento
        para evitar data leakage.
        
    Example:
        >>> X_train_scaled, X_test_scaled, scaler = scale_features(X_train, X_test)
    """
    if scaler is None:
        scaler = StandardScaler()
    
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    return X_train_scaled, X_test_scaled, scaler


def prepare_ml_pipeline(
    returns_df: pd.DataFrame,
    test_size: int = 25,
    windows: Optional[Dict[str, int]] = None,
    target_window: int = 21,
    feature_cols: Optional[List[str]] = None,
    target_col: str = "target_21d",
    scale: bool = True
) -> Dict[str, any]:
    """
    Pipeline completo que prepara datos listos para entrenar un modelo de ML.
    
    Esta función orquesta todo el proceso de preparación de datos:
    1. Crea panel data con features y target
    2. Separa train/test temporalmente
    3. Extrae features y target
    4. Escala features (opcional)
    
    Args:
        returns_df: DataFrame con índice Date y columnas Asset, conteniendo retornos diarios
        test_size: Número de días para el conjunto de test (default: 25)
        windows: Diccionario con ventanas para features (default: {'1m': 21, '3m': 63, '6m': 126})
        target_window: Ventana para el target en días (default: 21)
        feature_cols: Lista de columnas a usar como features (default: automático)
        target_col: Nombre de la columna target (default: 'target_21d')
        scale: Si True, escala las features (default: True)
        
    Returns:
        Diccionario con todas las estructuras necesarias para ML:
        - 'train_panel': Panel de entrenamiento completo
        - 'test_panel': Panel de prueba completo
        - 'X_train': Features de entrenamiento (escaladas si scale=True)
        - 'y_train': Target de entrenamiento
        - 'X_test': Features de prueba (escaladas si scale=True)
        - 'y_test': Target de prueba
        - 'scaler': StandardScaler usado (None si scale=False)
        - 'feature_cols': Lista de nombres de features usadas
        
    Example:
        >>> data = prepare_ml_pipeline(returns_df, test_size=25)
        >>> from sklearn.ensemble import RandomForestRegressor
        >>> model = RandomForestRegressor(n_estimators=300, max_depth=6)
        >>> model.fit(data['X_train'], data['y_train'])
        >>> predictions = model.predict(data['X_test'])
    """
    # Preparar dataset con features y target
    train_panel, test_panel = prepare_ml_dataset(
        returns_df=returns_df,
        test_size=test_size,
        windows=windows,
        target_window=target_window,
        drop_na=True
    )
    
    # Separar features y target
    X_train, y_train = split_features_target(train_panel, feature_cols=feature_cols, target_col=target_col)
    X_test, y_test = split_features_target(test_panel, feature_cols=feature_cols, target_col=target_col)
    
    # Obtener los nombres de features usados
    if feature_cols is None:
        feature_cols = ['ret_1m', 'ret_3m', 'ret_6m', 'vol_1m', 'vol_3m', 'vol_6m']
    
    # Escalar features si se requiere
    scaler = None
    if scale:
        X_train, X_test, scaler = scale_features(X_train, X_test)
    
    return {
        'train_panel': train_panel,
        'test_panel': test_panel,
        'X_train': X_train,
        'y_train': y_train,
        'X_test': X_test,
        'y_test': y_test,
        'scaler': scaler,
        'feature_cols': feature_cols
    }
