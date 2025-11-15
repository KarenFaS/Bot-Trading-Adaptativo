"""
Ejemplo de uso del módulo ml_data para preparar datos históricos con targets conocidos.

Este script demuestra cómo:
1. Cargar datos de retornos de activos
2. Preparar features y targets para machine learning
3. Entrenar un modelo supervisado (RandomForest)
4. Evaluar el rendimiento del modelo
"""

import sys
from pathlib import Path

# Añadir el directorio src al path para importar módulos locales
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

import pandas as pd
import numpy as np
from tfm import ml_data
from sklearn.ensemble import RandomForestRegressor
import matplotlib.pyplot as plt


def create_sample_returns_data(n_dates=400, n_assets=10):
    """
    Crea datos de retornos sintéticos para el ejemplo.
    
    En un caso real, estos datos vendrían del módulo universe.
    """
    np.random.seed(42)
    
    # Crear índice de fechas
    dates = pd.date_range(start='2023-01-01', periods=n_dates, freq='D')
    
    # Crear tickers sintéticos
    tickers = [f'ASSET_{i:02d}' for i in range(n_assets)]
    
    # Generar retornos aleatorios con algo de persistencia
    returns_dict = {}
    for ticker in tickers:
        # Retornos con media cercana a 0 y desviación estándar realista
        base_returns = np.random.normal(0.001, 0.02, n_dates)
        # Añadir algo de autocorrelación
        returns = []
        prev_return = 0
        for r in base_returns:
            new_return = 0.7 * r + 0.3 * prev_return
            returns.append(new_return)
            prev_return = new_return
        returns_dict[ticker] = returns
    
    # Crear DataFrame
    returns_df = pd.DataFrame(returns_dict, index=dates)
    
    return returns_df


def main():
    """Función principal del ejemplo."""
    
    print("=" * 80)
    print("Ejemplo: Preparación de datos históricos con targets conocidos para ML")
    print("=" * 80)
    print()
    
    # 1. Crear o cargar datos de retornos
    print("1. Creando datos de retornos sintéticos...")
    returns_df = create_sample_returns_data(n_dates=400, n_assets=10)
    print(f"   - Shape de retornos: {returns_df.shape}")
    print(f"   - Período: {returns_df.index[0].date()} a {returns_df.index[-1].date()}")
    print()
    
    # 2. Preparar datos usando el pipeline completo
    print("2. Preparando datos para ML usando prepare_ml_pipeline...")
    ml_pipeline_data = ml_data.prepare_ml_pipeline(
        returns_df=returns_df,
        test_size=25,
        windows={'1m': 21, '3m': 63, '6m': 126},
        target_window=21,
        scale=True
    )
    
    print(f"   - Training samples: {len(ml_pipeline_data['X_train'])}")
    print(f"   - Test samples: {len(ml_pipeline_data['X_test'])}")
    print(f"   - Features: {ml_pipeline_data['feature_cols']}")
    print()
    
    # 3. Entrenar modelo de ML
    print("3. Entrenando modelo RandomForest...")
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=5,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(ml_pipeline_data['X_train'], ml_pipeline_data['y_train'])
    print("   - Modelo entrenado exitosamente")
    print()
    
    # 4. Hacer predicciones
    print("4. Generando predicciones en conjunto de test...")
    y_pred = model.predict(ml_pipeline_data['X_test'])
    
    # Integrar predicciones al panel de test
    test_panel = ml_pipeline_data['test_panel'].copy()
    test_panel['pred'] = y_pred
    test_panel['signal'] = (test_panel['pred'] > 0).astype(int)
    test_panel['strategy_ret'] = test_panel['signal'] * test_panel['target_21d']
    
    print(f"   - Predicciones generadas: {len(y_pred)}")
    print()
    
    # 5. Calcular métricas de rendimiento
    print("5. Calculando métricas de rendimiento...")
    
    # Métricas por fecha (agregando activos)
    daily_results = test_panel.groupby("Date")[['target_21d', 'strategy_ret']].mean()
    
    # Retornos acumulados
    cumsum_bh = daily_results['target_21d'].cumsum()
    cumsum_strategy = daily_results['strategy_ret'].cumsum()
    
    print(f"   - Retorno B&H (media activos): {cumsum_bh.iloc[-1]:.2%}")
    print(f"   - Retorno estrategia ML: {cumsum_strategy.iloc[-1]:.2%}")
    print()
    
    # 6. Visualización
    print("6. Generando visualización...")
    plt.figure(figsize=(12, 6))
    plt.plot(daily_results.index, cumsum_bh, label='Buy & Hold (media activos)', linewidth=2)
    plt.plot(daily_results.index, cumsum_strategy, label='Estrategia ML (media activos)', linewidth=2)
    plt.title('Comparación ML vs Buy & Hold (período de test)')
    plt.xlabel('Fecha')
    plt.ylabel('Retorno acumulado')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    
    # Guardar figura
    output_path = project_root / "examples" / "ml_performance_comparison.png"
    plt.savefig(output_path, dpi=150)
    print(f"   - Gráfico guardado en: {output_path}")
    print()
    
    # 7. Mostrar feature importance
    print("7. Feature importance del modelo:")
    feature_importance = pd.DataFrame({
        'feature': ml_pipeline_data['feature_cols'],
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    for idx, row in feature_importance.iterrows():
        print(f"   - {row['feature']}: {row['importance']:.4f}")
    print()
    
    print("=" * 80)
    print("Ejemplo completado exitosamente!")
    print("=" * 80)
    print()
    print("Próximos pasos:")
    print("  - Usar este módulo en el notebook TFM-TRADING_ADAPTATIVO.ipynb")
    print("  - Experimentar con diferentes ventanas de features y targets")
    print("  - Probar otros modelos de ML (XGBoost, LightGBM, etc.)")
    print("  - Implementar validación cruzada walk-forward")


if __name__ == "__main__":
    main()
