"""Utility functions for binomial option pricing.

This module implements a Cox-Ross-Rubinstein style binomial tree for pricing
European and American options. The primary entry point is
``binomial_option_price`` which supports call and put payoffs and optional
continuous dividend yield. The implementation favors clarity and numerical
stability over micro-optimizations.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import exp, sqrt
from typing import Callable


@dataclass
class BinomialParameters:
    """Container for binomial tree configuration.

    Attributes:
        spot: Current underlying price.
        strike: Option strike price.
        rate: Continuously compounded risk-free rate.
        time: Time to maturity in years.
        volatility: Annualized volatility of the underlying.
        steps: Number of time steps in the tree.
        dividend_yield: Continuous dividend yield. Defaults to zero.
        option_type: ``"call"`` for a call option or ``"put"`` for a put option.
        exercise: ``"european"`` or ``"american"``.
    """

    spot: float
    strike: float
    rate: float
    time: float
    volatility: float
    steps: int
    dividend_yield: float = 0.0
    option_type: str = "call"
    exercise: str = "european"

    def validate(self) -> None:
        if self.steps <= 0:
            raise ValueError("Number of steps must be positive")
        if self.spot <= 0 or self.strike <= 0:
            raise ValueError("Spot and strike must be positive")
        if self.volatility < 0:
            raise ValueError("Volatility must be non-negative")
        if self.time <= 0:
            raise ValueError("Time to maturity must be positive")
        if self.option_type not in {"call", "put"}:
            raise ValueError("option_type must be 'call' or 'put'")
        if self.exercise not in {"european", "american"}:
            raise ValueError("exercise must be 'european' or 'american'")


def _payoff(option_type: str) -> Callable[[float, float], float]:
    if option_type == "call":
        return lambda price, strike: max(price - strike, 0.0)
    return lambda price, strike: max(strike - price, 0.0)


def binomial_option_price(params: BinomialParameters) -> float:
    """Price an option using the binomial tree method.

    Args:
        params: ``BinomialParameters`` instance with model configuration.

    Returns:
        Present value of the option according to the binomial model.

    Raises:
        ValueError: If invalid parameters are supplied.
    """

    params.validate()

    dt = params.time / params.steps
    up = exp(params.volatility * sqrt(dt))
    down = 1 / up
    growth = exp((params.rate - params.dividend_yield) * dt)
    prob = (growth - down) / (up - down)

    if not 0 <= prob <= 1:
        raise ValueError("Risk-neutral probability outside [0, 1]; adjust inputs or steps")

    disc = exp(-params.rate * dt)
    payoff_fn = _payoff(params.option_type)

    # Terminal payoffs
    prices = [params.spot * (up ** j) * (down ** (params.steps - j)) for j in range(params.steps + 1)]
    values = [payoff_fn(price, params.strike) for price in prices]

    if params.exercise == "european":
        for _ in range(params.steps):
            values = [disc * (prob * values[j + 1] + (1 - prob) * values[j]) for j in range(len(values) - 1)]
        return values[0]

    # American option backward induction with early exercise
    for step in range(params.steps - 1, -1, -1):
        next_values = []
        for j in range(step + 1):
            continuation = disc * (prob * values[j + 1] + (1 - prob) * values[j])
            node_price = params.spot * (up ** j) * (down ** (step - j))
            exercise_val = payoff_fn(node_price, params.strike)
            next_values.append(max(continuation, exercise_val))
        values = next_values

    return values[0]


def example() -> None:
    """Demonstrate the pricing function with a simple scenario."""

    params = BinomialParameters(
        spot=100,
        strike=100,
        rate=0.05,
        time=1,
        volatility=0.2,
        steps=200,
        option_type="call",
        exercise="european",
    )
    price = binomial_option_price(params)
    print(f"European call price (CRR, 200 steps): {price:.4f}")


if __name__ == "__main__":
    example()
