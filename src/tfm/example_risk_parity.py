"""
Ejemplo de uso del módulo de optimización de carteras.

Este script demuestra cómo usar las funciones de Risk Parity y otros métodos
de construcción de carteras disponibles en el módulo portfolio_optimization.

Uso:
    python -m src.tfm.example_risk_parity
"""

import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.tfm.portfolio_optimization import (
    risk_parity_weights,
    inverse_volatility_weights,
    analyze_portfolio_risk
)


def compare_portfolio_methods(returns: pd.DataFrame, show_plots: bool = True):
    """
    Compara diferentes métodos de construcción de carteras.
    
    Args:
        returns: DataFrame con retornos diarios de activos
        show_plots: Si mostrar gráficos
    
    Returns:
        Dict con los pesos de cada método
    """
    print("=" * 70)
    print("COMPARACIÓN DE MÉTODOS DE CONSTRUCCIÓN DE CARTERAS")
    print("=" * 70)
    
    # Calcular matriz de covarianza anualizada
    cov_matrix = returns.cov() * 252
    
    # Método 1: Equal Weight (baseline)
    n_assets = len(returns.columns)
    weights_equal = pd.Series(1.0 / n_assets, index=returns.columns)
    
    # Método 2: Inverse Volatility
    weights_inv_vol = inverse_volatility_weights(returns)
    
    # Método 3: Risk Parity
    weights_rp = risk_parity_weights(cov_matrix)
    
    # Compilar resultados
    results = {
        'Equal_Weight': weights_equal,
        'Inverse_Volatility': weights_inv_vol,
        'Risk_Parity': weights_rp
    }
    
    # Análisis de cada cartera
    print("\n" + "=" * 70)
    print("ANÁLISIS DE RIESGO POR MÉTODO")
    print("=" * 70)
    
    for name, weights in results.items():
        print(f"\n{name}:")
        print("-" * 70)
        analysis = analyze_portfolio_risk(weights, cov_matrix, annualize=False)
        
        # Métricas de concentración
        herfindahl = (weights ** 2).sum()
        effective_n = 1 / herfindahl
        print(f"Concentración (Herfindahl): {herfindahl:.4f}")
        print(f"Número efectivo de activos: {effective_n:.2f}")
    
    # Visualización
    if show_plots:
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        colors = ['steelblue', 'darkorange', 'darkgreen']
        
        for idx, (name, weights) in enumerate(results.items()):
            weights.sort_values(ascending=True).plot(
                kind='barh',
                ax=axes[idx],
                color=colors[idx]
            )
            axes[idx].set_title(f'Pesos - {name}', fontsize=12, fontweight='bold')
            axes[idx].set_xlabel('Peso')
            axes[idx].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('/tmp/portfolio_comparison.png', dpi=150, bbox_inches='tight')
        print("\nGráfico guardado en: /tmp/portfolio_comparison.png")
        plt.close()
    
    return results


def main():
    """Función principal de ejemplo."""
    
    # Generar datos sintéticos de ejemplo
    np.random.seed(42)
    
    # Parámetros
    n_days = 252 * 3  # 3 años de datos
    n_assets = 10
    
    # Generar retornos correlacionados
    mean_returns = np.random.uniform(0.0002, 0.0008, n_assets)
    volatilities = np.random.uniform(0.01, 0.03, n_assets)
    
    # Matriz de correlación aleatoria
    corr = np.random.uniform(0.1, 0.5, (n_assets, n_assets))
    corr = (corr + corr.T) / 2  # Hacerla simétrica
    np.fill_diagonal(corr, 1.0)
    
    # Matriz de covarianza
    cov_daily = np.outer(volatilities, volatilities) * corr
    
    # Generar retornos
    returns = np.random.multivariate_normal(mean_returns, cov_daily, n_days)
    
    # Crear DataFrame
    asset_names = [f'Asset_{i+1:02d}' for i in range(n_assets)]
    returns_df = pd.DataFrame(returns, columns=asset_names)
    
    print("\nDatos generados:")
    print(f"- Activos: {n_assets}")
    print(f"- Días: {n_days}")
    print(f"- Volatilidad media (anual): {returns_df.std().mean() * np.sqrt(252):.2%}")
    
    # Comparar métodos
    results = compare_portfolio_methods(returns_df, show_plots=True)
    
    # Mostrar resumen de pesos
    print("\n" + "=" * 70)
    print("RESUMEN DE PESOS (Top 5 por método)")
    print("=" * 70)
    
    comparison_df = pd.DataFrame(results)
    print(comparison_df.round(4))
    
    print("\n" + "=" * 70)
    print("CONCLUSIONES")
    print("=" * 70)
    print("""
    Risk Parity es especialmente útil cuando:
    - No se tienen estimaciones confiables de retornos esperados
    - Se busca diversificación basada puramente en riesgo
    - Se quiere evitar la inestabilidad numérica de Markowitz
    
    Inverse Volatility es una aproximación más simple que:
    - No requiere optimización (más rápido)
    - Da resultados similares a Risk Parity en muchos casos
    - Es útil como baseline
    
    Equal Weight es el benchmark más simple:
    - Asume que todos los activos son igualmente valiosos
    - Puede ser sorprendentemente efectivo en la práctica
    - Es el punto de partida para comparaciones
    """)


if __name__ == '__main__':
    main()
