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
