# Trading_Inteligente
(Trabajo TFM) Estrategias Adaptativas impulsadas por Machine Learning para Renta Variable, Divisas y Criptoactivos.

## Descripción

Este proyecto implementa estrategias de trading adaptativas utilizando técnicas de Machine Learning para optimización de carteras en múltiples clases de activos.

## Estructura del Proyecto

```
Bot-Trading-Adaptativo/
├── config/              # Archivos de configuración
│   ├── ips.yaml        # Investment Policy Statement
│   └── universe/       # Definición de universos de activos
├── src/                # Código fuente
│   └── tfm/           # Módulos del proyecto
│       ├── bootstrap.py    # Inicialización del entorno
│       └── universe.py     # Gestión de universo de activos
├── Notebooks/          # Notebooks de análisis
├── examples/           # Ejemplos de uso
├── docs/              # Documentación
└── requirements.txt   # Dependencias del proyecto
```

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/KarenFaS/Bot-Trading-Adaptativo.git
cd Bot-Trading-Adaptativo
```

2. Crear un entorno virtual (recomendado):
```bash
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## Módulos Disponibles

### Módulo Universe

El módulo `tfm.universe` proporciona funcionalidades para gestionar el universo de activos financieros:

- Carga de configuración desde archivos YAML
- Descarga de datos OHLCV desde Yahoo Finance
- Validación y filtrado de calidad de datos
- Gestión de snapshots para análisis offline

**Ejemplo de uso:**

```python
from tfm import universe
from pathlib import Path

# Cargar y preparar el universo
ohlcv_dict, universe_config, tickers_ok = universe.load_and_prepare_universe(
    universe_path=Path("config/universe/universe_equities.yaml"),
    years_of_data=2,
    max_missing_pct=0.10
)

# Acceder a los datos
adj_close_df = ohlcv_dict['adj_close']
```

Ver [documentación completa](docs/universe_usage.md) para más detalles.

### Ejecutar ejemplo

```bash
python examples/load_universe_example.py
```

## Características

- ✅ **Gestión de universo de activos**: Configuración flexible de múltiples activos
- ✅ **Descarga automática de datos**: Integración con Yahoo Finance
- ✅ **Validación de calidad**: Filtrado automático de activos con datos insuficientes
- ✅ **Reproducibilidad**: Sistema de snapshots para análisis offline
- 🚧 **Optimización de cartera**: HRP (Hierarchical Risk Parity) [En desarrollo]
- 🚧 **Machine Learning**: Modelos predictivos adaptativos [En desarrollo]
- 🚧 **Backtesting**: Validación walk-forward [En desarrollo]

## Notebook Principal

El análisis completo se encuentra en `Notebooks/TFM-TRADING_ADAPTATIVO.ipynb`, que incluye:

1. Configuración del entorno
2. Perfil del inversor (IPS)
3. Universo de activos y datos
4. Features y scoring con ML
5. Construcción de cartera
6. Validación y métricas
7. Paper trading
8. Selección para intradía

## Contribuir

Este es un proyecto académico (TFM). Para sugerencias o mejoras, por favor abre un issue.

## Licencia

Proyecto académico - Universidad del País Vasco (UPV/EHU)

## Autor

**Karen Fajardo**  
Máster en Finanzas y Dirección Financiera  
Tutor: PhD. Vicente Ruiz
