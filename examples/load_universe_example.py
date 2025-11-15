#!/usr/bin/env python3
"""
Ejemplo de uso del módulo universe para cargar el universo de activos.

Este script demuestra cómo usar el módulo tfm.universe para:
1. Cargar la configuración del universo
2. Descargar datos OHLCV de Yahoo Finance
3. Filtrar activos por disponibilidad de datos
4. Guardar y trabajar con los datos
"""

import sys
from pathlib import Path

# Configurar rutas del proyecto
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Importar el módulo universe
from tfm import bootstrap, universe

# Inicializar el entorno (semillas, configuración, etc.)
print("Inicializando entorno...")
seed = bootstrap()
print(f"Entorno inicializado con seed: {seed}\n")

# Configurar rutas
universe_path = PROJECT_ROOT / "config" / "universe" / "universe_equities.yaml"
snapshot_dir = PROJECT_ROOT / "data" / "snapshots"

print("="*80)
print("CARGA DEL UNIVERSO DE ACTIVOS")
print("="*80)

# Opción 1: Usar la función de alto nivel (recomendado)
print("\nCargando universo de activos...")
print(f"Archivo: {universe_path}")

try:
    ohlcv_dict, universe_config, tickers_ok = universe.load_and_prepare_universe(
        universe_path=universe_path,
        years_of_data=2,                # 2 años de datos históricos
        max_missing_pct=0.10,           # Máximo 10% de datos faltantes
        save_snapshot_dir=snapshot_dir  # Guardar snapshot para uso futuro
    )
    
    print("\n✓ Universo cargado exitosamente!")
    print(f"\nEstadísticas:")
    print(f"  - Total de activos en configuración: {len(universe_config['tickers'])}")
    print(f"  - Activos con datos válidos: {len(tickers_ok)}")
    print(f"  - Activos eliminados: {len(universe_config['tickers']) - len(tickers_ok)}")
    
    # Mostrar información de los DataFrames OHLCV
    print(f"\nDataFrames OHLCV disponibles:")
    for field, df in ohlcv_dict.items():
        print(f"  - {field:12s}: {df.shape} (filas × columnas)")
    
    # Mostrar algunos activos
    print(f"\nPrimeros 10 activos válidos:")
    for i, ticker in enumerate(tickers_ok[:10], 1):
        # Buscar información del ticker en el universo
        ticker_info = next((t for t in universe_config['tickers'] if t['symbol_yf'] == ticker), None)
        if ticker_info:
            print(f"  {i:2d}. {ticker:10s} - {ticker_info['name'][:40]:40s} ({ticker_info['sector']})")
    
    # Mostrar estadísticas de datos faltantes
    adj_close_df = ohlcv_dict['adj_close']
    missing_stats = adj_close_df.isna().mean().sort_values()
    
    print(f"\nActivos con menos datos faltantes (mejores 5):")
    for ticker in missing_stats.head(5).index:
        pct = missing_stats[ticker] * 100
        print(f"  - {ticker:10s}: {pct:5.2f}% faltante")
    
    # Ejemplo de cálculo simple: retornos diarios
    print(f"\n" + "="*80)
    print("EJEMPLO: CÁLCULO DE RETORNOS DIARIOS")
    print("="*80)
    
    returns = adj_close_df.pct_change()
    
    print(f"\nRetornos diarios calculados:")
    print(f"  - Shape: {returns.shape}")
    print(f"  - Período: {returns.index[0]} a {returns.index[-1]}")
    
    # Estadísticas de retornos
    print(f"\nEstadísticas de retornos (anualizado):")
    mean_return = returns.mean() * 252  # Anualizados
    std_return = returns.std() * (252 ** 0.5)  # Anualizados
    
    print(f"\nActivos con mayor retorno esperado:")
    for ticker in mean_return.sort_values(ascending=False).head(5).index:
        ret = mean_return[ticker] * 100
        vol = std_return[ticker] * 100
        sharpe = ret / vol if vol > 0 else 0
        print(f"  - {ticker:10s}: Retorno={ret:6.2f}%, Vol={vol:6.2f}%, Sharpe={sharpe:5.2f}")
    
    print(f"\n" + "="*80)
    print("✓ EJEMPLO COMPLETADO EXITOSAMENTE")
    print("="*80)
    print(f"\nLos datos están listos para ser usados en análisis posteriores.")
    print(f"Snapshot guardado en: {snapshot_dir}")
    
except FileNotFoundError as e:
    print(f"\n✗ Error: Archivo no encontrado")
    print(f"  {e}")
    print(f"\nVerifica que el archivo de universo existe en:")
    print(f"  {universe_path}")
    sys.exit(1)
    
except ValueError as e:
    print(f"\n✗ Error al descargar datos")
    print(f"  {e}")
    print(f"\nPosibles causas:")
    print(f"  - No hay conexión a internet")
    print(f"  - Yahoo Finance no está disponible")
    print(f"  - Los símbolos en el universo no son válidos")
    print(f"\nIntenta cargar un snapshot guardado previamente.")
    sys.exit(1)
    
except Exception as e:
    print(f"\n✗ Error inesperado: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
