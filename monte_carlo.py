"""Monte Carlo simulation utilities for option pricing.

This module simulates geometric Brownian motion paths and estimates option
prices by averaging discounted payoffs. Users can supply arbitrary payoff
functions or string expressions evaluated per path to accommodate exotic
structures.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import exp, sqrt
from typing import Callable, Iterable

import numpy as np


@dataclass
class MonteCarloParameters:
    """Configuration for Monte Carlo option pricing.

    Attributes:
        spot: Current underlying price.
        rate: Continuously compounded risk-free rate.
        time: Time to maturity in years.
        volatility: Annualized volatility of the underlying.
        paths: Number of simulated price paths.
        steps: Number of time steps per path. Use 1 for a single terminal draw.
        dividend_yield: Continuous dividend yield. Defaults to zero.
        seed: Optional random seed for reproducibility.
    """

    spot: float
    rate: float
    time: float
    volatility: float
    paths: int = 10000
    steps: int = 1
    dividend_yield: float = 0.0
    seed: int | None = None

    def validate(self) -> None:
        if self.spot <= 0:
            raise ValueError("Spot must be positive")
        if self.volatility < 0:
            raise ValueError("Volatility must be non-negative")
        if self.time <= 0:
            raise ValueError("Time to maturity must be positive")
        if self.paths <= 0:
            raise ValueError("Number of paths must be positive")
        if self.steps <= 0:
            raise ValueError("Number of steps must be positive")


def simulate_paths(params: MonteCarloParameters) -> np.ndarray:
    """Generate price paths under geometric Brownian motion."""

    params.validate()
    rng = np.random.default_rng(params.seed)
    dt = params.time / params.steps
    drift = (params.rate - params.dividend_yield - 0.5 * params.volatility**2) * dt
    diffusion = params.volatility * sqrt(dt)

    # Preallocate and fill paths
    paths = np.empty((params.paths, params.steps + 1), dtype=float)
    paths[:, 0] = params.spot

    shocks = rng.normal(loc=0.0, scale=1.0, size=(params.paths, params.steps))
    for step in range(1, params.steps + 1):
        paths[:, step] = paths[:, step - 1] * np.exp(drift + diffusion * shocks[:, step - 1])

    return paths


def monte_carlo_price(
    params: MonteCarloParameters, payoff: Callable[[np.ndarray], Iterable[float]]
) -> float:
    """Estimate an option price by averaging discounted simulated payoffs."""

    paths = simulate_paths(params)
    payoffs = np.asarray(list(payoff(paths)), dtype=float)
    if payoffs.shape != (params.paths,):
        raise ValueError("Payoff function must return one value per path")

    discount_factor = exp(-params.rate * params.time)
    return discount_factor * float(np.mean(payoffs))


def expression_payoff(expression: str) -> Callable[[np.ndarray], Iterable[float]]:
    """Create a payoff function from a Python expression.

    The expression is evaluated per simulated path with two helper names:
        * ``path``: 1D array of prices along the path.
        * ``np``: NumPy module for vectorized operations.
    Example: ``np.maximum(path[-1] - 100, 0)`` for a European call payoff.
    """

    def _payoff(paths: np.ndarray) -> Iterable[float]:
        # Evaluate the expression independently for each path to allow
        # references to path-level statistics such as maxima or minima.
        for path in paths:
            yield eval(expression, {"np": np}, {"path": path})

    return _payoff


def example() -> None:
    """Demonstrate pricing with a user-specified payoff expression."""

    params = MonteCarloParameters(
        spot=100,
        rate=0.05,
        time=1.0,
        volatility=0.2,
        paths=50_000,
        steps=252,
        seed=42,
    )

    # Asian call: average price over the path minus strike
    payoff_expr = "np.maximum(np.mean(path) - 100, 0)"
    price = monte_carlo_price(params, expression_payoff(payoff_expr))
    print(f"Asian call via Monte Carlo: {price:.4f}")


if __name__ == "__main__":
    user_expression = input(
        "Enter a payoff expression using 'path' (price path) and 'np' (NumPy):\n"
    )
    parameters = MonteCarloParameters(
        spot=float(input("Spot price: ")),
        rate=float(input("Risk-free rate (continuous): ")),
        time=float(input("Time to maturity (years): ")),
        volatility=float(input("Volatility: ")),
        paths=int(input("Number of paths: ")),
        steps=int(input("Steps per path: ")),
        dividend_yield=float(input("Dividend yield (optional, default 0): ") or 0.0),
        seed=None,
    )

    price = monte_carlo_price(parameters, expression_payoff(user_expression))
    print(f"Estimated option price: {price:.4f}")
