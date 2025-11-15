# Módulo ml_data: Preparación de Datos para Machine Learning

## Descripción

El módulo `tfm.ml_data` proporciona herramientas para preparar datos históricos de retornos con variables target conocidas, específicamente diseñado para modelos de machine learning supervisado en trading.

Este módulo resuelve el problema común de transformar datos de series temporales de múltiples activos en un formato adecuado para entrenar modelos predictivos, incluyendo:

- Conversión a formato panel (Date, Asset)
- Generación de features basadas en ventanas móviles
- Creación de variables target adelantadas (forward-looking)
- Separación temporal train/test
- Escalado de features

## Funciones Principales

### `prepare_ml_pipeline()`

Función principal que orquesta todo el pipeline de preparación de datos.

**Uso básico:**

```python
from tfm import ml_data
import pandas as pd

# Supongamos que tienes un DataFrame de retornos diarios
# returns_df: índice = Date, columnas = símbolos de activos

data = ml_data.prepare_ml_pipeline(
    returns_df=returns_df,
    test_size=25,          # últimos 25 días para test
    windows={'1m': 21, '3m': 63, '6m': 126},
    target_window=21,       # predecir retornos a 21 días
    scale=True              # escalar features
)

# El resultado es un diccionario con todo lo necesario
X_train = data['X_train']
y_train = data['y_train']
X_test = data['X_test']
y_test = data['y_test']
```

**Retorna:**

Un diccionario con las siguientes claves:

- `train_panel`: Panel de entrenamiento completo (con todas las columnas)
- `test_panel`: Panel de prueba completo
- `X_train`: Features de entrenamiento (matriz escalada si scale=True)
- `y_train`: Target de entrenamiento (Series)
- `X_test`: Features de prueba (matriz escalada si scale=True)
- `y_test`: Target de prueba (Series)
- `scaler`: StandardScaler usado (None si scale=False)
- `feature_cols`: Lista de nombres de features

### Funciones Individuales

Si prefieres más control, puedes usar las funciones individuales:

#### `create_panel_data(returns_df)`

Convierte DataFrame de retornos en formato panel.

```python
panel = ml_data.create_panel_data(returns_df)
# Panel con MultiIndex (Date, Asset) y columna 'ret'
```

#### `add_rolling_features(panel, windows)`

Añade features basadas en ventanas móviles.

```python
panel = ml_data.add_rolling_features(
    panel,
    windows={'1m': 21, '3m': 63, '6m': 126}
)
# Añade columnas: ret_1m, ret_3m, ret_6m, vol_1m, vol_3m, vol_6m
```

#### `add_target_variable(panel, target_window, target_col)`

Añade variable target (retornos futuros).

```python
panel = ml_data.add_target_variable(
    panel,
    target_window=21,
    target_col='target_21d'
)
# Añade columna target_21d con retornos adelantados
```

#### `split_features_target(panel, feature_cols, target_col)`

Separa features (X) y target (y).

```python
X, y = ml_data.split_features_target(
    panel,
    feature_cols=['ret_1m', 'ret_3m', 'ret_6m', 'vol_1m', 'vol_3m', 'vol_6m'],
    target_col='target_21d'
)
```

#### `scale_features(X_train, X_test, scaler)`

Escala features usando StandardScaler.

```python
X_train_scaled, X_test_scaled, scaler = ml_data.scale_features(
    X_train,
    X_test
)
```

## Ejemplo Completo

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "src"))

from tfm import ml_data, universe
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

# 1. Cargar datos de activos
ohlcv_dict, universe_config, tickers_ok = universe.load_and_prepare_universe(
    universe_path=Path("config/universe/universe_equities.yaml"),
    years_of_data=2,
    max_missing_pct=0.10
)

# 2. Calcular retornos
adj_close = ohlcv_dict['adj_close']
returns_df = adj_close.pct_change()

# 3. Preparar datos para ML
data = ml_data.prepare_ml_pipeline(
    returns_df=returns_df,
    test_size=25,
    windows={'1m': 21, '3m': 63, '6m': 126},
    target_window=21,
    scale=True
)

# 4. Entrenar modelo
model = RandomForestRegressor(
    n_estimators=300,
    max_depth=6,
    random_state=42,
    n_jobs=-1
)

model.fit(data['X_train'], data['y_train'])

# 5. Evaluar modelo
y_pred = model.predict(data['X_test'])

mse = mean_squared_error(data['y_test'], y_pred)
r2 = r2_score(data['y_test'], y_pred)

print(f"MSE: {mse:.4f}")
print(f"R²: {r2:.4f}")

# 6. Generar señales de trading
test_panel = data['test_panel'].copy()
test_panel['pred'] = y_pred
test_panel['signal'] = (test_panel['pred'] > 0).astype(int)
test_panel['strategy_ret'] = test_panel['signal'] * test_panel['target_21d']

# 7. Calcular rendimiento
daily_results = test_panel.groupby("Date")[['target_21d', 'strategy_ret']].mean()
cumsum_bh = daily_results['target_21d'].cumsum()
cumsum_strategy = daily_results['strategy_ret'].cumsum()

print(f"\nRetorno Buy & Hold: {cumsum_bh.iloc[-1]:.2%}")
print(f"Retorno Estrategia ML: {cumsum_strategy.iloc[-1]:.2%}")
```

## Conceptos Clave

### Formato Panel

El módulo trabaja con datos en formato panel (también conocido como "long format"):

```
                    ret    ret_1m  ret_3m  vol_1m  target_21d
Date       Asset                                              
2023-01-30 AAPL    0.015   0.045   0.123   0.012    0.034
           MSFT    0.012   0.038   0.115   0.015    0.028
           GOOGL   0.018   0.052   0.134   0.018    0.041
2023-01-31 AAPL    0.008   0.041   0.119   0.013    0.029
           ...
```

Este formato permite aplicar operaciones por activo de forma eficiente.

### Features de Ventanas Móviles

Las features capturan patrones históricos:

- **Retornos acumulados** (`ret_1m`, `ret_3m`, `ret_6m`): Momentum a diferentes horizontes
- **Volatilidad** (`vol_1m`, `vol_3m`, `vol_6m`): Riesgo/incertidumbre a diferentes horizontes

### Target Adelantado

El target es el retorno futuro acumulado en los próximos N días:

```python
target_21d = sum(retornos_próximos_21_días)
```

**Importante:** Esto crea "data leakage" si no se maneja correctamente. El módulo garantiza que:
1. El target se calcula usando `shift(-N)` para adelantar los valores
2. La separación train/test es temporal (nunca se entrena con datos futuros al test)

### Separación Temporal

A diferencia de problemas de ML tradicionales, en series temporales la separación debe ser temporal:

```
|<------- Training ------->|<-- Test -->|
|                          |            |
fecha_inicio          cutoff_date    fecha_fin
```

El módulo maneja esto automáticamente.

## Consideraciones Importantes

### 1. Valores Nulos

Las ventanas móviles y el target adelantado generan valores `NaN` al inicio y final de la serie. El módulo elimina estos valores automáticamente con `drop_na=True` (recomendado).

### 2. Data Leakage

El módulo previene data leakage asegurando que:
- El target se crea ANTES de separar train/test
- El scaler se ajusta SOLO con datos de entrenamiento
- No hay información futura en el conjunto de entrenamiento

### 3. Ventanas Recomendadas

```python
windows = {
    '1m': 21,    # ~1 mes (días de trading)
    '3m': 63,    # ~3 meses
    '6m': 126    # ~6 meses
}
```

Ajusta según tu estrategia y frecuencia de trading.

### 4. Target Window

```python
target_window = 21  # Para estrategias mensuales
target_window = 5   # Para estrategias semanales
target_window = 1   # Para estrategias diarias
```

## Integración con el Notebook

Para integrar este módulo en el notebook `TFM-TRADING_ADAPTATIVO.ipynb`:

```python
# En lugar de:
# ... código extenso para crear panel, features, target, etc.

# Usar:
from tfm import ml_data

data = ml_data.prepare_ml_pipeline(
    returns_df=retornos_activos,
    test_size=25,
    scale=True
)

# Continuar con el modelo
model = RandomForestRegressor(n_estimators=300, max_depth=6, random_state=42)
model.fit(data['X_train'], data['y_train'])
```

## Ejecutar el Ejemplo

```bash
python examples/ml_data_preparation_example.py
```

Este ejemplo genera datos sintéticos, prepara el dataset, entrena un modelo y genera visualizaciones.

## Referencias

- Ver ejemplo completo: `examples/ml_data_preparation_example.py`
- Ver código fuente: `src/tfm/ml_data.py`
- Ver notebook principal: `Notebooks/TFM-TRADING_ADAPTATIVO.ipynb`

## Próximas Mejoras

- Soporte para múltiples targets (clasificación, regresión)
- Validación cruzada walk-forward
- Selección automática de features
- Métricas de evaluación específicas para trading
