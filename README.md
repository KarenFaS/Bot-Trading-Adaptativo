# Trading_Inteligente
(Trabajo TFM) Estrategias Adaptativas impulsadas por Machine Learning para Renta Variable, Divisas y Criptoactivos. 

Trabajo en proceso

## Componentes Implementados

### Portfolio Optimization (Optimización de Carteras)

Implementación de métodos modernos de construcción de carteras:

- **Risk Parity (Equal Risk Contribution)**: Método robusto que asigna pesos basándose en la estructura del riesgo, evitando los problemas clásicos del método de Markowitz (inestabilidad de la inversa de la matriz de covarianza).
  
- **Inverse Volatility**: Método simple y rápido de ponderación basado en volatilidad.

- **Análisis de Riesgo**: Herramientas para analizar contribuciones al riesgo de cada activo.

Ver documentación completa en: [`docs/RISK_PARITY.md`](docs/RISK_PARITY.md)

#### Uso Rápido

```python
from src.tfm.portfolio_optimization import risk_parity_weights, analyze_portfolio_risk

# Calcular pesos Risk Parity
cov_matrix = returns.cov() * 252  # Covarianza anualizada
weights = risk_parity_weights(cov_matrix)

# Analizar cartera
analysis = analyze_portfolio_risk(weights, cov_matrix)
```

#### Ejemplo Completo

```bash
python -m src.tfm.example_risk_parity
```
