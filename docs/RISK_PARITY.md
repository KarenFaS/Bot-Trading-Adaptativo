# Risk Parity Portfolio Construction

## Descripción

Este módulo implementa métodos de construcción de carteras basados en riesgo, específicamente **Risk Parity (Equal Risk Contribution)**, que evitan los problemas clásicos del método de Markowitz.

## Problema con Markowitz

El método clásico de Markowitz para optimización de carteras tiene varios problemas:

1. **Inestabilidad numérica**: Requiere invertir la matriz de covarianza, lo que puede ser numéricamente inestable cuando:
   - Los activos están altamente correlacionados
   - La matriz está cerca de ser singular
   - Hay ruido en las estimaciones de covarianza

2. **Sensibilidad a estimaciones de retorno**: Pequeños cambios en las estimaciones de retorno esperado (μ) pueden causar grandes cambios en los pesos óptimos.

3. **Concentración excesiva**: Tiende a asignar mucho peso a pocos activos, reduciendo la diversificación.

## Solución: Risk Parity

Risk Parity es un método alternativo que:

✓ **No requiere inversión de matriz**: Usa optimización numérica estable
✓ **No depende de retornos esperados**: Solo usa la estructura de riesgo (covarianza)
✓ **Mejor diversificación**: Cada activo contribuye igual al riesgo total
✓ **Más robusto**: Menos sensible a errores de estimación

### Concepto Matemático

En Risk Parity, buscamos pesos `w` tales que:

```
RC_i = w_i × (Σw)_i / σ_p = constante para todo i
```

Donde:
- `RC_i`: Contribución al riesgo del activo i
- `w_i`: Peso del activo i
- `Σ`: Matriz de covarianza
- `σ_p`: Volatilidad del portafolio

### Algoritmo

1. Iniciar con pesos iguales: `w_0 = [1/N, 1/N, ..., 1/N]`
2. Minimizar la función objetivo:
   ```
   min Σ(RC_i - σ_p/N)²
   ```
3. Sujeto a:
   - `Σw_i = 1` (pesos suman 1)
   - `w_i ≥ 0` (no posiciones cortas)

## Uso

### Uso Básico

```python
from src.tfm.portfolio_optimization import risk_parity_weights

# Calcular matriz de covarianza (anualizada)
cov_matrix = returns.cov() * 252

# Obtener pesos Risk Parity
weights = risk_parity_weights(cov_matrix)

print(weights)
```

### Análisis de Riesgo

```python
from src.tfm.portfolio_optimization import analyze_portfolio_risk

# Analizar la cartera
analysis = analyze_portfolio_risk(weights, cov_matrix)

# Muestra:
# - Volatilidad del portafolio
# - Contribución al riesgo de cada activo
# - Porcentaje de contribución al riesgo
```

### Comparación con Otros Métodos

```python
from src.tfm.portfolio_optimization import (
    risk_parity_weights,
    inverse_volatility_weights
)

# Método 1: Risk Parity (óptimo)
weights_rp = risk_parity_weights(cov_matrix)

# Método 2: Inverse Volatility (aproximación rápida)
weights_iv = inverse_volatility_weights(returns)

# Método 3: Equal Weight (baseline)
weights_eq = pd.Series(1/N, index=returns.columns)
```

## Integración con el Notebook

Para usar en el notebook `TFM-TRADING_ADAPTATIVO.ipynb`, agregar después de la celda 37 (Markowitz):

```python
# 3b. Cartera Risk Parity (alternativa robusta a Markowitz)

from src.tfm.portfolio_optimization import (
    risk_parity_weights,
    analyze_portfolio_risk
)

# Calcular pesos Risk Parity
weights_risk_parity = risk_parity_weights(Sigma_ml)

print("Pesos de la cartera Risk Parity:")
print(weights_risk_parity.sort_values(ascending=False))

# Analizar riesgo
analysis_rp = analyze_portfolio_risk(weights_risk_parity, Sigma_ml)
print(analysis_rp)

# Comparar con Markowitz
comparison = pd.DataFrame({
    'Markowitz': weights_classic,
    'Risk_Parity': weights_risk_parity
})
print(comparison)
```

## Ventajas y Desventajas

### Ventajas de Risk Parity

1. **Estabilidad numérica**: No invierte matrices, más robusto
2. **No requiere μ**: Evita errores en estimación de retornos
3. **Mejor diversificación**: Distribución más equitativa del riesgo
4. **Interpretabilidad**: Fácil de entender y comunicar

### Desventajas de Risk Parity

1. **Ignora retornos esperados**: No maximiza retorno esperado
2. **Puede ser conservador**: Prefiere activos de bajo riesgo
3. **Requiere optimización**: Más lento que métodos analíticos

### Cuándo Usar Cada Método

| Situación | Método Recomendado |
|-----------|-------------------|
| Estimaciones de μ inciertas | **Risk Parity** |
| Alta confianza en predicciones ML | Markowitz |
| Necesidad de velocidad | Inverse Volatility |
| Benchmark simple | Equal Weight |
| Máxima diversificación | **Risk Parity** |

## Referencias Teóricas

1. **Maillard, S., Roncalli, T., & Teiletche, J. (2010)**. "On the properties of equally-weighted risk contribution portfolios." Journal of Portfolio Management, 36(4), 60-70.

2. **Qian, E. (2005)**. "Risk parity portfolios: Efficient portfolios through true diversification." PanAgora Asset Management.

3. **Roncalli, T. (2013)**. "Introduction to Risk Parity and Budgeting." Chapman & Hall/CRC Financial Mathematics Series.

## Ejemplo Completo

Ver archivo: `src/tfm/example_risk_parity.py`

```bash
python -m src.tfm.example_risk_parity
```

Este script genera datos sintéticos y compara los tres métodos:
- Equal Weight
- Inverse Volatility  
- Risk Parity

Muestra análisis de riesgo y gráficos de comparación.

## Tests

Para verificar la implementación:

```bash
python /tmp/test_risk_parity.py
```

El test verifica que:
- Los pesos suman 1
- Las contribuciones al riesgo son aproximadamente iguales
- La optimización converge correctamente
- Risk Parity tiene menor dispersión en contribuciones vs Equal Weight
