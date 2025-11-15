# Cómo Agregar Risk Parity al Notebook

Este documento explica cómo integrar el método de Risk Parity en el notebook `TFM-TRADING_ADAPTATIVO.ipynb`.

## Ubicación

Agregar después de la **Celda 37** (que implementa la cartera clásica de Markowitz).

## Código para Agregar

### Opción 1: Implementación Completa

Agregar una nueva celda con el siguiente código:

```python
# 3b. Cartera Risk Parity (Equal Risk Contribution)
# Alternativa robusta a Markowitz que evita problemas de inestabilidad numérica

from src.tfm.portfolio_optimization import (
    risk_parity_weights,
    analyze_portfolio_risk,
    inverse_volatility_weights
)

print("=" * 70)
print("MÉTODO ALTERNATIVO: RISK PARITY")
print("=" * 70)
print("""
Risk Parity es un método que:
✓ NO invierte la matriz de covarianza (más estable)
✓ NO requiere estimaciones de retorno esperado (mu)
✓ Asigna pesos para que cada activo contribuya igual al riesgo total
✓ Es más robusto ante errores de estimación
""")

# Calcular pesos Risk Parity
weights_risk_parity = risk_parity_weights(Sigma_ml)

print("\nPesos de la cartera Risk Parity:")
print(weights_risk_parity.sort_values(ascending=False).head(15))

# Análisis de riesgo
print("\n" + "=" * 70)
print("ANÁLISIS DE RIESGO - RISK PARITY")
print("=" * 70)
analysis_rp = analyze_portfolio_risk(weights_risk_parity, Sigma_ml, annualize=False)
print(analysis_rp.head(15))

# Comparación con Markowitz
print("\n" + "=" * 70)
print("COMPARACIÓN: MARKOWITZ vs RISK PARITY")
print("=" * 70)

comparison = pd.DataFrame({
    'Markowitz': weights_classic,
    'Risk_Parity': weights_risk_parity,
    'Diferencia': abs(weights_classic - weights_risk_parity)
}).sort_values('Diferencia', ascending=False)

print("\nTop 10 activos con mayor diferencia de pesos:")
print(comparison.head(10))

# Métricas de concentración
def herfindahl_index(w):
    return (w ** 2).sum()

def effective_n(w):
    return 1 / herfindahl_index(w)

print(f"\nMarkowitz:")
print(f"  Índice Herfindahl: {herfindahl_index(weights_classic):.4f}")
print(f"  Nº efectivo de activos: {effective_n(weights_classic):.2f}")

print(f"\nRisk Parity:")
print(f"  Índice Herfindahl: {herfindahl_index(weights_risk_parity):.4f}")
print(f"  Nº efectivo de activos: {effective_n(weights_risk_parity):.2f}")

# Visualización
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(15, 6))

# Markowitz
weights_classic.sort_values(ascending=True).tail(15).plot(
    kind='barh', ax=axes[0], color='steelblue'
)
axes[0].set_title('Top 15 Pesos - Markowitz', fontsize=12, fontweight='bold')
axes[0].set_xlabel('Peso')
axes[0].grid(True, alpha=0.3)

# Risk Parity
weights_risk_parity.sort_values(ascending=True).tail(15).plot(
    kind='barh', ax=axes[1], color='darkgreen'
)
axes[1].set_title('Top 15 Pesos - Risk Parity', fontsize=12, fontweight='bold')
axes[1].set_xlabel('Peso')
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.show()
```

### Opción 2: Implementación Mínima

Si solo quieres los pesos de Risk Parity sin análisis detallado:

```python
# Risk Parity: alternativa robusta a Markowitz
from src.tfm.portfolio_optimization import risk_parity_weights

weights_risk_parity = risk_parity_weights(Sigma_ml)
print("Pesos Risk Parity:")
print(weights_risk_parity.sort_values(ascending=False))
```

## Cálculo de Retornos de la Cartera

Para calcular los retornos de la cartera Risk Parity (similar a como se hace con Markowitz):

```python
# Retornos diarios de la cartera Risk Parity
port_ret_risk_parity = (returns_ml * weights_risk_parity).sum(axis=1)

# Rentabilidad acumulada
cumulative_ret_rp = (1 + port_ret_risk_parity).cumprod()

# Rentabilidad en los últimos 21 días
last_21_ret_rp = port_ret_risk_parity.iloc[-21:]
real_21d_return_rp = (1 + last_21_ret_rp).prod() - 1

print(f"Rentabilidad REAL de Risk Parity en últimos 21 días: {real_21d_return_rp:.2%}")
```

## Comparación de Rendimientos

```python
# Comparar rendimientos acumulados
plt.figure(figsize=(12, 6))
plt.plot((1 + port_ret_classic).cumprod(), label='Markowitz', linewidth=2)
plt.plot((1 + port_ret_risk_parity).cumprod(), label='Risk Parity', linewidth=2)
plt.title('Rentabilidad Acumulada: Markowitz vs Risk Parity')
plt.xlabel('Fecha')
plt.ylabel('Valor de la cartera (base 1)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()
```

## Ventajas de Risk Parity

1. **Más estable**: No invierte matrices, evita problemas numéricos
2. **No requiere mu**: Solo usa la estructura de riesgo (covarianza)
3. **Mejor diversificación**: Mayor número efectivo de activos
4. **Más robusto**: Menos sensible a errores de estimación

## Cuándo Usar Cada Método

| Situación | Método |
|-----------|--------|
| Estimaciones de retorno inciertas | **Risk Parity** |
| Alta confianza en predicciones ML | Markowitz |
| Máxima diversificación | **Risk Parity** |
| Maximizar Sharpe (con mu confiable) | Markowitz |

## Referencias

- Documentación completa: `docs/RISK_PARITY.md`
- Ejemplo ejecutable: `python -m src.tfm.example_risk_parity`
- Tests: `/tmp/test_risk_parity.py` y `/tmp/integration_test_notebook.py`
