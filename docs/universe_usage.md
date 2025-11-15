# Módulo Universe - Ejemplos de Uso

El módulo `tfm.universe` proporciona funciones para gestionar el universo de activos financieros del proyecto TFM.

## Instalación de Dependencias

```bash
pip install -r requirements.txt
```

## Uso Básico

### 1. Cargar y preparar el universo completo

La forma más sencilla de usar el módulo es con la función de alto nivel `load_and_prepare_universe()`:

```python
from pathlib import Path
from tfm import universe

# Definir rutas
PROJECT_ROOT = Path(__file__).resolve().parent
universe_path = PROJECT_ROOT / "config" / "universe" / "universe_equities.yaml"
snapshot_dir = PROJECT_ROOT / "data" / "snapshots"

# Cargar y preparar todo el universo
ohlcv_dict, universe_config, tickers_ok = universe.load_and_prepare_universe(
    universe_path=universe_path,
    years_of_data=2,                # 2 años de datos históricos
    max_missing_pct=0.10,           # Máximo 10% de datos faltantes
    save_snapshot_dir=snapshot_dir  # Guardar snapshot
)

# Usar los datos
adj_close_df = ohlcv_dict['adj_close']
print(f"Activos válidos: {len(tickers_ok)}")
print(f"Dimensiones: {adj_close_df.shape}")
```

### 2. Uso paso a paso (más control)

Si necesitas más control sobre el proceso:

```python
from pathlib import Path
import datetime as dt
from tfm import universe

PROJECT_ROOT = Path(__file__).resolve().parent

# Paso 1: Cargar configuración del universo
universe_path = PROJECT_ROOT / "config" / "universe" / "universe_equities.yaml"
universe_config = universe.load_universe_config(universe_path)

# Paso 2: Extraer símbolos
symbols = universe.extract_symbols(universe_config)
print(f"Total de activos: {len(symbols)}")

# Paso 3: Descargar datos OHLCV
start_date = (dt.date.today() - dt.timedelta(days=365*2)).strftime("%Y-%m-%d")
end_date = dt.date.today().strftime("%Y-%m-%d")

prices_df = universe.download_ohlcv_data(
    symbols=symbols,
    start_date=start_date,
    end_date=end_date,
    auto_adjust=False,
    progress=False
)

# Paso 4: Separar en DataFrames individuales
ohlcv_dict = universe.split_ohlcv_dataframe(prices_df)

# Paso 5: Filtrar por disponibilidad de datos
filtered_dict, tickers_ok, tickers_bad = universe.filter_by_data_availability(
    ohlcv_dict,
    max_missing_pct=0.10  # Eliminar activos con >10% datos faltantes
)

# Paso 6: Guardar snapshot (opcional)
snapshot_dir = PROJECT_ROOT / "data" / "snapshots"
snapshot_path = universe.save_snapshot(prices_df, snapshot_dir)

print(f"Activos válidos: {len(tickers_ok)}")
print(f"Activos eliminados: {len(tickers_bad)}")
```

### 3. Trabajar con snapshots guardados

```python
from pathlib import Path
from tfm import universe

PROJECT_ROOT = Path(__file__).resolve().parent

# Cargar un snapshot existente
snapshot_path = PROJECT_ROOT / "data" / "snapshots" / "prices_OHLCV_20251115.csv.gz"
prices_df = universe.load_snapshot(snapshot_path)

# Procesar los datos
ohlcv_dict = universe.split_ohlcv_dataframe(prices_df)

# Acceder a los diferentes campos
open_df = ohlcv_dict['open']
high_df = ohlcv_dict['high']
low_df = ohlcv_dict['low']
close_df = ohlcv_dict['close']
adj_close_df = ohlcv_dict['adj_close']
volume_df = ohlcv_dict['volume']
```

### 4. Descargar solo un subconjunto de activos

```python
from tfm import universe
import datetime as dt

# Seleccionar solo algunos activos
symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA']

# Configurar fechas
start_date = (dt.date.today() - dt.timedelta(days=365)).strftime("%Y-%m-%d")
end_date = dt.date.today().strftime("%Y-%m-%d")

# Descargar datos
prices_df = universe.download_ohlcv_data(
    symbols=symbols,
    start_date=start_date,
    end_date=end_date
)

# Procesar
ohlcv_dict = universe.split_ohlcv_dataframe(prices_df)
```

## Integración con el Notebook

Para usar el módulo en el notebook `TFM-TRADING_ADAPTATIVO.ipynb`, reemplaza el código de la celda 10-13 con:

```python
from tfm import universe
from pathlib import Path

# Cargar y preparar el universo
ohlcv_dict, universe_config, tickers_ok = universe.load_and_prepare_universe(
    universe_path=PROJECT_ROOT / "config" / "universe" / "universe_equities.yaml",
    years_of_data=2,
    max_missing_pct=0.10,
    save_snapshot_dir=PROJECT_ROOT / "data" / "snapshots"
)

# Extraer los DataFrames OHLCV
open_df = ohlcv_dict['open']
high_df = ohlcv_dict['high']
low_df = ohlcv_dict['low']
close_df = ohlcv_dict['close']
adj_df = ohlcv_dict['adj_close']
vol_df = ohlcv_dict['volume']

print(f"Universo cargado: {len(tickers_ok)} activos válidos")
```

## Estructura de Datos

### DataFrame de precios (prices_df)

MultiIndex DataFrame con estructura:
- **Índice (rows)**: Fechas (Date)
- **Columnas (cols)**: MultiIndex (Ticker, Field)
  - Nivel 1: Ticker (e.g., 'AAPL', 'GOOGL')
  - Nivel 2: Field (e.g., 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume')

### Diccionario OHLCV (ohlcv_dict)

Diccionario con las siguientes claves:
- `'open'`: DataFrame de precios de apertura
- `'high'`: DataFrame de precios máximos
- `'low'`: DataFrame de precios mínimos
- `'close'`: DataFrame de precios de cierre
- `'adj_close'`: DataFrame de precios de cierre ajustados
- `'volume'`: DataFrame de volúmenes

Cada DataFrame tiene:
- **Índice (rows)**: Fechas
- **Columnas (cols)**: Tickers

## Configuración del Universo (YAML)

El archivo `config/universe/universe_equities.yaml` debe tener la siguiente estructura:

```yaml
tickers:
  - name: Apple Inc.
    symbol_yf: AAPL
    symbol_alpaca: AAPL
    country: USA
    sector: Technology
    source: yfinance
    min_years: 4
  - name: Alphabet Inc.
    symbol_yf: GOOGL
    symbol_alpaca: GOOGL
    country: USA
    sector: Technology
    source: yfinance
    min_years: 4
  # ... más activos
```

## Manejo de Errores

```python
from tfm import universe
from pathlib import Path

try:
    # Cargar universo
    universe_config = universe.load_universe_config(universe_path)
except FileNotFoundError:
    print("Archivo de universo no encontrado")
except ValueError as e:
    print(f"Error en la configuración: {e}")

try:
    # Descargar datos
    prices_df = universe.download_ohlcv_data(symbols, start_date, end_date)
except ValueError:
    print("No se pudieron descargar datos. Verifica símbolos y fechas.")
```

## Parámetros Clave

### `max_missing_pct`
- **Tipo**: float (0.0 a 1.0)
- **Default**: 0.10
- **Descripción**: Porcentaje máximo de datos faltantes permitido por activo
- **Ejemplo**: 0.10 = 10% de datos faltantes máximo

### `years_of_data`
- **Tipo**: int
- **Default**: 2
- **Descripción**: Número de años de datos históricos a descargar
- **Ejemplo**: 2 = últimos 2 años

### `auto_adjust`
- **Tipo**: bool
- **Default**: False
- **Descripción**: Si True, usa precios ajustados automáticamente por yfinance

### `progress`
- **Tipo**: bool
- **Default**: False
- **Descripción**: Si True, muestra barra de progreso durante la descarga

## Notas Importantes

1. **Acceso a Internet**: La descarga de datos requiere acceso a Yahoo Finance
2. **Rate Limiting**: Yahoo Finance puede limitar solicitudes; usa snapshots para evitar descargas repetidas
3. **Datos Faltantes**: Los activos con >10% de datos faltantes son eliminados por defecto
4. **Snapshots**: Se recomienda guardar snapshots para reproducibilidad y análisis offline

## Troubleshooting

### Error: "No se pudieron descargar datos"
- Verifica que los símbolos sean válidos en Yahoo Finance
- Verifica tu conexión a internet
- Considera usar símbolos alternativos o actualizar el universo

### Error: "Archivo de universo no encontrado"
- Verifica la ruta al archivo YAML
- Asegúrate de que el archivo existe en `config/universe/`

### Advertencias de deprecación de pandas
- Estas advertencias son normales y están suprimidas en el módulo
- Se corregirán en futuras versiones de las dependencias
