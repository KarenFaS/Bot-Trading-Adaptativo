"""
Portfolio optimization methods.

This module implements various portfolio construction techniques:
- Risk Parity (Equal Risk Contribution)
- Helpers for portfolio analysis

Risk Parity avoids the classic Markowitz problems by:
1. Not requiring expected returns (mu)
2. Not inverting the covariance matrix (more stable)
3. Allocating weights based purely on risk structure
"""

import numpy as np
import pandas as pd
from typing import Union
from scipy.optimize import minimize


def calculate_portfolio_variance(weights: np.ndarray, cov_matrix: np.ndarray) -> float:
    """
    Calculate portfolio variance given weights and covariance matrix.
    
    Args:
        weights: Array of portfolio weights
        cov_matrix: Covariance matrix of assets
    
    Returns:
        Portfolio variance
    """
    return weights @ cov_matrix @ weights


def calculate_risk_contributions(weights: np.ndarray, cov_matrix: np.ndarray) -> np.ndarray:
    """
    Calculate the risk contribution of each asset to total portfolio risk.
    
    Risk contribution of asset i = w_i * (Σw)_i / σ_p
    where (Σw)_i is the i-th element of the covariance matrix times weight vector,
    and σ_p is the portfolio standard deviation.
    
    Args:
        weights: Array of portfolio weights
        cov_matrix: Covariance matrix of assets
    
    Returns:
        Array of risk contributions (sum equals portfolio volatility)
    """
    portfolio_variance = calculate_portfolio_variance(weights, cov_matrix)
    portfolio_volatility = np.sqrt(portfolio_variance)
    
    # Marginal contribution to risk: ∂σ_p/∂w_i = (Σw)_i / σ_p
    marginal_contrib = cov_matrix @ weights / portfolio_volatility
    
    # Risk contribution: w_i * marginal_contrib_i
    risk_contrib = weights * marginal_contrib
    
    return risk_contrib


def risk_parity_objective(weights: np.ndarray, cov_matrix: np.ndarray) -> float:
    """
    Objective function for Risk Parity optimization.
    
    Minimizes the sum of squared differences between each asset's risk contribution
    and the equal risk contribution (1/N of total risk).
    
    Args:
        weights: Array of portfolio weights
        cov_matrix: Covariance matrix of assets
    
    Returns:
        Objective value (lower is better)
    """
    portfolio_volatility = np.sqrt(calculate_portfolio_variance(weights, cov_matrix))
    risk_contrib = calculate_risk_contributions(weights, cov_matrix)
    
    # Target: each asset contributes equally to risk (1/N of total volatility)
    n_assets = len(weights)
    target_risk = portfolio_volatility / n_assets
    
    # Sum of squared deviations from target
    return np.sum((risk_contrib - target_risk) ** 2)


def risk_parity_weights(
    cov_matrix: Union[pd.DataFrame, np.ndarray],
    initial_weights: Union[np.ndarray, None] = None,
    method: str = 'SLSQP',
    max_iter: int = 1000
) -> pd.Series:
    """
    Calculate Risk Parity (Equal Risk Contribution) portfolio weights.
    
    This method allocates weights so that each asset contributes equally to 
    portfolio risk, avoiding the instability issues of Markowitz optimization:
    - No need to invert the covariance matrix
    - No dependence on expected returns
    - More stable and robust
    
    Args:
        cov_matrix: Covariance matrix (can be pandas DataFrame or numpy array)
        initial_weights: Initial guess for weights (default: equal weights)
        method: Optimization method (default: 'SLSQP')
        max_iter: Maximum number of iterations
    
    Returns:
        pandas Series with optimized weights (indexed by asset names if DataFrame input)
    
    Example:
        >>> cov = returns.cov() * 252  # Annualized covariance
        >>> weights_rp = risk_parity_weights(cov)
    """
    # Convert to numpy if needed and extract index
    if isinstance(cov_matrix, pd.DataFrame):
        asset_names = cov_matrix.index.tolist()
        cov_array = cov_matrix.values
    else:
        cov_array = np.array(cov_matrix)
        asset_names = [f"Asset_{i}" for i in range(cov_array.shape[0])]
    
    n_assets = cov_array.shape[0]
    
    # Initial guess: equal weights
    if initial_weights is None:
        initial_weights = np.ones(n_assets) / n_assets
    
    # Constraints: weights sum to 1
    constraints = [
        {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}
    ]
    
    # Bounds: weights between 0 and 1 (long-only)
    bounds = tuple((0.0, 1.0) for _ in range(n_assets))
    
    # Optimize
    result = minimize(
        fun=risk_parity_objective,
        x0=initial_weights,
        args=(cov_array,),
        method=method,
        bounds=bounds,
        constraints=constraints,
        options={'maxiter': max_iter}
    )
    
    if not result.success:
        print(f"Warning: Optimization did not converge. Message: {result.message}")
    
    # Return as pandas Series
    weights = pd.Series(result.x, index=asset_names)
    
    return weights


def inverse_volatility_weights(
    returns: pd.DataFrame,
    window: Union[int, None] = None
) -> pd.Series:
    """
    Calculate Inverse Volatility portfolio weights (simple risk-based approach).
    
    Weight each asset inversely proportional to its volatility:
    w_i = (1/σ_i) / Σ(1/σ_j)
    
    This is a simpler alternative to Risk Parity, useful as a baseline.
    
    Args:
        returns: DataFrame of asset returns
        window: Rolling window for volatility calculation (None = use all data)
    
    Returns:
        pandas Series with weights
    """
    if window is not None:
        volatilities = returns.iloc[-window:].std()
    else:
        volatilities = returns.std()
    
    # Inverse volatility
    inv_vol = 1.0 / volatilities
    
    # Normalize to sum to 1
    weights = inv_vol / inv_vol.sum()
    
    return weights


def analyze_portfolio_risk(
    weights: pd.Series,
    cov_matrix: pd.DataFrame,
    annualize: bool = True
) -> pd.DataFrame:
    """
    Analyze the risk characteristics of a portfolio.
    
    Args:
        weights: Portfolio weights
        cov_matrix: Covariance matrix
        annualize: Whether to annualize the results (assuming daily data)
    
    Returns:
        DataFrame with risk analysis (volatility, risk contributions, etc.)
    """
    weights_array = weights.values
    cov_array = cov_matrix.loc[weights.index, weights.index].values
    
    # Portfolio volatility
    portfolio_var = calculate_portfolio_variance(weights_array, cov_array)
    portfolio_vol = np.sqrt(portfolio_var)
    
    if annualize:
        portfolio_vol = portfolio_vol * np.sqrt(252)
    
    # Risk contributions
    risk_contrib = calculate_risk_contributions(weights_array, cov_array)
    if annualize:
        risk_contrib = risk_contrib * np.sqrt(252)
    
    # Percentage contribution to risk
    risk_contrib_pct = risk_contrib / portfolio_vol
    
    # Create analysis DataFrame
    analysis = pd.DataFrame({
        'weight': weights.values,
        'risk_contribution': risk_contrib,
        'risk_contrib_pct': risk_contrib_pct
    }, index=weights.index)
    
    analysis = analysis.sort_values('risk_contrib_pct', ascending=False)
    
    print(f"\nPortfolio Volatility: {portfolio_vol:.2%}")
    print(f"Risk Contribution Range: {risk_contrib_pct.min():.2%} - {risk_contrib_pct.max():.2%}")
    print(f"Risk Contribution Std: {risk_contrib_pct.std():.2%}")
    
    return analysis
