# 20251121

Python implementation of a Cox-Ross-Rubinstein binomial tree for pricing
equity options. The `binomial_model.py` module exposes a `binomial_option_price`
function and an accompanying `BinomialParameters` dataclass to describe the
contract and model inputs.

## Quick start

Create a parameter set and price an option:

```python
from binomial_model import BinomialParameters, binomial_option_price

params = BinomialParameters(
    spot=100,          # current underlying price
    strike=100,        # strike price
    rate=0.05,         # risk-free rate (continuous)
    time=1.0,          # time to maturity in years
    volatility=0.2,    # annualized volatility
    steps=200,         # number of steps in the binomial tree
    dividend_yield=0.0,
    option_type="call",   # or "put"
    exercise="american",  # or "european"
)

price = binomial_option_price(params)
print(price)
```

Run the included example from the command line:

```bash
python binomial_model.py
```

## Monte Carlo pricing with custom payoffs

Use `monte_carlo.py` to simulate geometric Brownian motion paths and evaluate
payoffs you provide as Python expressions. The helper `expression_payoff`
accepts any formula involving the path (`path`) and NumPy (`np`). For example,
to price an Asian call whose payoff depends on the average price over the path:

```python
from monte_carlo import MonteCarloParameters, expression_payoff, monte_carlo_price

params = MonteCarloParameters(
    spot=100,
    rate=0.05,
    time=1.0,
    volatility=0.2,
    paths=50_000,
    steps=252,
    seed=42,
)

payoff_expr = "np.maximum(np.mean(path) - 100, 0)"
price = monte_carlo_price(params, expression_payoff(payoff_expr))
print(price)
```

You can also run an interactive prompt to enter your own payoff expression and
parameters:

```bash
python monte_carlo.py
```
