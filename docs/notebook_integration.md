# Integración del Módulo Universe en el Notebook

Esta guía muestra cómo reemplazar el código de carga de datos del notebook con el nuevo módulo `tfm.universe`.

## Código Original (Celdas 10-13)

El notebook originalmente tenía aproximadamente 50+ líneas de código distribuidas en 4 celdas para:
- Descargar datos de Yahoo Finance
- Guardar snapshots
- Separar OHLCV
- Filtrar por disponibilidad de datos

## Código Nuevo (1 celda)

Reemplaza las celdas 10-13 con este código simplificado:

```python
# Celda 10 (NUEVA) - Cargar universo usando el módulo
from tfm import universe

print("Cargando universo de activos...")

# Cargar y preparar el universo completo en una sola línea
ohlcv_dict, universe_config, tickers_ok = universe.load_and_prepare_universe(
    universe_path=PROJECT_ROOT / "config" / "universe" / "universe_equities.yaml",
    years_of_data=2,
    max_missing_pct=0.10,
    save_snapshot_dir=PROJECT_ROOT / "data" / "snapshots"
)

# Extraer los DataFrames OHLCV (compatible con código existente)
open_df = ohlcv_dict['open']
high_df = ohlcv_dict['high']
low_df = ohlcv_dict['low']
close_df = ohlcv_dict['close']
adj_df = ohlcv_dict['adj_close']
vol_df = ohlcv_dict['volume']

print(f"\n✓ Universo cargado: {len(tickers_ok)} activos válidos")
print(f"  Período: {adj_df.index[0]} a {adj_df.index[-1]}")
print(f"  Dimensiones: {adj_df.shape}")
```

## Ventajas

1. **Menos código**: ~50 líneas reducidas a ~15 líneas
2. **Más legible**: Una sola función clara
3. **Reutilizable**: El mismo código funciona en scripts y notebooks
4. **Mantenible**: Los cambios se hacen en un solo lugar
5. **Testeable**: El módulo tiene tests unitarios
6. **Documentado**: Documentación completa disponible

## Compatibilidad

El código nuevo es 100% compatible con el resto del notebook porque:
- Las variables `open_df`, `high_df`, `low_df`, `close_df`, `adj_df`, `vol_df` se crean igual
- El formato de los DataFrames es idéntico
- La variable `universe` ahora se llama `universe_config` pero tiene la misma estructura

## Opcional: Visualización de Nulos

Si quieres mantener la visualización de nulos, añade después:

```python
# Opcional: Visualizar nulos como en el notebook original
import missingno as msno
import matplotlib.pyplot as plt

msno.matrix(adj_df)
plt.title("Datos disponibles (Adj Close)")
plt.show()
```

## Manejo de Errores

El módulo incluye manejo de errores automático:

```python
try:
    ohlcv_dict, universe_config, tickers_ok = universe.load_and_prepare_universe(
        universe_path=PROJECT_ROOT / "config" / "universe" / "universe_equities.yaml",
        years_of_data=2,
        max_missing_pct=0.10,
        save_snapshot_dir=PROJECT_ROOT / "data" / "snapshots"
    )
except FileNotFoundError:
    print("Error: Archivo de universo no encontrado")
except ValueError:
    print("Error: No se pudieron descargar datos. Usando snapshot previo...")
    # Cargar desde snapshot guardado
    snapshot_path = PROJECT_ROOT / "data" / "snapshots" / "prices_OHLCV_20251115.csv.gz"
    prices_df = universe.load_snapshot(snapshot_path)
    ohlcv_dict = universe.split_ohlcv_dataframe(prices_df)
    # Continuar con el análisis...
```

## Trabajar Offline

Si no tienes conexión a internet, puedes trabajar con snapshots guardados:

```python
from tfm import universe
from pathlib import Path

# Usar el último snapshot disponible
snapshot_dir = PROJECT_ROOT / "data" / "snapshots"
snapshot_files = sorted(snapshot_dir.glob("prices_OHLCV_*.csv.gz"))

if snapshot_files:
    latest_snapshot = snapshot_files[-1]
    print(f"Cargando snapshot: {latest_snapshot.name}")
    
    prices_df = universe.load_snapshot(latest_snapshot)
    ohlcv_dict = universe.split_ohlcv_dataframe(prices_df)
    
    # Filtrar por disponibilidad
    filtered_dict, tickers_ok, tickers_bad = universe.filter_by_data_availability(
        ohlcv_dict,
        max_missing_pct=0.10
    )
    
    # Usar los datos filtrados
    open_df = filtered_dict['open']
    high_df = filtered_dict['high']
    low_df = filtered_dict['low']
    close_df = filtered_dict['close']
    adj_df = filtered_dict['adj_close']
    vol_df = filtered_dict['volume']
else:
    print("No hay snapshots disponibles. Descarga datos primero.")
```

## Personalización

Ajusta los parámetros según necesites:

```python
# Descargar solo 1 año de datos
ohlcv_dict, universe_config, tickers_ok = universe.load_and_prepare_universe(
    universe_path=PROJECT_ROOT / "config" / "universe" / "universe_equities.yaml",
    years_of_data=1,  # 1 año en lugar de 2
    max_missing_pct=0.05,  # Más estricto: solo 5% de datos faltantes
    save_snapshot_dir=PROJECT_ROOT / "data" / "snapshots"
)
```

```python
# No guardar snapshot
ohlcv_dict, universe_config, tickers_ok = universe.load_and_prepare_universe(
    universe_path=PROJECT_ROOT / "config" / "universe" / "universe_equities.yaml",
    years_of_data=2,
    max_missing_pct=0.10,
    save_snapshot_dir=None  # No guardar
)
```

## Siguiente Paso

Una vez integrado el módulo en el notebook, el resto del código funciona sin cambios. Las celdas posteriores que usan `adj_df`, `close_df`, etc., funcionarán exactamente igual.
